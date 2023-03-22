import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from DTOs.linking_DTOs import Linked_data_DTO,  Question_DTO

from utils.Request_utils import query_api

import spacy

# Reading the config file
config_file_path = 'linking_service/Config/Config.ini'
config = read_config_file(config_file_path)

# saving config vars
falcon_api_headers = dict(config.items('FALCON-API-HEADERS'))
falcon_api = dict(config.items('FALCON-API'))
falcon_api_params = dict(config.items('FALCON-API-PARAMS'))

kg_prefix = config['KG_DATA']['prefix']

# SpaCy Open tapioca entity linker initialization
spaCy_EL = spacy.blank('en')
spaCy_EL.add_pipe('opentapioca')

app = FastAPI()

@app.post('/link/')
def link_data(question : Question_DTO):
    try:
        response = {}
        
        # Query the external falcon API
        falcon_response = get_falcon_response(question.__dict__)

        print('1')

        # Use spacy open tapioca to get the entities
        doc =  spaCy_EL(question.text)

        print('2')


        # Iterate in the found entities to get the expecte information
        doc_ents = []

        for span in doc.ents:
            doc_ents.append({
                'source text' : span.text,
                'UID' : span.kb_id_
            })
            #print((span.text, span.kb_id_, span.label_, span._.description, span._.score))

        print('3')
        
        # If SpaCy Open Tapioca did not succed in linking entities, we will use falcon entities
        if len(doc_ents) == 0:
            doc_ents = falcon_response.get('entities')

        response['entities'] = doc_ents
        response['relations'] = falcon_response.get('relations')

        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail='Unexpected error on server:' + str(e))
    
def get_falcon_response(question: dict):
    try:
        # Making a query to falcon API
        res = query_api('post', falcon_api.get('endpoint'), json_payload=question, headers=falcon_api_headers, params=falcon_api_params)

        # Case of receiving an error response
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Falcon API error. Code ' + res.get('code')  + " : " + res.get('text'))
        
        # Transform the answer to the desired format
        json = res.get('json')
        
        for entity in json.get('entities_wikidata'):
            entity['UID'] = entity.pop('URI').replace(kg_prefix,'')
            entity['source text'] = entity.pop('surface form')

        for relation in json.get('relations_wikidata'):
           relation['source text'] = relation.pop('surface form')
           relation['UID'] = relation.pop('URI').replace(kg_prefix,'')
        
        return {
            'entities' : json.get('entities_wikidata'),
            'relations' : json.get('relations_wikidata')
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server while working with FALCON 2.0 API. Error:' + str(e))
