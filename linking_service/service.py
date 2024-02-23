import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from string import Template

from utils.Configuration_utils import read_config_file

from DTOs.linking_DTOs import Linked_Data_DTO,  Question_DTO

from utils.Request_utils import query_api, query_graphDB
from utils.OpenAI_utils import query_open_ai

from pathlib import Path
import json

from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from Levenshtein import distance

linking_data_path = 'linking_service/Data/Linking_Data/linked_entities/entities_index'
config_file_path = 'linking_service/Config/Config.ini'
app_config_file_path = 'App_config.ini'

# check if required config files exist
if not Path(config_file_path).is_file() or not Path(app_config_file_path).is_file:
    print('Config file was not found for the linking service.')
    exit()

# Reading the config file

config = read_config_file(config_file_path)

# saving config vars
falcon_api_headers = dict(config.items('FALCON-API-HEADERS'))
falcon_api = dict(config.items('FALCON-API'))
falcon_api_params = dict(config.items('FALCON-API-PARAMS'))

open_tapioca_api_headers = dict(config.items('OPEN-TAPIOCA-HEADERS'))
open_tapioca_api = dict(config.items('OPEN-TAPIOCA-API'))

kg_prefix = config['KG_DATA']['prefix']

main_entity_prompt_template= config['OPENAI']['main_entity_prompt_template'].replace(r'\n', '\n')
ner_prompt_template = config['OPENAI']['ner_prompt_template'].replace(r'\n', '\n')
selection_prompt_template = config['OPENAI']['selection_prompt_template'].replace(r'\n', '\n')

wikidata_search_engine_url = config['WIKIDATA_SEARCH_ENGINE']['url']
wikidata_search_engine_params = dict(config.items('WIKIDATA_SEARCH_ENGINE_PARAMS'))

graph_elements_query = config['GRAPHDB_QUERIES']['graph_elements_query']
description_property = config['GRAPHDB_QUERIES']['description_property']
class_property = config['GRAPHDB_QUERIES']['class_property']
prefix = config['GRAPHDB_QUERIES']['prefix']
type_prefix = config['GRAPHDB_QUERIES']['type_prefix']

# Reding the app configurations to get the service configuration
app_config = read_config_file(app_config_file_path)
linking_service = dict(app_config.items('LINKING_SERVICE'))

# Check if the vector store used for entity linking with GRAPHDB exists

vector_store = None

# Let's initialize our HuggingFace embeddings model
model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

if not Path(linking_data_path).exists():
    # if the data does not exists, we will create a vector store querying the graph
    # Let's query the graph
    entities_query_template = Template(graph_elements_query)
    raw_data = query_graphDB(entities_query_template.substitute({
        'description_property' : description_property,
        'class_property' : class_property,
        'prefix' : prefix
    }))

    # Now we will set a format to store each entity information:
    #       URI: Entity URI
    #       label: Entity label
    #       description: entity description
    #       type: entity class or type
    entity_data = []

    for entity in raw_data.get('json').get('results').get('bindings'):
        entity_info = f"""
        URI: {entity.get('item').get('value')}
        label: {entity.get('itemLabel').get('value')}
        description: {entity.get('description').get('value')}
        type : {entity.get('type').get('value').replace(type_prefix,'')} 
        """
        entity_data.append(entity_info)

    # Let's start by creating chunks to store we will use as separator: \n~\n
    text_splitter = CharacterTextSplitter(chunk_size=1,chunk_overlap=0, separator="\n~\n")
    chunks = text_splitter.create_documents(texts=['\n~\n'.join(entity_data)], metadatas=[{'source':'GraphDB'}])

    # Let's create a Faiss Vector Store using these chunks
    vector_store = FAISS.from_documents(
        documents=chunks, # nuestros chunks
        embedding=embeddings.embed_query, # Modulo de embeddings para la transformación de chunk a embedding
    )

    print('Entities index created')
    # Now We will save the vector store
    vector_store.save_local(linking_data_path)

else:
    # If index exists load it
    vector_store = FAISS.load_local(linking_data_path, embeddings.embed_query)
    print('Entities index loaded')

# Initialize retrievers
# Faiss retriever
faiss_retriever = vector_store.as_retriever(search_kwargs={"k": 1})

app = FastAPI()

@app.post(linking_service.get('link_graph_db'))
def link_with_embeddings_to_graphdb(question : Question_DTO):
    # We will use the vector store to retrieve data related to the question
    #data = vector_store.similarity_search('What is the Death Star?')
    data = faiss_retriever.invoke(question.text)[0].page_content.split('\n')
    uri = data[0].replace('URI:', '').strip()
    label = data[1].replace('label:', '').strip()
    return Linked_Data_DTO(entities = [{'UID':uri, 'label':label}])

@app.post(linking_service.get('link_main_endpoint'))
def link_data_main(question : Question_DTO):
    # this endpoint performs the best selected linking method (gpt v1) and returns only the main entity of the question, we perform this in the linking
    # prompt in order to reduce the number of required prompts in the pipeline, the main_entity_prompt_template contains the chosen method prompt as one of
    # the instructions of the prompt, then it will only keep the main entity of the question
    global main_entity_prompt_template
    
    # We will call the chosen method (gpt v1) and run it with the main template
    return link_with_embeddings_to_graphdb(question=question)
    #return link_data_with_OpenAI(question=question, prompt_template=main_entity_prompt_template)

