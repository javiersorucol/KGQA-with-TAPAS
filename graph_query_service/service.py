import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException
from string import Template
from typing import List

from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json

from DTOs.graph_query_DTOs import Entity_Triples_DTO, Entity_Table_DTO
from DTOs.linking_DTOs import Linked_Data_DTO

import copy
from pathlib import Path
from rdflib import Graph, Literal
import re

from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings

config_file_path = 'graph_query_service/Config/Config.ini'
app_config_file_path = 'App_config.ini'


# check if required config files exist
if not Path(config_file_path).is_file() or not Path(app_config_file_path).is_file:
    print('Config file was not found for the graph query service.')
    exit()

# Reading the config file
config = read_config_file(config_file_path)

# Saving config vars
# Query entity data
entity_prefix = config['KNOWLEDGE_GRAPH']['entity_prefix']
property_prefix = config['KNOWLEDGE_GRAPH']['property_prefix']
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
direct_triples_epo = config['SPARQL']['direct_triples_epo']
direct_triples_spe = config['SPARQL']['direct_triples_spe']
one_hop_triples_query = config['SPARQL']['one_hop_triples_query']

# Graph ontology UID
ontology_prefix = config['KNOWLEDGE_GRAPH']['ontology_prefix']

banned_data_types = config.get('KNOWLEDGE_GRAPH', 'banned_data_types').split()
banned_words = config.get('KNOWLEDGE_GRAPH', 'banned_words').split()

banned_data_path = config['SERVER_PARAMS']['banned_data_path']
labels_map_path = config['SERVER_PARAMS']['labels_map_path']

# Reding the service configurations
app_config = read_config_file(app_config_file_path)
graph_query_service = dict(app_config.items('GRAPH_QUERY_SERVICE'))

banned_data = { 'banned_properties' : [] }
labels_map = { 'no_label_elements': [] }

# if the banned_data.json file does not exist, create it, if it does, read it
if not os.path.exists(banned_data_path):
    save_json(filename=banned_data_path, data=banned_data)
else:
    banned_data = read_json(banned_data_path)

# if the labels_map.json file does not exist, create it, if it does, read it
if not os.path.exists(labels_map_path):
    save_json(filename=labels_map_path, data=labels_map)
else:
    labels_map = read_json(labels_map_path)

app = FastAPI()

