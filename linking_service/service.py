import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from DTOs.linking_DTOs import Linked_data_DTO,  Question_DTO

from utils.Request_utils import query_api

# Reading the config file
config_file_path = 'linking_service/Config/Config.ini'
config = read_config_file(config_file_path)

# saving config vars
falcon_api_headers = dict(config.items('FALCON-API-HEADERS'))
falcon_api = dict(config.items('FALCON-API'))
falcon_api_params = dict(config.items('FALCON-API-PARAMS'))

open_tapioca_api_headers = dict(config.items('OPEN-TAPIOCA-HEADERS'))
open_tapioca_api = dict(config.items('OPEN-TAPIOCA-API'))

kg_prefix = config['KG_DATA']['prefix']

# Reding the app configurations to get the service configuration
app_config_file_path = 'App_config.ini'
app_config = read_config_file(app_config_file_path)
linking_service = dict(app_config.items('LINKING_SERVICE'))

app = FastAPI()

@app.post(linking_service.get('link_endpoint'))
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
    
def get_open_tapioca_response(question:dict):
    try:
        res = query_api('post', open_tapioca_api.get('endpoint'), json_payload={}, headers=open_tapioca_api_headers, params={
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
        res = query_api('post', falcon_api.get('endpoint'), json_payload=question, headers=falcon_api_headers, params=falcon_api_params)

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
