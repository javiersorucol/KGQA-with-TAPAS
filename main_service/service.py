import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from pathlib import Path

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from utils.Request_utils import translate, link_graph_elements , ask_tapas, get_entity_table, get_entity_triples, ask_gpt_v1, ask_gpt_v2

from DTOs.main_DTOs import QUERY_DTO, FINAL_ANSWER_DTO

config_file_path = 'main_service/Config/Config.ini'
app_config_file_path = 'App_config.ini'

# check if required config files exist
if not Path(config_file_path).is_file() or not Path(app_config_file_path).is_file:
    print('Config file was not found for the main service.')
    exit()

# Reading the config file
config = read_config_file(config_file_path)

supported_languges = config.get('LANGUAGES', 'supported_languges').split()

# Reding the app configurations to get the service configuration
app_config = read_config_file(app_config_file_path)
main_service = dict(app_config.items('MAIN_SERVICE'))

app = FastAPI()

@app.post(main_service.get('gpt_endpoint'))
def ask_Wikidata_with_gpt(question: QUERY_DTO):
   try:
      # Process the question to obtain linked elements (tranlation and linking service are involved)
      linked_elements = preprocess_question(question)
      print('LINKED ELEMENTS: ', linked_elements)

      # Get related entity triples
      entity_triples = {}
      for entity in linked_elements.get('entities'):
         res = get_entity_triples(entity.get('UID'))

         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error retieving the entity triples from the graph query service.' + str(res.get('text'))) 

         entity_triples[entity.get('UID')] = res.get('json')
      
      print("ENTITY TRIPLES: ", entity_triples.keys())

      # Ask GPT using each entity recieved triple
      answers = {}
      for key,triples in entity_triples.items():
         print('entity: ', key)

         res = ask_gpt_v1(triples=triples.get('triples'), question=question.text)

         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error connecting with Answer service: ' + res.get('text')) 
         
         print('answer: ', res.get('json').get('answer'))
         answers = res.get('json').get('answer')
         break
      
      return FINAL_ANSWER_DTO(answer=answers, linked_elements=linked_elements)

   except HTTPException as e:
      raise e
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error on main server while attending the query: ' + str(e))
   

@app.post(main_service.get('tapas_endpoint'))
def ask_Wikidata_with_TAPAS(question: QUERY_DTO):
   try:
      # Process the question to obtain linked elements (tranlation and linking service are involved)
      linked_elements = preprocess_question(question)
      print('LINKED ELEMENTS: ', linked_elements)

      # Get the related entity tables
      entity_tables = {}
      for entity in linked_elements.get('entities'):
         res = get_entity_table(entity.get('UID'))
         
         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error retieving the entity tables from the graph query service.' + str(res.get('text'))) 

         entity_tables[entity.get('UID')] = res.get('json')

      print("ENTITY TABLES: ", entity_tables.keys())

      # Ask TAPAS using each table
      answers = {}
      for key,tables in entity_tables.items():
         print('table: ', key)
         res = ask_tapas(table=tables.get('labels_table'), question=question.text)
         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error connecting with Answer service: ' + res.get('text')) 
         
         print('answer: ', res.get('json').get('answer'))
         answers = res.get('json').get('answer')
         break
      
      return FINAL_ANSWER_DTO(answer=answers, linked_elements=linked_elements)
   
   except HTTPException as e:
      raise e
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error on main server while attending the query: ' + str(e))

# Functions

def preprocess_question(question: QUERY_DTO):
   # Process the question to obtain the linked elements

   # Check if the langugeis supported
   if question.lang not in supported_languges:
      raise HTTPException(status_code=400, detail='Languge not supported. The supported languges are: ' + str(supported_languges))

   # If the language is not english, query the translation service 
   if question.lang != 'en':
      res = translate(query=question.text,lang=question.lang)

      if res.get('code') != 200:
         raise HTTPException(status_code=502, detail='Error with while translating the query. ' + res.get('text'))          

      question.text = res.get('json').get('text')

   print('QUESTION: ', question.text)
   
   # Get question links to Wikidata KG
   res = link_graph_elements(question.text)
   if res.get('code') != 200:
      raise HTTPException(status_code=502, detail='Error retieving the query links from the linking service: ' + res.get('text')) 
   
   linked_elements = res.get('json')

   return linked_elements
