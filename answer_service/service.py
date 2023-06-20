import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from DTOs.answer_DTOs import Table_DTO

import pandas as pd
from transformers import pipeline

# Reading the config file
config_file_path = 'answer_service/Config/Config.ini'
config = read_config_file(config_file_path)

# Read service configuration
config = read_config_file('App_config.ini')

answer_service = dict(config.items('ANSWER_SERVICE'))


# initializting tapas
tqa = pipeline(task="table-question-answering", model="google/tapas-base-finetuned-wtq")

app = FastAPI()

@app.post(answer_service.get('ask_tapas_endpoint'))
def ask_tapas(table_DTO: Table_DTO):
   table = pd.DataFrame(table_DTO.table)
   table = table.astype(str)

   answer= tqa(table=table, query=table_DTO.question)
   
   return {'answer' : answer.get('answer')}
