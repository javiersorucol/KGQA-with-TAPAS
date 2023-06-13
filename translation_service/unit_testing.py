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
    translate_endpoint = translation_service.get('translate_endpoint')

    def test_translation_endpoint_correct_input(self):
        # testing a correct case:
        res = query_api('post', translation_service_url + self.translate_endpoint, {}, {}, {
            "text": "¿En dónde murió John Lennon?",
            "mode": "es-en"
        })
        self.assertEqual(res.get('code'), 200 , self.translate_endpoint + ' endpoint is failing with a correct input.')

        # testing question text is in the expected answer
        self.assertIsNotNone(res.get('json').get('text') , self.translate_endpoint + ' endpoint is failing with a correct input, text key not found.')

        # test if the translation mode is returned
        self.assertIsNotNone(res.get('json').get('mode') , self.translate_endpoint + ' endpoint is failing with a correct input, mode key not found.')

    def test_translation_endpoint_unsupported_mode(self):
        # testing an unvalid translation mode
        res = query_api('post', translation_service_url + self.translate_endpoint, {}, {}, {
            "text": "¿En dónde murió John Lennon?",
            "mode": "es-e"
        })
        self.assertEqual(res.get('code'), 400 , self.translate_endpoint + ' endpoint is not returning error 400 using an unsupported translation mode.')

    def test_transltion_endpoint_invalid_payload(self):
        # testing not valid object as payload
        res = query_api('post', translation_service_url + self.translate_endpoint, {}, {}, {
            "text": "¿En dónde murió John Lennon?",
            "models": "es-en"
        })
        self.assertEqual(res.get('code'), 422 , self.translate_endpoint + ' endpoint is not returning error coe 422 when sending an incorrect DTO.')




if __name__ == '__main__':
    unittest.main()