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

    # /link/ unit tests
    def test_link_endpoint_correct_input(self):
        endpoint = '/link/'
        # testing a correct case:
        res = query_api('post', linking_url + endpoint, {}, {}, {
            'text': 'Who is the president of Bolivia?'
        })

        self.assertEqual(res.get('code'), 200 , '/link/ endpoint is failing with a correct input.')

        # testing if the result contains entity list
        self.assertIsNotNone(res.get('json').get('entities') , '/link/ endpoint is failing with a correct input, entities key not found.')

        # testing if the result contains relations list
        self.assertIsNotNone(res.get('json').get('relations') , '/link/ endpoint is failing with a correct input, relations key not found.')

        # testing if entity contains UID and label
        self.assertIsNotNone(res.get('json').get('entities')[0].get('UID') , '/link/ endpoint is failing with a correct input, resulting entity does not have UID.')
        self.assertIsNotNone(res.get('json').get('entities')[0].get('label') , '/link/ endpoint is failing with a correct input, resulting entity does not have label.')
        
        # testing if relation contains UID and label
        self.assertIsNotNone(res.get('json').get('relations')[0].get('UID') , '/link/ endpoint is failing with a correct input, resulting relation does not have UID.')
        self.assertIsNotNone(res.get('json').get('relations')[0].get('label') , '/link/ endpoint is failing with a correct input, resulting relation does not have label.')
        
    def test_link_endpoint_incorrect_input(self):
        endpoint = '/link/'
        # incorrect case
        res = query_api('post', linking_url + endpoint, {}, {}, {})
        
        self.assertEqual(res.get('code'), 422 , '/link/ endpoint allows incorrect input.')


if __name__ == '__main__':
    unittest.main()