@app.post(linking_service.get('link_endpoint_gpt_v1'))
def link_data_with_OpenAI(question : Question_DTO, prompt_template : str = ner_prompt_template):
    try:
        # extract the entity candidates label using OpenAI GPT
        labels = [label.strip() for label in query_open_ai(prompt_template, {'question': question.text}).split(',')]
        print('GPT found named entities: ', labels)

        result = Linked_Data_DTO(entities = [])
        
        # Match each label to a UID using the wikidata entities search service, if result is none, discard the label
        for label in labels:
            search_result = search_entity_with_wikidata_service(label)
            if search_result is not None:
                result.entities.append(search_result)
        
        return result
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server while working with GPT v1 method. Error:' + str(e))

@app.post(linking_service.get('link_endpoint_gpt_v2'))
def link_data_with_OpenAI_v2(question : Question_DTO, prompt_template : str = ner_prompt_template):
    try:
        # extract the entity candidates label using OpenAI GPT
        labels = [label.strip() for label in query_open_ai(prompt_template, {'question': question.text}).split(',')]
        print('GPT found named entities: ', labels)

        result = Linked_Data_DTO(entities = [])
        
        # Match each label to a UID using the wikidata entities search service and use OpenAI to chose the best candidate, if result is none, discard the label
        for label in labels:
            search_result = search_entity_with_wikidata_service_and_OPENAI(label=label, question=question.text)
            if search_result is not None:
                result.entities.append(search_result)
        
        return result
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server while working with GPT v2 method. Error:' + str(e))
    
@app.post(linking_service.get('link_endpoint_opentapioca'))
def get_open_tapioca_response(question:Question_DTO):
    try:
        res = query_api('post', open_tapioca_api.get('endpoint'), payload={}, headers=open_tapioca_api_headers, params={
            'query' : question.text,
            'lc' : 'en'
        })
        
        # Case of receiving an error response
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='OpenTapioca API error. Code ' + res.get('code')  + " : " + res.get('text'))
        
        json = res.get('json')

        # Transform the answer to the desired format

        entities = []

        for annotation in json.get('annotations'):
            if annotation.get('best_qid'):
                entities.append({ 'UID': annotation['best_qid'], 'label': annotation.get('best_tag_label') })

        return  Linked_Data_DTO(entities = entities)

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server while working with Open Tapioca API. Error:' + str(e))

@app.post(linking_service.get('link_endpoint_falcon'))
def get_falcon_response(question: Question_DTO):
    try:
        # Making a query to falcon API
        res = query_api('post', falcon_api.get('endpoint'), payload=question.__dict__, headers=falcon_api_headers, params=falcon_api_params)

        # Case of receiving an error response
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Falcon API error. Code ' + res.get('code')  + " : " + res.get('text'))
        
        # Transform the answer to the desired format
        json = res.get('json')
        
        for entity in json.get('entities_wikidata'):
            entity['UID'] = entity.pop('URI').replace(kg_prefix,'')
            entity['label'] = entity.pop('surface form')
        
        return Linked_Data_DTO(entities = json.get('entities_wikidata'))

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server while working with FALCON 2.0 API. Error:' + str(e))

def search_entity_with_wikidata_service(label:str):
    def sort_by_levenshtein(data, label):
        data.sort(key=lambda x: distance(x.get('display').get('label').get('value') , label))

    try:
        # ask wikidata search engine to get the information for the given label
        wikidata_search_engine_params['search'] = label
        res = query_api('get', wikidata_search_engine_url, payload={}, headers={}, params=wikidata_search_engine_params)
        
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Unexpected error using wikidata search entities service. Error: ' + res.get('text'))
        
        # if no results were returned of the success flag is set to 0 return None
        if len(res.get('json').get('search')) == 0 or res.get('json').get('success') == 0:
            return None
        
        sort_by_levenshtein(res.get('json').get('search'), label)
        return { 'UID': res.get('json').get('search')[0].get('id'), 'label': label }
    
    except HTTPException as e:
        raise e

    except Exception as e:
        print('Error while querying wikidata search entities service: ', str(e))
        raise HTTPException(status_code=500, detail='Unexpected error using wikidata search entities service. Error: ' + str(e))

def search_entity_with_wikidata_service_and_OPENAI(label:str, question:str):
    global selection_prompt_template
    try:
        # ask wikidata search engine to get the information for the given label
        wikidata_search_engine_params['search'] = label
        res = query_api('get', wikidata_search_engine_url, payload={}, headers={}, params=wikidata_search_engine_params)
        
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Unexpected error using wikidata search entities service. Error: ' + res.get('text'))

        # we will remove elements with no label or description as they are required for this approach
        results = list(filter(lambda x:  x.get('label') is not None and x.get('description') is not None, res.get('json').get('search')))
        
        # if no results were returned of the success flag is set to 0 return None
        if len(results) == 0 or res.get('json').get('success') == 0:
            print('No match found for: ', label)
            return None

        candidates = ['"UID":"' + x.get('id') + '", "label":"' + x.get('label') + '", "description":"' + x.get('description') + '"' for x in results]

        res = query_open_ai(selection_prompt_template, {'question': question, 'candidates': '\n'.join(candidates)})

        # load the received best candidate as json
        best_candidate = json.loads(res)

        return best_candidate
    
    except HTTPException as e:
        raise e

    except Exception as e:
        print('Error while querying wikidata search entities service: ', str(e))
        raise HTTPException(status_code=500, detail='Unexpected error using wikidata search entities service. Error: ' + str(e))