### endpoints
@app.post(graph_query_service.get('entity_triples_langchain_endpoint'))
def get_entity_triples_lang(question:str, entities : Linked_Data_DTO, k:int=15):
    def get_value_from_dict(dict, key):
        if dict.get(key) is None:
            return key
        else:
            return dict.get(key)

    def get_entity_direct_triples(entity_UID):

        print('Getting direct triples for entity ', entity_UID)
        data = []
        # Get direct triples in format entity, predicate, object
        res = sparql_query_kg(direct_triples_epo, { 'uid' : entity_UID })
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Wikidata External API error getting direct triples (e, p, o). Code ' + str(res.get('code')) + " : " + res.get('text'))

        if res.get('json').get('results') is not None and res.get('json').get('results').get('bindings') is not None:
            data = data + res.get('json').get('results').get('bindings')
        else:
            print('Error retrieving epo triples for entity: ', entity_UID)

        # Get direct triples in format subject, predicate, object
        res = sparql_query_kg(direct_triples_spe, { 'uid' : entity_UID })
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Wikidata External API error getting direct triples (s, p, e). Code ' + str(res.get('code')) + " : " + res.get('text'))
        
        if res.get('json').get('results') is not None and res.get('json').get('results').get('bindings') is not None:
            data = data + res.get('json').get('results').get('bindings')
        else:
            print('Error retrieving spe triples for entity: ', entity_UID)
        
        #print('Number of direct triples found for entity ', entity_UID, ' : ', len(data))

        #print(data)

        entity_URI = entity_prefix + entity_UID
        entity_label = get_labels_from_UIDs([entity_UID]).get(entity_UID)

        one_hop_entities = []
        unique_entities = []
        unique_properties = []

        triples_dict = { 'epo' : {}, 'spe' : {} }

        for triple in data:
            #subject: if subjct is uri with wikidata prefix and it's not saved in the unique uri list
            subject_value = triple.get('subject').get('value')
            if triple.get('subject').get('type') == 'uri' and entity_prefix in subject_value:
                subject_value = subject_value.replace(entity_prefix, '')
                if subject_value not in unique_entities:
                    unique_entities.append(subject_value)
            
            # predicate: if property not in the list
            predicate_value = triple.get('predicate').get('value').replace(property_prefix, '')
            if predicate_value not in unique_properties:
                unique_properties.append(predicate_value)

            # object: same as subject
            object_value = triple.get('object').get('value')
            if triple.get('object').get('type') == 'uri' and entity_prefix in object_value:
                object_value = object_value.replace(entity_prefix, '')
                if object_value not in unique_entities:
                    unique_entities.append(object_value)
                    # we will only keep one hop entities in the form entity, predicate, object
                    one_hop_entities.append(object_value)

            case = None
            value = None
            # now we will put the triples in format, we have two cases e,p,o and s,p,e
            # To identify which kind of triples we have, we will check where is th given entity
            if triple.get('subject').get('value') == entity_URI:
                #  case e,p,o
                case = 'epo'
                value = object_value
            elif triple.get('object').get('value') == entity_URI:
                #  case s,p,e
                case = 'spe'
                value = subject_value
            else:
                print('ERROR CASE')
                print(triple)

            # Now we will group data in a dict form organized by cases
            if triples_dict.get(case).get(predicate_value) is None:
                triples_dict[case][predicate_value] = [value]
            else:
                triples_dict[case][predicate_value].append(value)

        # We will ask for the required labels to cache or Wikidata
        property_labels_dict = get_labels_from_UIDs(uids=unique_properties)
        entity_labels_dict = get_labels_from_UIDs(uids=unique_entities)

        # Now we will set data in verbalzied triples format

        #print('Number of epo triples: ', len(triples_dict.get('epo')))
        #print('Number of spe triples: ', len(triples_dict.get('spe')))

        entity_graph = Graph()
        # Transform e,p,o to triples format
        for property, object in triples_dict.get('epo').items():
            entity_graph.add( (Literal(entity_label), Literal(get_value_from_dict(property_labels_dict, property)), Literal(';'.join([get_value_from_dict(entity_labels_dict, x) for x in object]))) )

        # Transform s,p,e to triples format
        for property, object in triples_dict.get('spe').items():
            entity_graph.add( ( Literal(';'.join([get_value_from_dict(entity_labels_dict, x) for x in object])), Literal(get_value_from_dict(property_labels_dict, property)), Literal(entity_label)) )


        return (one_hop_entities, entity_graph.serialize(format='nt').replace('\n','\n').replace(' .',''))

    def get_one_hop_triples(uids):
        # we get direct e,p,o triples for each one hop entity
        global one_hop_triples_query
        # If no uids are provided return empty string
        if len(uids) == 0:
            return ''

        # query for triples
        res = sparql_query_kg(one_hop_triples_query, { 'uids' : ' '.join([ 'wd:' + x for x in uids]) })

        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Wikidata External API error getting one hop triples. Code ' + str(res.get('code')) + " : " + res.get('text'))

            
        print('Getting one-hop triples for ', len(uids), ' one-hop entities')

        unique_entities = []
        unique_properties = []
        triples_dict = {} ## Format { subject: { property: [objects], .... }}

        if res.get('json').get('results') is not None and res.get('json').get('results').get('bindings') is not None:
            for triple in res.get('json').get('results').get('bindings'):
                # Save subject value es unique entity
                subject_value = triple.get('subject').get('value')
                if triple.get('subject').get('type') == 'uri' and entity_prefix in subject_value:
                    subject_value = subject_value.replace(entity_prefix, '')
                    if subject_value not in unique_entities:
                        unique_entities.append(subject_value)
                
                # predicate: if property not in the list
                predicate_value = triple.get('predicate').get('value').replace(property_prefix, '')
                if predicate_value not in unique_properties:
                    unique_properties.append(predicate_value)

                # object: same as subject
                object_value = triple.get('object').get('value')
                if triple.get('object').get('type') == 'uri' and entity_prefix in object_value:
                    object_value = object_value.replace(entity_prefix, '')
                    if object_value not in unique_entities:
                        unique_entities.append(object_value)

                # add data to dict
                if triples_dict.get(subject_value) is None:
                    triples_dict[subject_value] = {}
                
                if triples_dict.get(subject_value).get(predicate_value) is None:
                    triples_dict[subject_value][predicate_value] = [object_value]
                elif object_value not in triples_dict.get(subject_value).get(predicate_value):
                    triples_dict.get(subject_value).get(predicate_value).append(object_value)

        property_labels_dict = get_labels_from_UIDs(uids=unique_properties)
        entity_labels_dict = get_labels_from_UIDs(uids=unique_entities)

        entity_graph = Graph()
        
        for subject, data in triples_dict.items():
            for predicate, objects in data.items():
                entity_graph.add( (Literal(get_value_from_dict(entity_labels_dict, subject)), Literal(get_value_from_dict(property_labels_dict, predicate)), Literal(';'.join([get_value_from_dict(entity_labels_dict, x) for x in objects]))) )

        return entity_graph.serialize(format='nt').replace('\n','\n').replace(' .','')

        
    
    # Get entity direct triples
    unique_entities = []
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    embedding = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    text_splitter = CharacterTextSplitter(chunk_size=1,chunk_overlap=0, separator="\n")
    chunks = []
    text_triples = ''

    # get data for all found entities
    for entity in entities.entities:
        entity_unique_entities, direct_triples = get_entity_direct_triples(entity.get('UID'))
        print('Number of unique properties directly related to entity ', entity.get('UID'), ' : ', len(direct_triples))
        unique_entities = unique_entities + entity_unique_entities
        chunks = chunks + text_splitter.create_documents(texts=[direct_triples], metadatas=[{'source':'direct triples of entity : ' + entity.get('UID')}])
        text_triples = text_triples + '\n' + direct_triples

    print('We have ', len(chunks), ' triples from question entities')
    unique_entities = list(set(unique_entities))
    print('We have found ', len(unique_entities), ' one hope entities')
    # get data for one hop entities
    
    one_hop_data = get_one_hop_triples(unique_entities)
    text_triples = text_triples + '\n' + one_hop_data
    one_hop_triples = text_splitter.create_documents(texts=[one_hop_data], metadatas=[{'source':'one hop triples'}])
    print('We have ', len( one_hop_triples ), ' one hop triples.')

    chunks = chunks + one_hop_triples

    print('We have ', len(chunks), ' total triples (question entities + one hope entities)')

    vectordb = Chroma.from_documents(
    documents=chunks, # nuestros chunks
    embedding=embedding, # Modulo de embeddings para la transformación de chunk a embedding
    )

    save_json('multihop_1_triples.json', {'triples' : text_triples })

    selected_triples = vectordb.similarity_search(question,k=len(entities.entities)*int(k))
    print('SELECTED TRIPLES: ', selected_triples)
    return Entity_Triples_DTO(triples = '\n'.join([x.page_content for x in selected_triples]))

