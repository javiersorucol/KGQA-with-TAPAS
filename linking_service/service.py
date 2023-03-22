import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException

from utils.Configuration_utils import read_config_file

# Reading the config file
config_file_path = 'linking_service/Config/Config.ini'
config = read_config_file(config_file_path)

# saving config vars
headers = dict(config.items('FALCON-API-HEADERS'))
external_api = dict(config.items('FALCON-API'))
params = dict(config.items('FALCON-API-PARAMS'))

kg_prefix = config['KG_DATA']['prefix']

app = FastAPI()

@app.post('/test/')
def test():
    return 'success'