import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file
from utils.OpenAI_utils import query_open_ai

from DTOs.answer_DTOs import Table_DTO, Triples_DTO

import pandas as pd
from transformers import pipeline
from string import Template

# Reading the config file
config_file_path = 'answer_service/Config/Config.ini'
config = read_config_file(config_file_path)

# read the config vars
prompt_template = config['GPT_METHOD']['prompt']

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
      
      return {'answer' : answer.get('answer')}
   
   except HTTPException as e:
      raise e
   
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error while using TAPAS to answer the question. Error: ' + str(e))

@app.post(answer_service.get('ask_gpt_endpoint'))
def ask_gpt(triples_DTO : Triples_DTO):
   try:
      global prompt_template
      answer = query_open_ai(prompt_template=prompt_template, prompt_params={ 'triples' : triples_DTO.triples, 'question':triples_DTO.question }, max_tokens=100)

      print('Answer: ', answer)

      return answer

   except HTTPException as e:
      raise e
   
   except Exception as e:
      raise HTTPException(status_code=500, detail='Unexpected error while using TAPAS to answer the question. Error: ' + str(e))
