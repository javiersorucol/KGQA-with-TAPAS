# Before running this script make sure to run the tapas Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import unittest
from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file

import re

config = read_config_file('App_config.ini')

answer_service = dict(config.items('ANSWER_SERVICE'))
answer_service_url = 'http://' + answer_service.get('ip') + ':' + answer_service.get('port')

class Tapas_testing(unittest.TestCase):

    ask_tapas_endpoint = answer_service.get('ask_tapas_endpoint')
    ask_gpt_endpoint_v1 = answer_service.get('ask_gpt_endpoint_v1')
    ask_gpt_endpoint_v2 = answer_service.get('ask_gpt_endpoint_v2')

    # ask_tapas_endpoint unit tests
    # service  must return code 200 and correct dto with correct input and data
    def test_ask_tapas_endpoint_correct_input(self):

        # testing a correct case:
        res = query_api('post', answer_service_url + self.ask_tapas_endpoint, {}, {}, {
        "question": "Who is the president of Bolivia?",
        "table":{"label": ["Bolivia"], "contient": ["South America"], "President": ["Luis Arce"], "oficial language": ["Español; Quechua; Aymara; Guarani"]}
        })

        self.assertEqual(res.get('code'), 200 , self.ask_tapas_endpoint + ' endpoint is failing with a correct input.')

        # testing question text is in the expected answer
        self.assertIsNotNone(res.get('json').get('answer') , self.ask_tapas_endpoint + ' endpoint is failing with a correct input, answer key not found.')

    # service must return 422 whe receiving invalid payload
    def test_ask_tapas_endpoint_invalid_payload(self):

        # testing not valid object as payload
        res = query_api('post', answer_service_url + self.ask_tapas_endpoint, {}, {}, {
        "question": "Who is the MVP of Argentina?",
        })
        self.assertEqual(res.get('code'), 422 , self.ask_tapas_endpoint + ' endpoint is not returning error code 422 when receiving n incorrect payload.')

    # Answer must follow the expected format
    def test_ask_tapas_endpoint_answer_format(self):
        
        # singular answer case
        res = query_api('post', answer_service_url + self.ask_tapas_endpoint, {}, {}, {
        "question": "Who is the president of Bolivia?",
        "table":{"label": ["Bolivia"], "contient": ["South America"], "President": ["Luis Arce"], "oficial language": ["Español; Quechua; Aymara; Guarani"]}
        })

        singular_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?.+"
        result = re.search(singular_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_tapas_endpoint + ' endpoint is not returning the correct format with singular question.')

        # multiple answer case
        res = query_api('post', answer_service_url + self.ask_tapas_endpoint, {}, {}, {
        "question": "What are the oficial languages of Bolivia?",
        "table":{"label": ["Bolivia"], "contient": ["South America"], "President": ["Luis Arce"], "oficial language": ["Español; Quechua; Aymara; Guarani"]}
        })

        multiple_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?((\s)?\w+;(\s)?\w+(;)?)+"
        result = re.search(multiple_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_tapas_endpoint + ' endpoint is not returning the correct format with multiple question.')

        # aggregation case
        res = query_api('post', answer_service_url + self.ask_tapas_endpoint, {}, {}, {
        "question": "How many languages does Bolivia have?",
        "table":{"label": ["Bolivia"], "contient": ["South America"], "President": ["Luis Arce"], "oficial language": ["Español; Quechua; Aymara; Guarani"]}
        })

        aggregation_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?[\+-]?\d+"
        result = re.search(aggregation_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_tapas_endpoint + ' endpoint is not returning the correct format with aggregation question.')

        # Not found case
        res = query_api('post', answer_service_url + self.ask_tapas_endpoint, {}, {}, {
        "question": "How old is Angelina Jolie?",
        "table":{"label": ["Bolivia"], "continent": ["South America"], "President": ["Luis Arce"], "oficial language": ["Español; Quechua; Aymara; Guarani"]}
        })

        self.assertIn('Answer not found', res.get('json').get('answer'), self.ask_tapas_endpoint + ' endpoint is not returning the correct format with answer not found question.')

    # ask_gpt_endpoint_v1 unit tests
    # service  must return code 200 and correct dto with correct input and data
    def test_ask_gpt_endpoint_v1_correct_input(self):

        # testing a correct case:
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v1, {}, {}, {
        "question": "Who is the president of Bolivia?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        self.assertEqual(res.get('code'), 200 , self.ask_gpt_endpoint_v1 + ' endpoint is failing with a correct input.')

        # testing question text is in the expected answer
        self.assertIsNotNone(res.get('json').get('answer') , self.ask_gpt_endpoint_v1 + ' endpoint is failing with a correct input, answer key not found.')

    # service must return 422 whe receiving invalid payload
    def test_ask_gpt_endpoint_v1_invalid_payload(self):

        # testing not valid object as payload
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v1, {}, {}, {
        "question": "Who is the MVP of Argentina?",
        })
        self.assertEqual(res.get('code'), 422 , self.ask_gpt_endpoint_v1 + ' endpoint is not returning error code 422 when receiving n incorrect payload.')

    # Answer must follow the expected format
    def test_ask_gpt_endpoint_v1_answer_format(self):
        
        # singular answer case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v1, {}, {}, {
        "question": "Who is the president of Bolivia?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        singular_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?.+"
        result = re.search(singular_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_gpt_endpoint_v1 + ' endpoint is not returning the correct format with singular question.')

        # multiple answer case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v1, {}, {}, {
        "question": "What are the oficial languages of Bolivia?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        multiple_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?((\s)?\w+;(\s)?\w+(;)?)+"
        result = re.search(multiple_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_gpt_endpoint_v1 + ' endpoint is not returning the correct format with multiple question.')

        # aggregation case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v1, {}, {}, {
        "question": "How many languages does Bolivia have?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        aggregation_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?[\+-]?\d+"
        result = re.search(aggregation_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_gpt_endpoint_v1 + ' endpoint is not returning the correct format with aggregation question.')

        # Boolean case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v1, {}, {}, {
        "question": "Is Bolivia in South America?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        boolean_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?(yes|no)"

        result = re.search(boolean_pattern, res.get('json').get('answer'), re.IGNORECASE)

        self.assertTrue(result, self.ask_gpt_endpoint_v1 + ' endpoint is not returning the correct format with boolean question.')

        # not found case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v1, {}, {}, {
        "question": "How old is Angelina Jolie?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        self.assertIn('Answer not found', res.get('json').get('answer'), self.ask_gpt_endpoint_v1 + ' endpoint is not returning the correct format with answer not found question.')

    
    # ask_gpt_endpoint_v2 unit tests
    # service  must return code 200 and correct dto with correct input and data
    def test_ask_gpt_endpoint_v2_correct_input(self):

        # testing a correct case:
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v2, {}, {}, {
        "question": "Who is the president of Bolivia?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        self.assertEqual(res.get('code'), 200 , self.ask_gpt_endpoint_v2 + ' endpoint is failing with a correct input.')

        # testing question text is in the expected answer
        self.assertIsNotNone(res.get('json').get('answer') , self.ask_gpt_endpoint_v2 + ' endpoint is failing with a correct input, answer key not found.')

    # service must return 422 whe receiving invalid payload
    def test_ask_gpt_endpoint_v2_invalid_payload(self):

        # testing not valid object as payload
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v2, {}, {}, {
        "question": "Who is the MVP of Argentina?",
        })
        self.assertEqual(res.get('code'), 422 , self.ask_gpt_endpoint_v2 + ' endpoint is not returning error code 422 when receiving n incorrect payload.')

    # Answer must follow the expected format
    def test_ask_gpt_endpoint_v2_answer_format(self):
        
        # singular answer case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v2, {}, {}, {
        "question": "Who is the president of Bolivia?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        singular_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?.+"
        result = re.search(singular_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_gpt_endpoint_v2 + ' endpoint is not returning the correct format with singular question.')

        # multiple answer case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v2, {}, {}, {
        "question": "What are the oficial languages of Bolivia?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        multiple_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?((\s)?\w+;(\s)?\w+(;)?)+"
        result = re.search(multiple_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_gpt_endpoint_v2 + ' endpoint is not returning the correct format with multiple question.')

        # aggregation case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v2, {}, {}, {
        "question": "How many languages does Bolivia have?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        aggregation_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?[\+-]?\d+"
        result = re.search(aggregation_pattern, res.get('json').get('answer'))

        self.assertTrue(result, self.ask_gpt_endpoint_v2 + ' endpoint is not returning the correct format with aggregation question.')

        # Boolean case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v2, {}, {}, {
        "question": "Is Bolivia in South America?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        boolean_pattern = "The\sanswer\sto\syour\squestion\sis:(\s)?(yes|no)"

        result = re.search(boolean_pattern, res.get('json').get('answer'), re.IGNORECASE)

        self.assertTrue(result, self.ask_gpt_endpoint_v2 + ' endpoint is not returning the correct format with boolean question.')

        # not found case
        res = query_api('post', answer_service_url + self.ask_gpt_endpoint_v2, {}, {}, {
        "question": "How old is Angelina Jolie?",
        "triples": "urn:Boliva urn:Continent \"South America\" \n urn:Bolivia urn:president \"Luis Arce\" \n urn:Bolivia urn:oficial_languages \"Español; Quechua; Aymara; Guarani\""
        })

        self.assertIn('Answer not found', res.get('json').get('answer'), self.ask_gpt_endpoint_v2 + ' endpoint is not returning the correct format with answer not found question.')


if __name__ == '__main__':
    unittest.main()