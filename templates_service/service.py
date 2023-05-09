import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException, Query

from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json
from utils.Request_utils import translate, link_graph_elements, get_entity_classes, generate_class_template, fill_templates

from DTOs.templates_DTOs import QALD_json_DTO
from DTOs.linking_DTOs import Linked_data_DTO
from DTOs.graph_query_DTOs import Table_templates_DTO, Table_template_DTO, Table_template_property_DTO

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

# read the service configuration
config = read_config_file('App_config.ini')

templates_service = dict(config.items('TEMPLATES_SERVICE'))

def update_index(index:dict, elements:list, class_UID:str):
    # Function use to update a given index with a new value (class_UID)
    for element in elements:
        element_index_val = index.get(element)
        if element_index_val is None:
            # if element is not registered in index
            index[element] = [class_UID]
        elif class_UID not in element_index_val:
            # if element is in index, but classUID is not saved
            element_index_val.append(class_UID)

# Function to update the template list from a dataset in QALD format
def update_with_data_set(dataset:dict, templates:dict, class_parents_search_index:dict, properties_search_index:dict, lang:str='en'):
    
    reviewed_entities = []
    total = len(dataset.get('questions'))
    print('Dataset size: ' + str(total))
    now = 0
    for question in dataset.get('questions'): 
        now = now + 1
        print('Progress: ', str(now), '/', str(total), ', ', str(now/total*100), '%', 'question id: ', question.get('id'))
        
        # Retreive question string
        en_question = ''
        # if the question is not available in the selected language, then continue with the next question
        try:
            question = next(filter((lambda x: x.get('language') == lang), question.get('question'))).get('string')
        except:
            continue

        # translate the question if necessary
        if lang != 'en' :
            res = translate(question, lang)
            if res.get('code') != 200:
                print('Error getting a transltion for question: ', res)
                continue

            en_question = res.get('json').get('text')
        else:
            en_question = question
        
        # get question's entity links
        res = link_graph_elements(en_question)
        if res.get('code') != 200:
            print('Error linking elements for question: ', res)
            continue
        question_UIDs = res.get('json')

        # for every entity in the question
        for entity in question_UIDs.get('entities'):
            entity_UID = entity.get('UID')
            
            # check if entity was already reviewed
            if entity_UID in reviewed_entities:
                continue

            # get the entity classes
            res = get_entity_classes(entity_UID)
            if res.get('code') != 200:
                print('Error getting a entity classes for question: ', res)
                continue

            entity_classes = res.get('json')

            # for every class
            for class_UID in entity_classes:
                # check if it's not banned
                if class_UID in banned_classes:
                    continue

                # Initialize the template if not existent
                if templates.get(class_UID) is None:
                    res = generate_class_template(class_UID)
                    if res.get('code') != 200:
                        print('Error generating classs template for question: ', res)
                        continue

                    new_template = res.get('json')

                    #upate indexes
                    update_index(class_parents_search_index, new_template.pop('subclasses'), class_UID)
                    update_index(properties_search_index, new_template.get('properties').keys(), class_UID)

                    templates[class_UID] = new_template
                else:
                    templates[class_UID]['frequency'] = templates[class_UID]['frequency'] + 1
            # add entity to the review list
            reviewed_entities.append(entity_UID)
    
    templates = dict(filter((lambda x: len(x[1].get('properties')) > 0), templates.items()))

    save_json(templates_data_path, templates)
    save_json(class_parents_search_index_data_path, class_parents_search_index)
    save_json(properties_search_index_data_path, properties_search_index)

def initialize_templates(templates, class_parents_search_index, properties_search_index):
    training_set = read_json(training_data_path)
    update_with_data_set(training_set, templates, class_parents_search_index, properties_search_index)

# Load the templates, if the file does not exists, create and update with the defult training file

if not os.path.exists(templates_data_path):
    print('Templates file not found, creating the templates file and filling it with training data.')
    templates = {}
    class_parents_search_index = {}
    properties_search_index = {}
    initialize_templates(templates, class_parents_search_index, properties_search_index)

