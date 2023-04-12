import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json
from utils.Request_utils import query_api

from DTOs.templates_DTOs import QALD_json_DTO
from DTOs.linking_DTOs import Question_DTO

# Reading the config file
config_file_path = 'templates_service/Config/Config.ini'
config = read_config_file(config_file_path)

# saving config vars
number_of_attempts = config['REQUESTS']['number_of_attempts']
training_data_path = config['DATA']['training_data_path']
templates_data_path = config['DATA']['templates_data_path']
class_parents_search_index_data_path = config['DATA']['class_parents_search_index_data_path']
properties_search_index_data_path = config['DATA']['properties_search_index_data_path']
max_templates_per_question = int(config['DATA']['max_templates_per_question'])
banned_classes = config.get('BANNED', 'classes').split()

# Reding the app configurations to communicate with other APIs
app_config_file_path = 'App_config.ini'
app_config = read_config_file(app_config_file_path)

translation_service = dict(app_config.items('TRANSLATION_SERVICE'))
entity_linking_service = dict(app_config.items('LINKING_SERVICE'))
graph_query_service = dict(app_config.items('GRAPH_QUERY_SERVICE'))

app = FastAPI()

@app.post('/test/')
def test():
    return translate('Quien es el presidente de Bolivia?', 'es')

# Functions to query other services
def translate(question:str, lang:str):
    # to translate we will query the translation service
    try:
        global number_of_attempts
        global translation_service
        
        payload = { 'text' : question, 'mode' : lang + '-en' }

        url = get_service_url(translation_service, 'translate_endpoint')

        res = query_api('post', url, {}, {}, payload, int(number_of_attempts))
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Translation service returned an error. Code: ' + str(res.get('code')) + ' . Error: ' + res.get('text'))

        return res.get('json')

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying translation service: ' + str(e))

def get_service_url(service:dict, enpoint:str):
    try:    
        url = service.get('ip') + ':' + service.get('port') + service.get(enpoint)
        if 'http://' not in url:
            url = 'http://' + url
        return url
    except Exception as e:
        raise Exception('Error while generating url to query the endpoint: ' + enpoint + ' . Error: ' + str(e))