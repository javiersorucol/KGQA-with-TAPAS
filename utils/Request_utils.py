import requests
from fastapi import HTTPException
from utils.Configuration_utils import read_config_file

def query_api(method:str, url:str, headers:dict, params:dict, json_payload:dict, attempts:int = 1):
    try:
        attempt = 0
        res = None
        while attempt < attempts:
            attempt = attempt + 1
            if method == 'get':
                res = requests.get(url, params=params, headers=headers, json=json_payload)
            elif method =='post':
                res = requests.post(url, params=params, headers=headers, json=json_payload)
            else:
                raise Exception('Unexpected method.')
            if res.status_code == 200:
                break
        
        return { 'code': res.status_code, 'json' : res.json() }
    
    except Exception as e:
        print('---------------------------------------------------------------------------------')
        print('Error with request, method: ', method, ', url: ', url, ', headers: ', headers, ', params: ', params, ', json_payload: ', json_payload)
        print('Error: ', str(e))
        print('---------------------------------------------------------------------------------')
        return { 'code': res.status_code, 'json' : None, 'text': res.text }
    
# Functions to query the app internal APIs

# Reding the app configurations to communicate with other APIs
app_config_file_path = 'App_config.ini'
app_config = read_config_file(app_config_file_path)

translation_service = dict(app_config.items('TRANSLATION_SERVICE'))
linking_service = dict(app_config.items('LINKING_SERVICE'))
graph_query_service = dict(app_config.items('GRAPH_QUERY_SERVICE'))

def translate(query:str, lang:str):
    # to translate we will query the translation service
    try:
        global translation_service
        
        payload = { 'text' : query, 'mode' : lang + '-en' }

        url = get_service_url(translation_service, 'translate_endpoint')

        res = query_api('post', url, {}, {}, payload)
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Translation service returned an error. Code: ' + str(res.get('code')) + ' . Error: ' + res.get('text'))

        return res.get('json')

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying translation service: ' + str(e))


def link_graph_elements(query:str):
    # to link to graph elements we will query the linking service
    try:
        global linking_service

        payload = { 'text' : query }

        url = get_service_url(linking_service, 'link_endpoint')
        res = query_api('post', url, {}, {}, payload)
    
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Linking service returned an error. Code: ' + str(res.get('code')) + ' . Error: ' + res.get('text'))

        return res.get('json')

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying linking service: ' + str(e))


def get_entity_classes(entity_UID:str):
    try:
        global graph_query_service
        
        url = get_service_url(graph_query_service, 'entity_classes_endpoint') + entity_UID
        res = query_api('get', url, {}, {}, {})

        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Graph Query service returned an error. Code: ' + str(res.get('code')) + ' . Error: ' + res.get('text'))

        return res.get('json')

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying graph query service: ' + str(e))


def get_service_url(service:dict, enpoint:str):
    try:    
        url = service.get('ip') + ':' + service.get('port') + service.get(enpoint)
        if 'http://' not in url:
            url = 'http://' + url
        return url
    except Exception as e:
        raise Exception('Error while generating url to query the endpoint: ' + enpoint + ' . Error: ' + str(e))

