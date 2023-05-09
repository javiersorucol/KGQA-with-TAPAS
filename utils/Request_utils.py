import requests
from fastapi import HTTPException
from utils.Configuration_utils import read_config_file

def query_api(method:str, url:str, headers:dict, params:dict, payload, attempts:int = 1, paylod_type:str='json'):
    try:
        attempt = 0
        res = None
        while attempt < attempts:
            attempt = attempt + 1
            if paylod_type == 'json':
                if method == 'get':
                    res = requests.get(url, params=params, headers=headers, json=payload)
                elif method =='post':
                    res = requests.post(url, params=params, headers=headers, json=payload)
                elif method == 'put':
                    res = requests.put(url, params=params, headers=headers, json=payload)
                else:
                    raise Exception('Unexpected method.')
            else:
                if method == 'get':
                    res = requests.get(url, params=params, headers=headers, data=payload)
                elif method =='post':
                    res = requests.post(url, params=params, headers=headers, data=payload)
                elif method == 'put':
                    res = requests.put(url, params=params, headers=headers, data=payload)
                else:
                    raise Exception('Unexpected method.')
            if res.status_code == 200:
                break
        
        return { 'code': res.status_code, 'json' : res.json() }
    
    except Exception as e:
        print('---------------------------------------------------------------------------------')
        print('Error with request, method: ', method, ', url: ', url, ', headers: ', headers, ', params: ', params, ', json_payload: ', payload)
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
templates_service = dict(app_config.items('TEMPLATES_SERVICE'))

def fill_templates(templates:dict):
    try:
        global graph_query_service
        
        url = get_service_url(graph_query_service, 'fill_template_endpoint')
        res = query_api('post', url, {}, {}, templates)
        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying the graph query service to fill the templates: ' + str(e))

def translate(query:str, lang:str):
    # to translate we will query the translation service
    try:
        global translation_service
        
        payload = { 'text' : query, 'mode' : lang + '-en' }

        url = get_service_url(translation_service, 'translate_endpoint')

        res = query_api('post', url, {}, {}, payload)
        
        return res

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
    
        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying linking service: ' + str(e))


def get_entity_classes(entity_UID:str):
    try:
        global graph_query_service
        
        url = get_service_url(graph_query_service, 'entity_classes_endpoint') + entity_UID
        res = query_api('get', url, {}, {}, {})

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining informtion from entity ' + entity_UID + ': ' + str(e))

def generate_class_template(class_UID:str):
    try:
        global graph_query_service

        url = get_service_url(graph_query_service, 'class_template_endpoint') + class_UID
        res = query_api('get', url, {}, {}, {})

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while generating class template for class ' + class_UID + ': ' + str(e))

def get_question_tables(linked_data:dict):
    try:
        url = get_service_url(templates_service, 'question_templates_endpoint')
        res = query_api('post', url, {}, {}, linked_data)

        return res
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while generating class tables : ' + str(e))

def get_service_url(service:dict, enpoint:str):
    try:    
        url = service.get('ip') + ':' + service.get('port') + service.get(enpoint)
        if 'http://' not in url:
            url = 'http://' + url
        return url
    except Exception as e:
        raise Exception('Error while generating url to query the endpoint: ' + enpoint + ' . Error: ' + str(e))

