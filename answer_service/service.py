import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file
from utils.OpenAI_utils import query_open_ai

from DTOs.answer_DTOs import Table_DTO, Triples_DTO

import pandas as pd
from transformers import pipeline
from string import Template
import re
from statistics import mean 

# Reading the config file
config_file_path = 'answer_service/Config/Config.ini'
config = read_config_file(config_file_path)

# read the config vars
gpt_aggregation_prompt = config['GPT_METHOD']['gpt_aggregation_prompt'].replace(r'\n', '\n')
manual_aggregation_prompt = config['GPT_METHOD']['manual_aggregation_prompt'].replace(r'\n', '\n')

# Read service configuration
config = read_config_file('App_config.ini')

answer_service = dict(config.items('ANSWER_SERVICE'))


# initializting tapas
tqa = pipeline(task="table-question-answering", model="google/tapas-base-finetuned-wtq")

app = FastAPI()

@app.post(answer_service.get('ask_tapas_endpoint'))
def ask_tapas(table_DTO : Table_DTO):
   try:
      table = pd.DataFrame(table_DTO.table)
      table = table.astype(str)

      answer= tqa(table=table, query=table_DTO.question)
      answer = answer.get('answer')
      print(answer)
      print('------------------------------------------------------')

      if 'COUNT >' in answer:
         res = re.findall(r'COUNT >.*', answer)
         if len(res) > 0:
            answer = str(len(res[0].replace('COUNT >','').split(';')))
      elif 'SUM >' in answer:
         res = re.findall(r'SUM >.*', answer)
         if len(res) > 0:
            try:
               answer = str(sum([ int(x) for x in (res[0].replace('SUM >','').split(';')) ]))
            except:
               return 'The answer of your question is: ' + answer
      elif 'AVG >' in answer:
         res = re.findall(r'AVG >.*', answer)
         if len(res) > 0:
            try:
               answer = str(mean([ int(x) for x in (res[0].replace('AVG >','').split(';')) ]))
            except:
               return 'The answer of your question is: ' + answer     

      return 'The answer of your question is: ' + answer
   
   except HTTPException as e:
      raise e
   
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error while using TAPAS to answer the question. Error: ' + str(e))

@app.post(answer_service.get('ask_gpt_endpoint_v1'))
def ask_gpt_v1(triples_DTO : Triples_DTO):
   try:
      global gpt_aggregation_prompt
      answer = query_open_ai(prompt_template=gpt_aggregation_prompt, prompt_params={ 'triples' : triples_DTO.triples, 'question':triples_DTO.question }, max_tokens=100)

      print('Answer: ', answer)

      return answer

   except HTTPException as e:
      raise e
   
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error while using GPT to answer the question. Error: ' + str(e))

@app.post(answer_service.get('ask_gpt_endpoint_v2'))
def ask_gpt_v2(triples_DTO : Triples_DTO):
   try:
      global manual_aggregation_prompt
      answer = query_open_ai(prompt_template=manual_aggregation_prompt, prompt_params={ 'triples' : triples_DTO.triples, 'question':triples_DTO.question }, max_tokens=100)

      print('Answer: ', answer)
      print('------------------------------------------------------')
      if 'COUNT >' in answer:
         res = re.findall(r'COUNT >.*', answer)
         if len(res) > 0:
            answer = 'The answer of your question is: ' + str(len(res[0].replace('COUNT >','').split(';')))
      elif 'SUM >' in answer:
         res = re.findall(r'SUM >.*', answer)
         if len(res) > 0:
            try:
               answer = 'The answer of your question is: ' + str(sum([ int(x) for x in (res[0].replace('SUM >','').split(';')) ]))
            except:
               return answer
      elif 'AVG >' in answer:
         res = re.findall(r'AVG >.*', answer)
         if len(res) > 0:
            try:
               answer = 'The answer of your question is: ' + str(mean([ int(x) for x in (res[0].replace('AVG >','').split(';')) ]))
            except:
               return answer      

      return answer

   except HTTPException as e:
      raise e
   
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error while using GPT to answer the question. Error: ' + str(e))