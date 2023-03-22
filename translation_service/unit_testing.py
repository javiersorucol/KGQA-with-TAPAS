# Before running this script make sure to run the translation Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import unittest
from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file

config = read_config_file('App_config.ini')

translation_service = dict(config.items('TRANSLATION_SERVICE'))
translation_service_url = 'http://' + translation_service.get('ip') + ':' + translation_service.get('port')

class Translation_testing(unittest.TestCase):
    correct_case = {
        "text": "¿En dónde murió John Lennon?",
        "mode": "es-en"
    }
    error_case = {
        "text": "¿En dónde murió John Lennon?",
        "mode": "es-"
    }
    def test_translation_endpoint_correct_input(self):
        endpoint = '/translate/'
        # testing a correct case:
        res = query_api('post', translation_service_url + endpoint, {}, {}, {
            "text": "¿En dónde murió John Lennon?",
            "mode": "es-en"
        })
        self.assertEqual(res.get('code'), 200 , '/translate/ endpoint is failing with a correct input.')

        # testing question text is in the expected answer
        self.assertIsNotNone(res.get('json').get('text') , '/translate/ endpoint is failing with a correct input.')

        # test if the translation mode is returned
        self.assertIsNotNone(res.get('json').get('mode') , '/translate/ endpoint is failing with a correct input.')

    def test_trasnlation_endpoint_error_case(self):
        endpoint = '/translate/'
        # testing an unvalid translation mode
        res = query_api('post', translation_service_url + endpoint, {}, {}, {
            "text": "¿En dónde murió John Lennon?",
            "mode": "es-e"
        })
        self.assertEqual(res.get('code'), 400 , '/translate/ endpoint is failing with a correct input.')

        # testing not valid object as payload
        res = query_api('post', translation_service_url + endpoint, {}, {}, {
            "text": "¿En dónde murió John Lennon?",
            "models": "es-en"
        })
        self.assertEqual(res.get('code'), 422 , '/translate/ endpoint is failing with a correct input.')



if __name__ == '__main__':
    unittest.main()