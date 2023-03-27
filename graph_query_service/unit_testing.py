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

graph_query_service = dict(config.items('GRAPH_QUERY_SERVICE'))
graph_query_url = 'http://' + graph_query_service.get('ip') + ':' + graph_query_service.get('port')

class Graph_Query_testing(unittest.TestCase):
    def test_entity_endpoint_correct_input(self):
        endpoint = '/entity/'
        entity_UID = 'Q750'
        # testing a correct case:
        res = query_api('get', graph_query_url + endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 200 , '/entity/ endpoint is failing with a correct input.')

        # testing if the returned UID is correct
        self.assertIsNotNone(res.get('json').get('UID') , '/entity/ endpoint is failing with a correct input, UID key not found.')

        self.assertEqual(res.get('json').get('UID') , entity_UID, '/entity/ endpoint is failing with a correct input, UID returned is incorrect.')

        # checking if the label is returned
        self.assertIsNotNone(res.get('json').get('label') , '/entity/ endpoint is failing with a correct input, label key not found.')

        # checking if properties are returned
        self.assertIsNotNone(res.get('json').get('props') , '/entity/ endpoint is failing with a correct input, props key not found.')

        self.assertGreater(len(res.get('json').get('props').keys()), 0, '/entity/endpoint is not returning properties')

        # check properties have a type and a value
        self.assertIsNotNone(res.get('json').get('props').get('P30').get('data_type') , '/entity/ endpoint is failing with a correct input, property P30 data_type not found.')
        self.assertIsNotNone(res.get('json').get('props').get('P30').get('data_type') , '/entity/ endpoint is failing with a correct input, property P30 value not found.')

    def test_entity_endpoint_invalid_entity(self):
        # testing with an unexisting entity
        endpoint = '/entity/'
        entity_UID = '50'
        res = query_api('get', graph_query_url + endpoint + entity_UID, {}, {}, {})
        self.assertEqual(res.get('code'), 400 , '/entity/ endpoint is working with an unexisting entity UID.')

    

if __name__ == '__main__':
    unittest.main()