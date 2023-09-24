# Before running this script make sure to run the tapas Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import unittest
from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file

config = read_config_file('App_config.ini')

main_service = dict(config.items('MAIN_SERVICE'))
main_service_url = 'http://' + main_service.get('ip') + ':' + main_service.get('port')

class Main_Service_Testing(unittest.TestCase):

    tapas_endpoint = main_service.get('tapas_endpoint')
    gpt_endpoint = main_service.get('gpt_endpoint')

    # tapas_endpoint unit tests
    def test_tapas_endpoint_correct_input(self):
    
        # testing a correct case:
        res = query_api('post', main_service_url + self.tapas_endpoint, {}, {}, {
        "text": "Who is the president of Bolivia?",
        })

        self.assertEqual(res.get('code'), 200 , self.tapas_endpoint + ' endpoint is failing with a correct input.')

        # testing if the resulting dto has the correct format
        self.assertIsNotNone(res.get('json').get('answer') , self.tapas_endpoint + ' endpoint is failing with a correct input, answer key not found.')

    # service must return 422 whe receiving invalid payload
    def test_tapas_endpoint_invalid_payload(self):

        # testing not valid object as payload
        res = query_api('post', main_service_url + self.tapas_endpoint, {}, {}, {
        "text______": "Who is the president of Bolivia?",
        })
        self.assertEqual(res.get('code'), 422 , self.tapas_endpoint + ' endpoint is not returning error code 422 when receiving n incorrect payload.')

    # gpt_endpoint unit tests
    def test_gpt_endpoint_correct_input(self):
    
        # testing a correct case:
        res = query_api('post', main_service_url + self.gpt_endpoint, {}, {}, {
        "text": "Who is the president of Bolivia?",
        })

        self.assertEqual(res.get('code'), 200 , self.gpt_endpoint + ' endpoint is failing with a correct input.')

        # testing if the resulting dto has the correct format
        self.assertIsNotNone(res.get('json').get('answer') , self.gpt_endpoint + ' endpoint is failing with a correct input, answer key not found.')

    # service must return 422 whe receiving invalid payload
    def test_gpt_endpoint_invalid_payload(self):

        # testing not valid object as payload
        res = query_api('post', main_service_url + self.gpt_endpoint, {}, {}, {
        "text______": "Who is the president of Bolivia?",
        })
        self.assertEqual(res.get('code'), 422 , self.gpt_endpoint + ' endpoint is not returning error code 422 when receiving n incorrect payload.')

if __name__ == '__main__':
    unittest.main()