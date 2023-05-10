import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from utils.Request_utils import translate, link_graph_elements, get_question_tables, ask_tapas

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

      # Get question links to Wikidata KG

      res = link_graph_elements(question.text)
      if res.get('code') != 200:
         raise HTTPException(status_code=502, detail='Error retieving the query links from the linking service: ' + res.get('text')) 
      
      linked_elements = res.get('json')

      # Get the related tables
      res = get_question_tables(linked_elements)
      if res.get('code') != 200:
         raise HTTPException(status_code=502, detail='Error retieving the class tables from the template service.' + res.get('text')) 

      tables = res.get('json')

      # Ask TAPAS using each table
      answers = []
      for key,table in tables.items():
         res = ask_tapas(table=table, question=question.text)
         if res.get('code') != 200:
            raise HTTPException(status_code=502, detail='Error connecting with TAPAS service: ' + res.get('text')) 
         
         answers.append(res.get('json'))
      return answers
   except HTTPException as e:
      raise e
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error on main server while attending the query: ' + str(e))
