import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException
from string import Template
from typing import List

from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json

import copy
from pathlib import Path

config_file_path = 'graph_query_service/Config/Config.ini'

# check if required config files exist
if not Path(config_file_path).is_file():
    print('Config file was not found for the graph query service.')
    exit()

# Reading the config file
config = read_config_file(config_file_path)

# saving config vars
# Query entity data
entity_prefix = config['KNOWLEDGE_GRAPH']['entity_prefix']
entity_query_headers = dict(config.items('ENTITY_QUERY_HEADERS'))
entity_query_payload = dict(config.items('ENTITY_QUERY_PAYLOAD'))
entity_query_params = dict(config.items('ENTITY_QUERY_PARAMS'))

# Query sparql
query_endpoint = config['KNOWLEDGE_GRAPH']['query_endpoint']
kg_query_headers = dict(config.items('KG_QUERY_HEADERS'))
kg_query_payload = dict(config.items('KG_QUERY_PAYLOAD'))
kg_query_params = dict(config.items('KG_QUERY_PARAMS'))

# sparql queries
labels_sparql = config['SPARQL']['labels']

# Graph ontology UID
ontology_prefix = config['KNOWLEDGE_GRAPH']['ontology_prefix']

banned_data_types = config.get('KNOWLEDGE_GRAPH', 'banned_data_types').split()
banned_words = config.get('KNOWLEDGE_GRAPH', 'banned_words').split()

number_of_attempts = int(config['SERVER_PARAMS']['number_of_attempts'])
banned_data_path = config['SERVER_PARAMS']['banned_data_path']

# Reding the service configurations
app_config_file_path = 'App_config.ini'
app_config = read_config_file(app_config_file_path)
graph_query_service = dict(app_config.items('GRAPH_QUERY_SERVICE'))

banned_data = { 'banned_properties' : [] }

if not os.path.exists(banned_data_path):
    save_json(filename=banned_data_path, data=banned_data)
else:
    banned_data = read_json(banned_data_path)

app = FastAPI()

### endpoints

# Get entity data
@app.get('/entity/table/{entity_UID}')
def get_entity_table(entity_UID : str):
    def filter_properties(pair):
        # function to filter the banned properties types and banned properties
        global banned_data
        global banned_data_types

        key, value = pair
        if key not in banned_data.get('banned_properties') and value[0].get('mainsnak').get('datatype') not in banned_data_types:
            return True
        else:
            return False
    
    def filter_actual_values(values : List):
        # function to filter prefered values
        prefered_values = list(filter(lambda x: x.get('rank') == 'preferred',values))
        if len(prefered_values) == 0:
            return values
        else:
            return prefered_values
        
    def filter_properties_by_label(label:str, property_uid:str):
        #function to filter properties with banned words in the label
        global banned_words
        global banned_data
        global banned_data_path

        label = label.lower()

        for word in banned_words:
            if word in label:
                banned_data['banned_properties'].append(property_uid)
                save_json(filename=banned_data_path, data=banned_data)
                return False
            
        return True

    try:    
        global banned_data_types
        global entity_prefix

        # get the entity data
        entity_dto = get_entity_data(entity_UID)

        # initialize base elements on the tables
        entity_table_base = {
            'URI' : [entity_prefix + entity_dto.get('id')],
            'label' : [entity_dto.get('labels').get('en').get('value') if entity_dto.get('labels').get('en') is not None else ''],
            'description' : [entity_dto.get('descriptions').get('en').get('value') if entity_dto.get('descriptions').get('en') is not None else ''],
            'aliases' : [ list_to_str([ x.get('value') for x in entity_dto.get('aliases').get('en') ]) if entity_dto.get('aliases').get('en') is not None else '' ]
            }

        # we will providef a table with the values uris and a table with the values labels
        entity_table_URI = copy.deepcopy(entity_table_base)
        entity_table_labels = copy.deepcopy(entity_table_base)

        # we will filter banned properties types
        filtered_properties = dict(filter(filter_properties, entity_dto.get('claims').items()))
        
        # we will store unique entities and properties uids to construct a labels mapping dict
        unique_entity_UIDs = []
        property_UIDs = list(filtered_properties.keys())

        # for each filtered property
        for key, values_list in filtered_properties.items():
            # we will filter prefered values
            filtered_values = filter_actual_values(values_list)
            # we will get the value using the datatype
            property_datatype = values_list[0].get('mainsnak').get('datatype')
            filtered_values = list(filter(lambda x: x is not None, [get_value_by_type(property_datatype, x.get('mainsnak').get('datavalue')) for x in filtered_values]))
            # we will store the new entity uids
            if property_datatype == 'wikibase-item' or property_datatype == 'wikibase-property':
                unique_entity_UIDs = unique_entity_UIDs + filtered_values
            # we will save the values in the uri table
            entity_table_URI[key] = filtered_values

        # save only unique values and remove the entity prefix
        unique_entity_UIDs = [ x.replace(entity_prefix,'') for x in list(set(unique_entity_UIDs)) ]

        # if 'Q25556329' in unique_entity_UIDs:
        #     print(key)

        # construct a map to get labels usinf the uri
        labels_map = get_labels_from_UIDs(property_UIDs + unique_entity_UIDs)

        discarted_properties = []

        # for each column in the uri table
        for key, values_list in entity_table_URI.items():
            # only for columns that arent in the labels table
            if entity_table_labels.get(key) is None:
                # if there's an available mapping value, use the value in any other case keep the value of the uri table
                labels = [ labels_map.get(x) if labels_map.get(x) is not None else x for x in values_list]
                # store the values in string form in the labels table
                property_label = labels_map.get(entity_prefix + key)

                # Do not work if the prperty label contains substring ctegory or commons as they have no value for our table
                if filter_properties_by_label(label=property_label, property_uid=key):
                    entity_table_labels[ property_label ] = [ list_to_str(labels) ]
                    # modify to use the string form in the uri table
                    entity_table_URI[key] = [ list_to_str(values_list) ]
                
                else:
                    discarted_properties.append(key)

        # remove category and commons properties from uri table
        for key in discarted_properties:
            del entity_table_URI[key]

        return { 'labels_table' : entity_table_labels, 'uri_table' : entity_table_URI }

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while generating entity table. Error: ' + str(e))