@app.get( graph_query_service.get('entity_triples_endpoint') + '{entity_UID}')
def get_entity_triples(entity_UID):
    try:
        global entity_prefix

        entity_unique_UIDs = []

        # get the entity data
        entity_dto = get_entity_data(entity_UID)

        # check if the entity has an available label for english, if not raise an exception as triples can't be built without using the label
        if entity_dto.get('labels').get('en') is None:
            raise HTTPException(status_code=400,detail='Bad input, provided entity is not related to an english label')
        
        # Save base values
        label = entity_dto.get('labels').get('en').get('value')
        description = entity_dto.get('descriptions').get('en').get('value') if entity_dto.get('descriptions').get('en') is not None else ''
        aliases = list_to_str([ x.get('value') for x in entity_dto.get('aliases').get('en') ]) if entity_dto.get('aliases').get('en') is not None else ''

        # we will filter banned properties types
        filtered_properties = dict(filter(filter_properties, entity_dto.get('claims').items()))
        # for each filtered property
        for key, values_list in filtered_properties.items():
            # we will filter prefered values
            filtered_values = filter_actual_values(values_list)
            filtered_properties[key] = filtered_values
            # we will get the value using the datatype
            property_datatype = filtered_values[0].get('mainsnak').get('datatype')
            filtered_values = list(filter(lambda x: x is not None, [get_value_by_type(property_datatype, x.get('mainsnak').get('datavalue')) for x in filtered_values]))
            # we will store the new entity uids
            if property_datatype == 'wikibase-item' or property_datatype == 'wikibase-property':
                entity_unique_UIDs = entity_unique_UIDs + filtered_values

        # Remove the entity prefix
        entity_unique_UIDs = [x.replace(entity_prefix,'') for x in entity_unique_UIDs]
        # Store the property UIDs
        property_unique_UIDs =  list(filtered_properties.keys())
        # construct a map to get labels using the uids
        sub_labels_map = get_labels_from_UIDs(entity_unique_UIDs + property_unique_UIDs)
        # Construct the triples using a rdflib graph
        entity_graph = Graph()
        # Add base properties to the Graph
        entity_graph.add(( Literal('urn:'+label),  Literal('urn:description'), Literal(description)))
        entity_graph.add(( Literal('urn:'+label),  Literal('urn:aliases'), Literal(aliases)))
        # for each filtered property
        for key, values_list in filtered_properties.items():
            # if there's an available mapping value, use the value in any other case keep the value of the uri table
            property_datatype = values_list[0].get('mainsnak').get('datatype')
            labels = [ sub_labels_map.get(get_value_by_type(property_datatype, x.get('mainsnak').get('datavalue'),prefix=False)) if sub_labels_map.get(get_value_by_type(property_datatype, x.get('mainsnak').get('datavalue'),prefix=False)) is not None else get_value_by_type(property_datatype, x.get('mainsnak').get('datavalue')) for x in values_list]
            # Get the property label
            property_label = sub_labels_map.get(key)
            # Do not work if the prperty label contains substring category or commons as they have no value for our table
            if filter_properties_by_label(label=property_label, property_uid=key):
                # Add the triple
                entity_graph.add(( Literal('urn:'+label), Literal('urn:' + property_label), Literal(list_to_str(labels)) ))

        return Entity_Triples_DTO(triples = entity_graph.serialize(format='nt'))
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while generating entity triples. Error: ' + str(e))


