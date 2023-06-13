# Before running this script make sure to run the linking Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import unittest
from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file

config = read_config_file('App_config.ini')

templates_service = dict(config.items('TEMPLATES_SERVICE'))
templates_url = 'http://' + templates_service.get('ip') + ':' + templates_service.get('port')

class Templatess_testing(unittest.TestCase):
    question_templates_endpoint = templates_service.get('question_templates_endpoint')
    templates_update_endpoint = templates_service.get('templates_update_endpoint')

    # question_templates_endpoint
    def test_question_endpoint_correct_case(self):
        res = query_api('post', templates_url + self.question_templates_endpoint, {}, {}, {
        'entities': [
            {'UID':'Q750'}
        ],
        'relations': [
            ]
        })

        self.assertEqual(res.get('code'), 200 , self.question_templates_endpoint + ' endpoint is failing with a correct input.')

        # check country class is returned
        self.assertIsNotNone(res.get('json').get('Q6256'), self.question_templates_endpoint + ' endpoint is failing with a correct input, country template not found.')

        # check properties
        self.assertIsNotNone(res.get('json').get('Q6256').get('P6') , self.question_templates_endpoint + ' endpoint is failing with a correct input, property P6 not found')

    def test_question_endpoint_multiple_entities_case(self):
        res = query_api('post', templates_url + self.question_templates_endpoint, {}, {}, {
        'entities': [
            {'UID':'Q750'}, {'UID':'Q42410'}, {'UID':'Q414'}
        ],
        'relations': [
            ]
        })
        
        self.assertEqual(res.get('code'), 200 , self.question_templates_endpoint + ' endpoint is failing with a multiple entities input.')
        # check if the most important table templates are returned
        self.assertIsNotNone(res.get('json').get('Q6256'), self.question_templates_endpoint + ' endpoint is failing with a correct multiple entity input, country template not found.')
        self.assertIsNotNone(res.get('json').get('Q5'), self.question_templates_endpoint + ' endpoint is failing with a correct multiple entity input, human template not found.')

    def test_question_endpoint_no_entities_case(self):
        res = query_api('post', templates_url + self.question_templates_endpoint, {}, {}, {
        'entities': [
        ],

        'relations': [{'UID':'P19'}
            ]
        })
        self.assertEqual(res.get('code'), 200 , self.question_templates_endpoint + ' endpoint is failing to obtain templates by searching alternative classes using given properties.')
        self.assertNotEqual(0, len(res.get('json').keys()), self.question_templates_endpoint + ' endpoint returns no templates when searching alternative classes using found properties.')

    def test_question_endpoint_top_templates(self):
        res = query_api('post', templates_url + self.question_templates_endpoint, {}, {}, {
        'entities': [
            {'UID':'Q750'}, {'UID':'Q42410'}, {'UID':'Q60'}, {'UID':'Q79784'}, {'UID':'Q49740'}
        ],
        'relations': [
            ]
        })
        self.assertEqual(res.get('code'), 200 , self.question_templates_endpoint + ' endpoint is failing to obtain templates for cases that result in more than 10 templates.')
        self.assertLessEqual(10, len(res.get('json').keys()), self.question_templates_endpoint + ' endpoint allows more templates are returned than the max number allowed.')

    def test_question_endpoint_incorrect_input(self):
        # incorrect case
        res = query_api('post', templates_url + self.question_templates_endpoint, {}, {}, {})
        
        self.assertEqual(res.get('code'), 422 , self.question_templates_endpoint + ' endpoint allows incorrect input.')

    # templates endpoint
    def test_templates_update_endpoint_incorrect_input(self):
        # incorrect case
        res = query_api('put', templates_url + self.templates_update_endpoint, {}, {'lang':'en'}, {})
        
        self.assertEqual(res.get('code'), 422 , self.templates_update_endpoint + ' endpoint allows incorrect input.')

    def test_templates_update_endpoint_incorrect_input(self):
        # correct case
        res = query_api('put', templates_url + self.templates_update_endpoint, {}, {'lang':'en'}, {
            'questions': [
                {
                'id': '1',
                'question': [
                    {
                    'language': 'en',
                    'string': 'How tall is Michael B. Joran?'
                    }
                ],
                'query': {},
                'answers': []
                }
            ]
            })
        
        self.assertEqual(res.get('code'), 200, self.templates_update_endpoint + ' endpoint is failing with correct input.')

if __name__ == '__main__':
    unittest.main()

    
