import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from utils.Request_utils import translate, link_graph_elements , ask_tapas, get_entity_table

from DTOs.main_DTOs import QUERY_DTO

# Reading the config file
config_file_path = 'main_service/Config/Config.ini'
config = read_config_file(config_file_path)

supported_languges = config.get('LANGUAGES', 'supported_languges').split()

app = FastAPI()

@app.post('/question/')
def example(question: QUERY_DTO):
   try:
      # Check if the langugeis supported
      if question.lang not in supported_languges:
         raise HTTPException(status_code=400, detail='Languge not supported. The supported languges are: ' + str(supported_languges))
      
      # If the language is not english, query the translation service 
      if question.lang != 'en':
         res = translate(query=question.text,lang=question.lang)

         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error with while translting the query: ' + res.get('text'))          

         question.text = res.get('json').get('text')

      print('QUESTION: ', question.text)
      
      # Get question links to Wikidata KG

      res = link_graph_elements(question.text)
      if res.get('code') != 200:
         raise HTTPException(status_code=502, detail='Error retieving the query links from the linking service: ' + res.get('text')) 
      
      linked_elements = res.get('json')

      print('LINKED ELEMENTS: ', linked_elements)

      # Get the related entity tables
      entity_tables = {}
      for entity in linked_elements.get('entities'):
         res = get_entity_table(entity.get('UID'))
         
         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error retieving the entity tables from the template service.' + str(res.get('text'))) 

         entity_tables[entity.get('UID')] = res.get('json')

      print("ENTITY TABLES: ", entity_tables.keys())

      # Ask TAPAS using each table
      answers = {}
      for key,tables in entity_tables.items():
         print('table: ', key)
         res = ask_tapas(table=tables.get('labels_table'), question=question.text)
         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error connecting with Answer service: ' + res.get('text')) 
         
         print('answer: ', res.get('json'))
         answers[key] = res.get('json')
      return answers
   except HTTPException as e:
      raise e
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error on main server while attending the query: ' + str(e))