# Get entity table
@app.get(graph_query_service.get('entity_table_endpoint') + '{entity_UID}')
def get_entity_table(entity_UID : str):
    try:    
        global entity_prefix

        # get the entity data
        entity_dto = get_entity_data(entity_UID)

        # check if the entity has an available label for english, if not raise an exception as the table would be hard to interpret with no label
        if entity_dto.get('labels').get('en') is None:
            raise HTTPException(status_code=400,detail='Bad input, provided entity is not related to an english label')

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

        # construct maps to get labels using the uri
        sub_labels_map = get_labels_from_UIDs(unique_entity_UIDs + property_UIDs)

        discarted_properties = []

        # for each column in the uri table
        for key, values_list in entity_table_URI.items():
            # only for columns that arent in the labels table
            if entity_table_labels.get(key) is None:
                # if there's an available mapping value, use the value in any other case keep the value of the uri table
                labels = [ sub_labels_map.get(x.replace(entity_prefix,'')) if sub_labels_map.get(x.replace(entity_prefix,'')) is not None else x for x in values_list]
                # Get the property label
                property_label = sub_labels_map.get(key)

                # Do not work if the prperty label contains substring category or commons as they have no value for our table
                if filter_properties_by_label(label=property_label, property_uid=key):
                    entity_table_labels[ property_label ] = [ list_to_str(labels) ]
                    # modify to use the string form in the uri table
                    entity_table_URI[key] = [ list_to_str(values_list) ]
                
                else:
                    discarted_properties.append(key)

        # remove category and commons properties from uri table
        for key in discarted_properties:
            del entity_table_URI[key]

        return Entity_Table_DTO(labels_table = entity_table_labels, uri_table = entity_table_URI)

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while generating entity table. Error: ' + str(e))

