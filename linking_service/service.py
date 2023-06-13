import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from DTOs.linking_DTOs import Linked_data_DTO,  Question_DTO

from utils.Request_utils import query_api

from pathlib import Path

from dotenv import load_dotenv

from string import Template

import openai

config_file_path = 'linking_service/Config/Config.ini'
open_ai_key_file_path = '.env'

# check if required config files exist
if not Path(config_file_path).is_file():
    print('Config file was not found for the linking service.')
    exit()

if not Path(open_ai_key_file_path).is_file():
    print('.env file with OPENAI key was not found for the linking service.')
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

prompt_template = config['OPENAI']['prompt_template']

wikidata_search_engine_url = config['WIKIDATA_SEARCH_ENGINE']['url']
wikidata_search_engine_params = dict(config.items('WIKIDATA_SEARCH_ENGINE_PARAMS'))

# Read and save OPENAI key

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Reding the app configurations to get the service configuration
app_config_file_path = 'App_config.ini'
app_config = read_config_file(app_config_file_path)
linking_service = dict(app_config.items('LINKING_SERVICE'))

app = FastAPI()

@app.post(linking_service.get('link_endpoint'))
def link_data_with_OpenAI(question : Question_DTO):
    # extract the entity candidates label using OpenAI GPT
    labels = query_open_ai(question.text)
    result = {'entities': [], 'relations': []}
    
    # Match each label to a UID using the wikidata entities search service, if result is none, discard the label
    for label in labels:
        search_result = search_entity_with_wikidata_service(label)
        if search_result is not None:
            result['entities'].append(search_result)
    
    return result

@app.post('/link/backup/')
def link_data(question : Question_DTO):
    try:
        response = {}
        
        # Query the external falcon API
        falcon_response = get_falcon_response(question.__dict__)

        # Query the external OpenTapioca API
        entities = get_open_tapioca_response(question.__dict__)
        
        #if there are no opentapioca entities,  we will work with falcon ones
        if len(entities) == 0:
            entities = falcon_response.get('entities')

        response['entities'] = entities
        response['relations'] = falcon_response.get('relations')

        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail='Unexpected error linkin data with the question: ' + question.text + ' .Error: ' + str(e))

def search_entity_with_wikidata_service(label:str):
    try:
        # ask wikidata search engine to get the information for the given label
        wikidata_search_engine_params['search'] = label
        res = query_api('get', wikidata_search_engine_url, payload={}, headers={}, params=wikidata_search_engine_params)
        
        if res.get('code') != 200:
            raise HTTPException(status_code=500, detail='Unexpected error using wikidata search entities service. Error: ' + str(e))
        
        # if no results were returned of the success flag is set to 0 return None
        if len(res.get('json').get('search')) == 0 or res.get('json').get('success') == 0:
            return None

        return { 'UID': res.get('json').get('search')[0].get('id'), 'label': label }
    
    except HTTPException as e:
        raise e

    except Exception as e:
        print('Error while querying wikidata search entities service: ', str(e))
        raise HTTPException(status_code=500, detail='Unexpected error using wikidata search entities service. Error: ' + str(e))


def query_open_ai(question: str):
    global prompt_template
    try:
        prompt = Template(prompt_template).substitute({'question':question})
        gpt3_model = 'text-davinci-003'
        response = openai.Completion.create(
            engine = gpt3_model,
            prompt = prompt,
            max_tokens = 2048,
            n = 1,
            stop = None,
            temperature = 0
        )
        answer = response.get('choices')[0].get('text')
        print('GPT found named entities: ', answer)
        return answer.split(',')
    
    except Exception as e:
        print('Error while querying openai: ', str(e))
        raise HTTPException(status_code=502, detail='OpenAI API error: ' + str(e))

def get_open_tapioca_response(question:dict):
    try:
        res = query_api('post', open_tapioca_api.get('endpoint'), payload={}, headers=open_tapioca_api_headers, params={
            'query' : question.get('text'),
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

        return  entities

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server while working with Open Tapioca API. Error:' + str(e))

    
def get_falcon_response(question: dict):
    try:
        # Making a query to falcon API
        res = query_api('post', falcon_api.get('endpoint'), payload=question, headers=falcon_api_headers, params=falcon_api_params)

        # Case of receiving an error response
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Falcon API error. Code ' + res.get('code')  + " : " + res.get('text'))
        
        # Transform the answer to the desired format
        json = res.get('json')
        
        for entity in json.get('entities_wikidata'):
            entity['UID'] = entity.pop('URI').replace(kg_prefix,'')
            entity['label'] = entity.pop('surface form')

        for relation in json.get('relations_wikidata'):
           relation['UID'] = relation.pop('URI').replace(kg_prefix,'')
           relation['label'] = relation.pop('surface form')
        
        return {
            'entities' : json.get('entities_wikidata'),
            'relations' : json.get('relations_wikidata')
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server while working with FALCON 2.0 API. Error:' + str(e))
