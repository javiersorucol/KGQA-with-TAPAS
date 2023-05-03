import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file


# Reading the config file
config_file_path = 'tapas_service/Config/Config.ini'
config = read_config_file(config_file_path)

app = FastAPI()

@app.get('/example/')
def example():
   return 'success'
