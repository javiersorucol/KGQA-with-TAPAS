import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException
from string import Template

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

### endpoints
# Get entity info
@app.get('/entity/{entity_UID}')
def get_entity_data(entity_UID : str):
    try:
        res = query_api('get',(entity_prefix  + entity_UID), entity_query_headers, entity_query_params, entity_query_payload, number_of_attempts)

        if res.get('code') != 200:
            if res.get('code') == 400:
                raise HTTPException(status_code=400, detail='Error, entity not found. Code ' + str(res.get('code')) + " : " + res.get('text'))
            else:
                raise HTTPException(status_code=502, detail='Wikidata External API error. Code ' + str(res.get('code')) + " : " + res.get('text'))

    
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

# Get Entity Classes
@app.get('/entity/classes/{entity_UID}')
def get_entity_classes(entity_UID : str):
    try:

        res = sparql_query_kg(classes_sparql, { 'entity_UID' : entity_UID, 'class_property_UID' : class_property_UID })
        
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Wikidata External API error. Code ' + str(res.get('code')) + " : " + res.get('text'))

        # if there are no result
        if len(res.get('json').get('results').get('bindings')) == 0:
            raise HTTPException(status_code=400, detail='Error, entity not found, or there are not classes related to this entity. Response: ' + str(res))
        
        return [ x.get('class').get('value').replace(entity_prefix,'') for x in res.get('json').get('results').get('bindings')]
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error while retrieving classes for entity: ' + entity_UID + '. ' + str(e))

# Get a class template data
@app.get('/class/template/{class_UID}')
def get_class_template( class_UID: str):
    try:
        template = { 'frequency': 1,
        'subclasses' : get_class_subclasses(class_UID),
        'properties': get_class_properties(class_UID) 
        }
        return template
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining ' + class_UID + ' template. Error: ' + str(e))


### Functions
def get_class_properties(class_UID : str):
    try:
        # Using the properties for this class property to look for properties
        res = sparql_query_kg(properties_sparql, { 'class_UID' : class_UID, 'class_properties_UID' : class_properties_UID })
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error obtaining ' + class_UID +'properties, Wikidata API returned an error to the SPARQL query. Code ' + str(res.get('code')) + " : " + res.get('text'))
        
        res = res.get('json')
        class_properties_dict = {}
        
        # adding properties
        for prop in res.get('results').get('bindings'):
            class_properties_dict[prop.get('prop').get('value').replace(entity_prefix, '')] = { 
                'label' : prop.get('propLabel').get('value'),
                'type' : prop.get('propType').get('value').replace(ontology_prefix, '') 
            }
        
        # If no properties were found, search for compound classes 
        if len(class_properties_dict.items()) == 0:
            union_values = get_class_union_classes(class_UID)
            props_source = []
            props = {}
            if len(union_values) > 0:
                props_source = union_values
                
            else:
                # check parent clases
                props_source = get_class_parents(class_UID)
                
                # update if there is extra properties in this class (properties that are not inherit form the parent class)
                props.update(get_class_extra_properties(class_UID))

            props.update(get_related_classes_props(props_source))
            class_properties_dict.update(props)
        
        # Remove no valid data types
        class_properties_dict = dict(filter(lambda x: x[1]['type'] not in banned_data_types, class_properties_dict.items()))

        return class_properties_dict
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining ' + class_UID + ' total properties. Error: ' + str(e))


def get_class_parents(class_UID : str):
    try:
        res = sparql_query_kg(parents_sparql, { 'class_UID' : class_UID, 'subclass_property_UID' : subclass_property_UID })
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error obtaining ' + class_UID +' parent classes, Wikidata API returned an error to the SPARQL query. Code ' + str(res.get('code')) + " : " + res.get('text'))
        
        return [ x.get('parent').get('value').replace(entity_prefix,'') for x in res.get('json').get('results').get('bindings')]
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining ' + class_UID + ' parent classes. Error: ' + str(e))