### Functions
def get_labels_from_UIDs(uids : List, prefix : str = 'wd'):
    def get_query_header(uids : List, prefix : str):
        # function to  construct the header of the sparql  query using a template
        header_template = Template('${prefix}:${uid} rdfs:label ?${uid}Label')
        headers = []
        for uid in uids:
            headers.append(header_template.substitute({ 'uid': uid, 'prefix' : prefix }))
        return ' . '.join(headers)
    
    def get_query_body(uids : List, prefix : str):
        # function to  construct the body of the sparql  query using a template
        body_template = Template('${prefix}:${uid} rdfs:label ?${uid}Label filter(lang(?${uid}Label)="en")')
        body = []
        for uid in uids:
            body.append(body_template.substitute({ 'uid' : uid, 'prefix' : prefix }))
        return ' . '.join(body)
    
    try:
        # query wikidata to obtain labels
        res = sparql_query_kg(sparql=labels_sparql, sparql_params={ 
            'headers' : get_query_header(uids, prefix),
            'body' : get_query_body(uids, prefix)
        })
        
        if res.get('code') != 200:
            # if the query did not work, we will query one label at the time
            res['json'] = {'results':{'bindings':[]}}
            
        labels_map = {}
        results = []

        # if no elements are returne it might be because a element has no label, in this case we will query the label element by element and return the uid
        # for the unlabeled element
        if len(res.get('json').get('results').get('bindings')) == 0:
            for uid in uids:
                res = sparql_query_kg(sparql=labels_sparql, sparql_params={ 
                    'headers' : get_query_header([uid], prefix),
                    'body' : get_query_body([uid], prefix)
                })
                
                if res.get('code') != 200:
                    raise HTTPException(status_code=502, detail='Unexpected error while querying wikidata for labels. Error: ' + res.get('text'))
                
                if len(res.get('json').get('results').get('bindings')) == 0:
                    results.append({'subject': {'value':uid}, 'object': {'value':uid}})
                else:
                    results.append(res.get('json').get('results').get('bindings')[0])
        else:
            results = res.get('json').get('results').get('bindings')

        # populate the dict with the results
        for element in results:
            labels_map[element.get('subject').get('value')] = element.get('object').get('value')
        
        return labels_map
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining labels. Error: ' + str(e))


def list_to_str(list : List):
    # join list elements using ', ' e.g. for [1,2,3] returns '1, 2, 3'
    return ', '.join(list)

def get_entity_data(entity_UID : str):
    # query wikidata to get an entity information
    try:
        res = query_api('get',(entity_prefix  + entity_UID), entity_query_headers, entity_query_params, entity_query_payload, number_of_attempts)

        # if entity uid is incorrect
        if res.get('code') == 400:
            raise HTTPException(status_code=400, detail='Error, entity not found. Code ' + str(res.get('code')) + " : " + res.get('text'))
        
        # any other error
        elif res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Wikidata External API error. Code ' + str(res.get('code')) + " : " + res.get('text'))

    
        return res.get('json').get('entities').get(entity_UID)

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error while retrieving the information for entity: ' + entity_UID + '. ' + str(e))

def get_value_by_type(data_type: str, value: dict):
    try:
        # how to get the value depending on the data type
        if value is not None:
            if data_type == 'wikibase-item':
                return entity_prefix + value.get('value').get('id')
            elif data_type == 'time':
                return value.get('value').get('time')
            elif data_type == 'monolingualtext':
                return value.get('value').get('text')
            elif data_type == 'quantity':
                return (value.get('value').get('amount')) 
            elif data_type == 'globe-coordinate':
                return 'Latitud: ' + str(value.get('value').get('latitude')) + ' Longitud: ' + str(value.get('value').get('longitude')) + ' Altitud: ' + str(value.get('value').get('altitude')) + ' Presición: ' + str(value.get('value').get('precision')) + ' Planeta: ' + value.get('value').get('globe')
            elif data_type == 'wikibase-property':
                return entity_prefix + value.get('value').get('id')
            elif data_type == 'string' or data_type == 'url':
                return value.get('value')
            else:
                print(data_type, ': ' , value)
                return value.get('value')
        else:
            return None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown while obtaining the value. Data type: ' + data_type + '. Value src: ' + str(value) + ' Error: ' + str(e))

def sparql_query_kg(sparql: str, sparql_params:dict):
    # query wikidata with a given sparql
    try:
        # if the sparql provided is a template we will replace the values
        sparql_template = Template(sparql)
        sparql_query = sparql_template.substitute(sparql_params)

        #print(sparql_query)

        kg_query_params = {'format' : 'json'}

        xml = "query=" + sparql_query
        
        # query wikidata
        res = query_api('post', query_endpoint, {'content-type':'application/x-www-form-urlencoded; charset=UTF-8', 'User-Agent' : 'SubgraphBot/0.1, bot for obtention of class subgraphs (javiersorucol1@upb.edu)' }, kg_query_params, xml, paylod_type='data')

        return res
    
    except Exception as e:
        return { 'code': 500, 'json' : None, 'text': 'Error while preparing the SPARQL query. Error: ' + str(e) }
