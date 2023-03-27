# Before running this script make sure to run the translation Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import unittest
from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file

from graph_query_service.service  import get_value_by_type

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

    def test_get_value_by_type_function(self):
        # case quntity
        res = get_value_by_type('quantity', {
            "value": {
                "amount": "+115",
                "unit": "http://www.wikidata.org/entity/Q25250"
            },
            "type": "quantity"
        })
        self.assertEqual('+115', res, 'get_value_by_type funcion is failing in quantity case.')
        # case url
        res = get_value_by_type('url', {
            "value": "http://www.iec.ch/worldplugs/list_bylocation.htm",
            "type": "string"
        })
        self.assertEqual('http://www.iec.ch/worldplugs/list_bylocation.htm', res, 'get_value_by_type funcion is failing in url case.')
        #case time
        res = get_value_by_type('time', {
            "value": {
                "time": "+2016-06-10T00:00:00Z",
                "timezone": 120,
                "before": 0,
                "after": 0,
                "precision": 11,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
            },
            "type": "time"
        })
        self.assertEqual('+2016-06-10T00:00:00Z', res, 'get_value_by_type funcion is failing in time case.')
        # case wikibase item
        res = get_value_by_type('wikibase-item', {
            "value": {
                "entity-type": "item",
                "numeric-id": 193858,
                "id": "Q193858"
            },
            "type": "wikibase-entityid"
        })
        self.assertEqual('Q193858', res, 'get_value_by_type funcion is failing in wikibase-item case.')
        # case monolingualtext
        res = get_value_by_type('monolingualtext', {
            "value": {
                "text": "World Plugs",
                "language": "en"
            },
            "type": "monolingualtext"
        })
        self.assertEqual('World Plugs', res, 'get_value_by_type funcion is failing in monolingual case.')
        # case global  coordinate
        res = get_value_by_type('globe-coordinate', {
            "value": {
                "latitude": -9.67,
                "longitude": -65.45,
                "altitude": 1,
                "precision": 1.0e-6,
                "globe": "http://www.wikidata.org/entity/Q2"
            },
            "type": "globecoordinate"
        })
        print(res)
        self.assertIn(str(-9.67), res, 'get_value_by_type funcion is failing in global-coordinate case, latitude not found.')
        self.assertIn(str(-65.45), res, 'get_value_by_type funcion is failing in global-coordinate case, longitude not found.')
        self.assertIn(str(1), res, 'get_value_by_type funcion is failing in global-coordinate case, altitude not found.')        

if __name__ == '__main__':
    unittest.main()