def get_class_extra_properties(class_UID : str):
    # Get class extra properties
    try:
        res = sparql_query_kg(extra_properties_sparql, { 'class_UID' : class_UID, 'extra_properties_UID' : extra_properties_UID })
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error obtaining ' + class_UID +' extra properties, Wikidata API returned an error to the SPARQL query. Code ' + str(res.get('code')) + " : " + res.get('text'))

        inherited_properties_dict = {}
        for prop in res.get('json').get('results').get('bindings'):
            inherited_properties_dict[prop.get('prop').get('value').replace(entity_prefix, '')] = {
                'label' : prop.get('propLabel').get('value'),
                'type' : prop.get('propType').get('value').replace(ontology_prefix, '')
            }
        
        return inherited_properties_dict
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining ' + class_UID + ' extra properties. Error: ' + str(e))


def get_class_union_classes(class_UID : str):
    try:
        res = sparql_query_kg(union_sparql, { 'class_UID' : class_UID, 'union_of_property_UID' : union_property_UID })
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error obtaining ' + class_UID +' union classes, Wikidata API returned an error to the SPARQL query. Code ' + str(res.get('code')) + " : " + res.get('text'))
        
        return [ x.get('class').get('value').replace(entity_prefix,'') for x in res.get('json').get('results').get('bindings')]
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining ' + class_UID + ' union classes. Error: ' + str(e))

def get_class_subclasses(class_UID : str):
    try:
        res = sparql_query_kg(subclasses_sparql, { 'class_UID' : class_UID, 'subclass_property_UID' : subclass_property_UID })
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error obtaining ' + class_UID +' subclasses, Wikidata API returned an error to the SPARQL query. Code ' + str(res.get('code')) + " : " + res.get('text'))
        
        return [ x.get('subclass').get('value').replace(entity_prefix,'') for x in res.get('json').get('results').get('bindings')]
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining ' + class_UID + ' subclasses. Error: ' + str(e))

def get_related_classes_props(related_classes):
    # get the relted classes properties
    try:
        # Query to get the list of class properties and its info
        props = {}
        for source in related_classes:
            res = sparql_query_kg(properties_sparql, { 'class_UID' : source, 'class_properties_UID' : class_properties_UID })
            if res.get('code') != 200:
                raise HTTPException(status_code=502, detail='Error obtaining ' + source +' related classes properties. Wikidata API returned an error to the SPARQL query. Code ' + str(res.get('code')) + " : " + res.get('text'))
            
            related_properties_dict = {}
            for prop in res.get('json').get('results').get('bindings'):
                related_properties_dict[prop.get('prop').get('value').replace(entity_prefix, '')] = {
                    'label' : prop.get('propLabel').get('value'),
                    'type' : prop.get('propType').get('value').replace(ontology_prefix, '') }
            props.update(related_properties_dict)
            #templates[source] = { 'freq' : 1, 'subclasses' : self.get_class_subclasses(source), 'props' : props }
        
        return props
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining ' + str(related_classes) + ' properties. Error: ' + str(e))


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
                return (value.get('value').get('amount')) 
            elif data_type == 'globe-coordinate':
                return 'Latitud: ' + str(value.get('value').get('latitude')) + ' Longitud: ' + str(value.get('value').get('longitude')) + ' Altitud: ' + str(value.get('value').get('altitude')) + ' Presición: ' + str(value.get('value').get('precision')) + ' Planeta: ' + value.get('value').get('globe')
            else:
                return value.get('value')
        else:
            return None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown while obtaining the value. Data type: ' + data_type + '. Value src: ' + str(value) + ' Error: ' + str(e))

def sparql_query_kg(sparql: str, sparql_params:dict):
    try:
        sparql_template = Template(sparql)
        sparql_query = sparql_template.substitute(sparql_params)
        kg_query_params = {'query' : sparql_query, 
                        'format' : 'json'}
        res = query_api('get', query_endpoint, { 'User-Agent' : 'SubgraphBot/0.1, bot for obtention of class subgraphs (javiersorucol1@upb.edu)' }, kg_query_params, {})

        return res
    
    except Exception as e:
        return { 'code': 500, 'json' : None, 'text': 'Error while preparing the SPARQL query. Error: ' + str(e) }
