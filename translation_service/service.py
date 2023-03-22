import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from fastapi import FastAPI, HTTPException
from transformers import pipeline

from utils.Configuration_utils import read_config_file

from DTOs.translation_DTOs import Question_DTO

# Reading the config file
config_file_path = 'translation_service/Config/Config.ini'
config = read_config_file(config_file_path)

# saving config vars
translations_modes = dict(config.items('TRANSLATION-MODES'))

translators = {}
for key, value in translations_modes.items():
    translators[key] = pipeline('translation', model=value)


app = FastAPI()

# End Points

@app.post('/translate/')
def translate(question :  Question_DTO):
    try:
        #If translation mode does not exist, return error
        if translators.get(question.mode) is None:
            raise HTTPException(status_code=400, detail='Translation mode not supported. The supported translation modes are: ' + str(translations_modes.keys()))

        # translation process
        question.text = translators.get(question.mode)(question.text)[0].get('translation_text')
        return question
        
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unexpected error on server: ' + str(e))