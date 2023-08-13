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

linking_service = dict(config.items('LINKING_SERVICE'))
linking_url = 'http://' + linking_service.get('ip') + ':' + linking_service.get('port')

class Linking_testing(unittest.TestCase):

    link_main_endpoint = linking_service.get('link_main_endpoint')
    link_endpoint_gpt_v1 = linking_service.get('link_endpoint_gpt_v1')
    link_endpoint_gpt_v2 = linking_service.get('link_endpoint_gpt_v2')
    link_endpoint_falcon = linking_service.get('link_endpoint_falcon')
    link_endpoint_opentapioca = linking_service.get('link_endpoint_opentapioca')

    # link_main_endpoint unit tests
    def test_link_main_endpoint_correct_input(self):
        # testing a correct case:
        res = query_api('post', linking_url + self.link_main_endpoint, {}, {}, {
            'text': 'Who is the president of Bolivia?'
        })

        self.assertEqual(res.get('code'), 200 , self.link_main_endpoint + ' endpoint is failing with a correct input.')

        # testing if the result contains entity list
        self.assertIsNotNone(res.get('json').get('entities') , self.link_main_endpoint + ' endpoint is failing with a correct input, entities key not found.')

        # testing if entity contains UID and label
        self.assertIsNotNone(res.get('json').get('entities')[0].get('UID') , self.link_main_endpoint + ' endpoint is failing with a correct input, resulting entity does not have UID.')
        self.assertIsNotNone(res.get('json').get('entities')[0].get('label') , self.link_main_endpoint + ' endpoint is failing with a correct input, resulting entity does not have label.')
        
    def test_link_main_endpoint_incorrect_input(self):
        # incorrect case
        res = query_api('post', linking_url + self.link_main_endpoint, {}, {}, {})
        
        self.assertEqual(res.get('code'), 422 , self.link_main_endpoint + ' endpoint allows incorrect input.')
    
    def test_link_main_endpoint_only_main_entity(self):
        res = query_api('post', linking_url + self.link_main_endpoint, {}, {}, {
            'text': 'Is Christian Bale starring in Batman Begins?'
        })

        # Test to check that the endpoint only returns at most one entity (main entity)
        self.assertLessEqual(len(res.get('json').get('entities')), 1, self.link_main_endpoint + ' endpoint return more than one entity: ' + str(len(res.get('json').get('entities'))))

    
    # link_endpoint_gpt_v1 unit tests
    def test_link_endpoint_gpt_v1_correct_input(self):
        # testing a correct case:
        res = query_api('post', linking_url + self.link_endpoint_gpt_v1, {}, {}, {
            'text': 'Who is the president of Bolivia?'
        })

        self.assertEqual(res.get('code'), 200 , self.link_endpoint_gpt_v1 + ' endpoint is failing with a correct input.')

        # testing if the result contains entity list
        self.assertIsNotNone(res.get('json').get('entities') , self.link_endpoint_gpt_v1 + ' endpoint is failing with a correct input, entities key not found.')

        # testing if entity contains UID and label
        self.assertIsNotNone(res.get('json').get('entities')[0].get('UID') , self.link_endpoint_gpt_v1 + ' endpoint is failing with a correct input, resulting entity does not have UID.')
        self.assertIsNotNone(res.get('json').get('entities')[0].get('label') , self.link_endpoint_gpt_v1 + ' endpoint is failing with a correct input, resulting entity does not have label.')
        
    def test_link_endpoint_gpt_v1_incorrect_input(self):
        # incorrect case
        res = query_api('post', linking_url + self.link_endpoint_gpt_v1, {}, {}, {})
        
        self.assertEqual(res.get('code'), 422 , self.link_endpoint_gpt_v1 + ' endpoint allows incorrect input.')
    
    # link_endpoint_gpt_v2 unit tests
    def test_link_endpoint_gpt_v2_correct_input(self):
        # testing a correct case:
        res = query_api('post', linking_url + self.link_endpoint_gpt_v2, {}, {}, {
            'text': 'Who is the president of Bolivia?'
        })

        self.assertEqual(res.get('code'), 200 , self.link_endpoint_gpt_v2 + ' endpoint is failing with a correct input.')

        # testing if the result contains entity list
        self.assertIsNotNone(res.get('json').get('entities') , self.link_endpoint_gpt_v2 + ' endpoint is failing with a correct input, entities key not found.')

        # testing if entity contains UID and label
        self.assertIsNotNone(res.get('json').get('entities')[0].get('UID') , self.link_endpoint_gpt_v2 + ' endpoint is failing with a correct input, resulting entity does not have UID.')
        self.assertIsNotNone(res.get('json').get('entities')[0].get('label') , self.link_endpoint_gpt_v2 + ' endpoint is failing with a correct input, resulting entity does not have label.')
        
    def test_link_endpoint_gpt_v2_incorrect_input(self):
        # incorrect case
        res = query_api('post', linking_url + self.link_endpoint_gpt_v2, {}, {}, {})
        
        self.assertEqual(res.get('code'), 422 , self.link_endpoint_gpt_v2 + ' endpoint allows incorrect input.')

    # link_endpoint_falcon unit tests
    def test_link_endpoint_falcon_correct_input(self):
        # testing a correct case:
        res = query_api('post', linking_url + self.link_endpoint_falcon, {}, {}, {
            'text': 'Who is the president of Bolivia?'
        })

        self.assertEqual(res.get('code'), 200 , self.link_endpoint_falcon + ' endpoint is failing with a correct input.')

        # testing if the result contains entity list
        self.assertIsNotNone(res.get('json').get('entities') , self.link_endpoint_falcon + ' endpoint is failing with a correct input, entities key not found.')

        # testing if entity contains UID and label
        self.assertIsNotNone(res.get('json').get('entities')[0].get('UID') , self.link_endpoint_falcon + ' endpoint is failing with a correct input, resulting entity does not have UID.')
        self.assertIsNotNone(res.get('json').get('entities')[0].get('label') , self.link_endpoint_falcon + ' endpoint is failing with a correct input, resulting entity does not have label.')
        
    def test_link_endpoint_falcon_incorrect_input(self):
        # incorrect case
        res = query_api('post', linking_url + self.link_endpoint_falcon, {}, {}, {})
        
        self.assertEqual(res.get('code'), 422 , self.link_endpoint_falcon + ' endpoint allows incorrect input.')

    # link_endpoint_opentapioca unit tests
    def test_link_endpoint_opentapioca_correct_input(self):
        # testing a correct case:
        res = query_api('post', linking_url + self.link_endpoint_opentapioca, {}, {}, {
            'text': 'Who is the president of Bolivia?'
        })

        self.assertEqual(res.get('code'), 200 , self.link_endpoint_opentapioca + ' endpoint is failing with a correct input.')

        # testing if the result contains entity list
        self.assertIsNotNone(res.get('json').get('entities') , self.link_endpoint_opentapioca + ' endpoint is failing with a correct input, entities key not found.')

        # testing if entity contains UID and label
        self.assertIsNotNone(res.get('json').get('entities')[0].get('UID') , self.link_endpoint_opentapioca + ' endpoint is failing with a correct input, resulting entity does not have UID.')
        self.assertIsNotNone(res.get('json').get('entities')[0].get('label') , self.link_endpoint_opentapioca + ' endpoint is failing with a correct input, resulting entity does not have label.')
        
    def test_link_endpoint_opentapioca_incorrect_input(self):
        # incorrect case
        res = query_api('post', linking_url + self.link_endpoint_opentapioca, {}, {}, {})
        
        self.assertEqual(res.get('code'), 422 , self.link_endpoint_opentapioca + ' endpoint allows incorrect input.')

if __name__ == '__main__':
    unittest.main()