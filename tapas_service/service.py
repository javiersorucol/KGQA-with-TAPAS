import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

from DTOs.tapas_DTOs import Table_DTO

import pandas as pd
from transformers import pipeline

# Reading the config file
config_file_path = 'tapas_service/Config/Config.ini'
config = read_config_file(config_file_path)

# Read service configuration
config = read_config_file('App_config.ini')

tapas_service = dict(config.items('TAPAS_SERVICE'))


# initializting tapas
tqa = pipeline(task="table-question-answering", model="google/tapas-base-finetuned-wtq")

app = FastAPI()

@app.post(tapas_service.get('ask_endpoint'))
def ask(table_DTO: Table_DTO):
   table = pd.DataFrame(table_DTO.table)
   table = table.astype(str)

   answer= tqa(table=table, query=table_DTO.question)
   
   return {'answer' : answer.get('answer')}
