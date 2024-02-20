import openai
from dotenv import load_dotenv

from string import Template
from pathlib import Path
import os

open_ai_key_file_path = '.env'

# Check open ai key file is present

if not Path(open_ai_key_file_path).is_file():
    print('.env file with OPENAI key was not found. Please add it to the root folder')
    exit()

# Read and save OPENAI key

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def query_open_ai(prompt_template : str, prompt_params: dict, max_tokens : int=100):
    try:
        client = openai.OpenAI()
        prompt = Template(prompt_template).substitute(prompt_params)
        model = 'gpt-4-1106-preview'
        completion = client.chat.completions.create(
            model=model,
            messages=[{'role' : 'user', 'content' : prompt}],
            temperature = 0,
            max_tokens=max_tokens,
        )

        answer = completion.choices[0].message.content
        return answer

    except Exception as e:
        print('Error while querying openai: ', str(e))
        raise Exception('OpenAI API error: ' + str(e))

def query_open_ai_gpt_3(prompt_template : str, prompt_params: dict, max_tokens : int=100):
    try:
        prompt = Template(prompt_template).substitute(prompt_params)
        gpt_model = 'text-davinci-003'
        response = openai.Completion.create(
            engine = gpt_model,
            prompt = prompt,
            max_tokens = max_tokens,
            n = 1,
            stop = None,
            temperature = 0
        )
        answer = response.get('choices')[0].get('text')
        return answer
    
    except Exception as e:
        print('Error while querying openai: ', str(e))
        raise Exception('OpenAI API error: ' + str(e))