templates = read_json(templates_data_path)
class_parents_search_index = read_json(class_parents_search_index_data_path)
properties_search_index = read_json(properties_search_index_data_path)

print('Data loaded!, ', len(templates.keys()), ' templates found.')


app = FastAPI()

@app.post(templates_service.get('question_templates_endpoint'))
def get_question_tables(linked_data : Linked_data_DTO):
    try:
        classes = get_linked_elements_classes(linked_data.__dict__)
        question_templates ={}

        for q_class in classes:
            # get the class template
            template = templates.get(q_class)
            if template is None:
                # if no template is found, search for a parent class
                parents = class_parents_search_index.get(q_class)
                if parents is not None:
                    # if we found partent classes add it to the question templates
                    for parent in parents:
                        if templates.get(parent) is not None:
                            question_templates[parent] = templates.get(parent)
                            templates[parent]['frequency'] = templates.get(parent).get('frequency') + 1
            else:
                question_templates[q_class] = template
                templates[q_class]['frequency'] = templates.get(q_class).get('frequency') + 1

        # Case we didn't find any template for the question
        if len(question_templates) == 0:
            # try to get templates by using relations
            for property in linked_data.relations:
                alternative_classes = properties_search_index.get(property.get('UID'))
                if alternative_classes is not None:
                    for alt_class in alternative_classes:
                        question_templates[alt_class] = templates.get(alt_class)
                        templates[alt_class]['frequency'] = templates.get(alt_class).get('frequency') + 1

        # check if we have too many templates
        if len(question_templates) > max_templates_per_question:
            question_templates = top_templates(question_templates)
        
        save_json(templates_data_path, templates)

        print('templates returned: ', str(question_templates.keys()))

        return get_tables_by_template(question_templates, linked_data.entities)

    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown Error getting the templates for the given entities: ' + str(e))


@app.put(templates_service.get('templates_update_endpoint'))
def update_with_remote_QALD_json(dataset : QALD_json_DTO, lang : str = Query(
        default='en', min_length=2, max_length=5, regex="^(es|en)$"
    )):
    try:

        # transform all the DTOs into dict
        dataset = dataset.__dict__
        dataset['questions'] = [{ 'id' : x.id, 'question' : [y.__dict__ for y in x.question] } for x in dataset.get('questions')]
    
        global templates
        global class_parents_search_index
        global properties_search_index
        
        update_with_data_set(dataset, templates, class_parents_search_index, properties_search_index, lang)

        templates = read_json(templates_data_path)
        class_parents_search_index = read_json(class_parents_search_index_data_path)
        properties_search_index = read_json(properties_search_index_data_path)  
        return { 'msg' : 'Success!' }
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown Error updating the templates: ' + str(e))


# extra functions

def get_tables_by_template(templates, entities):
    try:
        # transform to the expected DTO
        graph_templates = { 'templates': [], 'entities_UIDs' : [x.get('UID') for x in entities]}

        for template_UID, template in templates.items():
            graph_template = { 'UID' : template_UID, 'properties':[]}
            for property_UID, property in template.get('properties').items():
                graph_template['properties'].append({'UID' : property_UID, 'label' : property.get('label'), 'type' : property.get('type')})

            graph_templates['templates'].append(graph_template)
        
        # fill the templates
        res = fill_templates(graph_templates)
        if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error filling the templates: ' + res.get('text'))
        
        return res.get('json')
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail='Error while filling the templates: ' + str(e))

def top_templates(question_templates: dict):
    freq_rank= sorted(question_templates.items(), key=(lambda x: x[1].get('frequency')), reverse=True)[0:max_templates_per_question]
    return dict(freq_rank)
    

def get_linked_elements_classes(linked_data: dict):

    classes = []
        
    for entity in  linked_data.get('entities'):
        res = get_entity_classes(entity.get('UID'))
        if res.get('code') != 200:
            continue
        classes = classes + res.get('json')

    return list(set(classes))



