import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException
from utils.Request_utils import query_api

from utils.Configuration_utils import read_config_file

# Reading the config file
config_file_path = 'graph_query_service/Config/Config.ini'
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
classes_sparql = config['SPARQL']['classes']
subclasses_sparql = config['SPARQL']['subclasses']
union_sparql = config['SPARQL']['union']
extra_properties_sparql = config['SPARQL']['extra_properties']
parents_sparql = config['SPARQL']['parents']
properties_sparql = config['SPARQL']['properties']
table_sparql = config['SPARQL']['table']
table_property_template = config['SPARQL']['table_property_template']

# Graph ontology UID
ontology_prefix = config['KNOWLEDGE_GRAPH']['ontology_prefix']
class_property_UID = config['KNOWLEDGE_GRAPH']['class_property_UID']
subclass_property_UID = config['KNOWLEDGE_GRAPH']['subclass_property_UID']
union_property_UID = config['KNOWLEDGE_GRAPH']['union_property_UID']
extra_properties_UID = config['KNOWLEDGE_GRAPH']['extra_properties_UID']
class_properties_UID = config['KNOWLEDGE_GRAPH']['class_properties_UID']

banned_data_types = config.get('KNOWLEDGE_GRAPH', 'banned_data_types').split()
number_of_attempts = int(config['SERVER_PARAMS']['number_of_attempts'])
table_max_lenght = config['SERVER_PARAMS']['table_max_lenght']

app = FastAPI()

#endpoints
@app.get('/entity/{entity_UID}')
def get_entity_data(entity_UID : str):
    res = query_api('get',(entity_prefix  + entity_UID), entity_query_headers, entity_query_params, entity_query_payload, number_of_attempts)
    
    if res.get('code') != 200:
        raise HTTPException(status_code=502, detail='Wikidata External API error. Code ' + res.get('status_code') + " : " + res.get('text'))
    
    try:
        query_dto = res.get('json').get('entities').get(entity_UID)
        entity_dto = {}
        entity_dto['label'] = query_dto.get('labels').get('en').get('value')
        entity_dto['UID'] = entity_UID
        entity_dto['props'] = {}

        for key, value in query_dto.get('claims').items():
            # initialize the entity properties, the data type is the same for all the property instances
            data_type = value[0].get('mainsnak').get('datatype')
            entity_dto['props'][key] =  { 
                                            'data_type': data_type,
                                            'values': []
                                        }
            for instance in value:
                # for every instance of the property append a value
                entity_dto['props'][key]['values'].append(get_value_by_type(data_type, instance.get('mainsnak').get('datavalue')))

        return entity_dto
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error while retrieving the information for entity: ' + entity_UID + '. ' + str(e))

def get_value_by_type(data_type: str, value: dict):
    try:
        # how to get the value depending on the data type
        if value is not None:
            if data_type == 'wikibase-item':
                return value.get('value').get('id')
            elif data_type == 'time':
                return value.get('value').get('time')
            elif data_type == 'monolingualtext':
                return value.get('value').get('text')
            elif data_type == 'quantity':
                #unit = ''
                #if value.get('value').get('unit') is not None:
                #    unit = value.get('value').get('unit')
                #    unit = unit if entity_prefix not in unit else get_entity_data(unit.replace(entity_prefix,'')).get('label')
                return (value.get('value').get('amount')) 
                    #(' unit: ' +  unit) +  
                    #(' upper bound: ' + value.get('value').get('upperBound') if value.get('value').get('upperBound') is not None else '' ) +
                    #(' lower bound: ' + value.get('value').get('lowerBound') if value.get('value').get('lowerBound') is not None else '' ) )
            elif data_type == 'globe-coordinate':
                return 'Latitud: ' + str(value.get('value').get('latitude')) + ' Longitud: ' + str(value.get('value').get('longitude')) + ' Altitud: ' + str(value.get('value').get('altitude')) + ' Presición: ' + str(value.get('value').get('precision')) + ' Planeta: ' + value.get('value').get('globe')
            else:
                return value.get('value')
        else:
            return None
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown while obtaining the value. Data type: ' + data_type + '. Value src: ' + str(value) + ' Error: ' + str(e))
