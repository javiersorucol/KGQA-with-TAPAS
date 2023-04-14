import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json
from utils.Request_utils import translate, link_graph_elements, get_entity_classes

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

app = FastAPI()

@app.post('/test/')
def test():
    return get_entity_classes('Q750')

