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

tapas_service = dict(config.items('TAPAS_SERVICE'))
tapas_service_url = 'http://' + tapas_service.get('ip') + ':' + tapas_service.get('port')

class Tapas_testing(unittest.TestCase):
    def test_tapas_endpoint_correct_input(self):
        endpoint = '/ask/'
        # testing a correct case:
        res = query_api('post', tapas_service_url + endpoint, {}, {}, {
        "question": "Who is the MVP of Argentina?",
        "table":{"Team": ["Argentina", "Bolivia", "Brasil"], "Wins": [2, 1, 0], "MVP": ["Messi", "Martins", "Neymar"]}
        })
        self.assertEqual(res.get('code'), 200 , '/ask/ endpoint is failing with a correct input.')

        # testing question text is in the expected answer
        self.assertIsNotNone(res.get('json').get('answer') , '/ask/ endpoint is failing with a correct input, answer key not found.')

    def test_tapas_endpoint_invalid_payload(self):
        # testing not valid object as payload
        endpoint = '/ask/'
        res = query_api('post', tapas_service_url + endpoint, {}, {}, {
        "question": "Who is the MVP of Argentina?",
        })
        self.assertEqual(res.get('code'), 422 , '/ask/ endpoint is not returning error code 422 when receiving n incorrect payload.')


if __name__ == '__main__':
    unittest.main()