### Functions
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

def get_labels_from_UIDs(uids : List, prefix : str = 'wd:'):
    try:
        global labels_map
        global labels_map_path
        global entity_prefix

        sub_labels_map = {}
        query_list = []
        # Obtain each requested label using the get label method
        sub_labels_map = {}
        for uid in uids:
            # check if it's a valid Wikidata UID, if not return uid
            if not re.match(r'^(Q|P)\d+$', uid):
                sub_labels_map[uid] = uid
            
            # Check if the label is in the list of elements with no label, if it does, return the URI
            elif uid in labels_map.get('no_label_elements'):
                sub_labels_map[uid] = entity_prefix + uid

            # Check if the label is already registered in the cache
            elif labels_map.get(uid) is not None:
                sub_labels_map[uid] = labels_map.get(uid)

            # Any other case we will add it to query list
            else:
                query_list.append(uid)
        
        if len(query_list) > 0:
            # now we will query for the query list elements labels in groups of n
            res = sparql_query_kg(sparql=labels_sparql, sparql_params={ 
                'uids' : ' '.join([prefix + x for x in query_list])
            })

            if res.get('code') != 200:
                print('Wikidata returned an error while obtaining the labels. Error: ' + res.get('text') + '\n' + res)
                raise HTTPException(status_code=502, detail='Wikidata returned an error while obtaining the labels. Error: ' + res.get('text'))

            for element in res.get('json').get('results').get('bindings'):
                uid = element.get('item').get('value').replace(entity_prefix,'')
                # if by any reason it return an empty label return uri and ban element as no label
                if len(element.get('itemLabel').get('value')) == 0: 
                    sub_labels_map[uid] = entity_prefix + uid
                    labels_map['no_label_elements'].append(uid)
                else:
                    sub_labels_map[uid] = element.get('itemLabel').get('value')
                    labels_map[uid] = element.get('itemLabel').get('value')

        # update the cache
        save_json(filename=labels_map_path, data=labels_map)
        return sub_labels_map
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error while obtaining labels. Error: ' + str(e))

def list_to_str(list : List):
    # join list elements using '; ' e.g. for [1,2,3] returns '1; 2; 3'
    return '; '.join([ x if x is not None else 'unknown value' for x in list])

def get_entity_data(entity_UID : str):
    # query wikidata to get an entity information
    try:
        res = query_api('get',(entity_prefix  + entity_UID), entity_query_headers, entity_query_params, entity_query_payload)

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

def get_value_by_type(data_type: str, value: dict, prefix:bool=True):
    try:
        global entity_prefix
        # how to get the value depending on the data type
        if value is not None:
            if data_type == 'wikibase-item':
                prefix = entity_prefix if prefix else ''
                return prefix + value.get('value').get('id')
            elif data_type == 'time':
                return value.get('value').get('time')[0:11]
            elif data_type == 'monolingualtext':
                return value.get('value').get('text')
            elif data_type == 'quantity':
                return (value.get('value').get('amount')) 
            elif data_type == 'globe-coordinate':
                return 'Latitud: ' + str(value.get('value').get('latitude')) + ' Longitud: ' + str(value.get('value').get('longitude')) + ' Altitud: ' + str(value.get('value').get('altitude')) + ' Presición: ' + str(value.get('value').get('precision')) + ' Planeta: ' + value.get('value').get('globe')
            elif data_type == 'wikibase-property':
                prefix = entity_prefix if prefix else ''
                return prefix + value.get('value').get('id')
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
