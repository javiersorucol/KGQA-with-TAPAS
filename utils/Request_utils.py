import requests
from fastapi import HTTPException
from utils.Configuration_utils import read_config_file
from DTOs.linking_DTOs import Linked_Data_DTO

def query_api(method:str, url:str, headers:dict, params:dict, payload, attempts:int = 2, paylod_type:str='json'):
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
        
        return { 'code': res.status_code, 'json' : res.json(), 'text': res.text }
    
    except Exception as e:
        print('---------------------------------------------------------------------------------')
        print('Error with request, method: ', method, ', url: ', url)
        print('Error: ', str(e))
        print('Received response: ', res.text)
        print('---------------------------------------------------------------------------------')
        if res is not None:
            return { 'code': res.status_code, 'json' : None, 'text': res.text }
        else:
            return { 'code':500, 'json':None, 'text': str(e) }
    
# Functions to query the app internal APIs

# Reding the app configurations to communicate with other APIs
app_config_file_path = 'App_config.ini'
app_config = read_config_file(app_config_file_path)

translation_service = dict(app_config.items('TRANSLATION_SERVICE'))
linking_service = dict(app_config.items('LINKING_SERVICE'))
graph_query_service = dict(app_config.items('GRAPH_QUERY_SERVICE'))
answer_service = dict(app_config.items('ANSWER_SERVICE'))
main_service = dict(app_config.items('MAIN_SERVICE'))

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

def get_answer_tapas_method(question : str, lang : str = 'en'):
    try:
        global main_service

        url = get_service_url(main_service, 'tapas_endpoint')
        res = query_api('post', url, {}, {}, {
            'text' : question,
            'lang' : lang
        })

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying Main service: ' + str(e))

def get_answer_gpt_method(question : str, lang : str = 'en'):
    try:
        global main_service

        url = get_service_url(main_service, 'gpt_endpoint')
        res = query_api('post', url, {}, {}, {
            'text' : question,
            'lang' : lang
        })

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying Main service: ' + str(e))

def get_entity_triples_lang_chain(entities : Linked_Data_DTO, question):
    try:
        global graph_query_service
        
        url = get_service_url(graph_query_service, 'entity_triples_langchain_endpoint')
        res = query_api('post', url, {}, {'question':question}, entities)

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying Graph Query service for the entity triples: ' + str(e))

def get_entity_triples(entity_UID : str):
    try:
        global graph_query_service
        
        url = get_service_url(graph_query_service, 'entity_triples_endpoint')
        res = query_api('get', url + entity_UID, {}, {}, {})

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying Graph Query service for the entity triples: ' + str(e))

def get_entity_table(entity_UID : str):
    try:
        global graph_query_service
        
        url = get_service_url(graph_query_service, 'entity_table_endpoint')
        res = query_api('get', url + entity_UID, {}, {}, {})
        
        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying Graph Query service for the entity table: ' + str(e))

def ask_gpt_v1(triples : str, question : str):
    try:
        global answer_service

        url = get_service_url(answer_service, 'ask_gpt_endpoint_v1')
        res = query_api('post', url, {}, {}, { 'triples' : triples, 'question' : question })

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying answer service for gpt answer: ' + str(e))

def ask_gpt_v2(triples : str, question : str):
    try:
        global answer_service

        url = get_service_url(answer_service, 'ask_gpt_endpoint_v2')
        res = query_api('post', url, {}, {}, { 'triples' : triples, 'question' : question })

        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying answer service for gpt answer: ' + str(e))

def ask_tapas(table : dict, question : str):
    try:
        global answer_service

        url = get_service_url(answer_service, 'ask_tapas_endpoint')
        res = query_api('post', url, {}, {}, {
            'question':question,
            'table': table
        })
        
        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying answer service for tapas answer: ' + str(e))


def link_graph_elements_gpt_v1(query:str):
    # to link to graph elements we will query the linking service
    try:
        global linking_service

        payload = { 'text' : query }

        url = get_service_url(linking_service, 'link_endpoint_gpt_v1')
        res = query_api('post', url, {}, {}, payload)
    
        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying linking service: ' + str(e))


def link_graph_elements(query:str):
    # to link to graph elements we will query the linking service
    try:
        global linking_service

        payload = { 'text' : query }

        url = get_service_url(linking_service, 'link_main_endpoint')
        res = query_api('post', url, {}, {}, payload)
    
        return res

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while querying linking service: ' + str(e))


def get_service_url(service:dict, enpoint:str):
    try:    
        url = service.get('ip') + ':' + service.get('port') + service.get(enpoint)
        if 'http://' not in url:
            url = 'http://' + url
        return url
    except Exception as e:
        raise Exception('Error while generating url to query the endpoint: ' + enpoint + ' . Error: ' + str(e))

