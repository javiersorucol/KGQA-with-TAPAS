# Before running this script make sure to run the graph query Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import unittest
from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file

from graph_query_service.service  import get_value_by_type, sparql_query_kg, get_entity_data

import re

config = read_config_file('App_config.ini')

graph_query_service = dict(config.items('GRAPH_QUERY_SERVICE'))
graph_query_url = 'http://' + graph_query_service.get('ip') + ':' + graph_query_service.get('port')

class Graph_Query_testing(unittest.TestCase):
    entity_table_endpoint = graph_query_service.get('entity_table_endpoint')
    entity_triples_endpoint = graph_query_service.get('entity_triples_endpoint')

    # entity_table_endpoint unit tests

    # should return 200 in correct case
    # should contain the proper keys in correct case
    def test_entity_table_endpoint_correct_entity(self):
        entity_UID = 'Q750'

        res = query_api('get', graph_query_url + self.entity_table_endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 200 , self.entity_table_endpoint + ' endpoint is failing with a correct input.')

        self.assertIsNotNone(res.get('json').get('labels_table') , self.entity_table_endpoint + ' endpoint is failing with a correct input, labels_table key not found.')
        self.assertIsNotNone(res.get('json').get('uri_table') , self.entity_table_endpoint + ' endpoint is failing with a correct input, uri_table key not found.')
    
    # should return 400 for unvalid entities
    def test_entity_table_endpoint_unvalid_entity(self):
        entity_UID = '50'

        res = query_api('get', graph_query_url + self.entity_table_endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 400 , self.entity_table_endpoint + ' endpoint is not returning error code 400 when reciving an invalid entity.')

    # should return 400 for no label entities
    def test_entity_table_endpoint_no_label_entity(self):
        entity_UID = 'Q27103826'

        res = query_api('get', graph_query_url + self.entity_table_endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 400 , self.entity_table_endpoint + ' endpoint is not returning error code 400 when reciving an entity with no associated en label.')

    # should return a list separated with ; for multiple value properties
    def test_entity_table_endpoint_multiple_values(self):
        entity_UID = 'Q750'

        res = query_api('get', graph_query_url + self.entity_table_endpoint + entity_UID, {}, {}, {})

        results = res.get('json').get('labels_table').get('official language')[0].split(';')

        self.assertGreater(len(results), 1, self.entity_table_endpoint + ' endpoint is not  returning multiple value properties in required format.')

    # entity_triples_endpoint unit tests

    # should return 200 in correct case
    # should contain the proper keys in correct case
    def test_entity_triples_endpoint_correct_entity(self):
        entity_UID = 'Q750'

        res = query_api('get', graph_query_url + self.entity_triples_endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 200 , self.entity_triples_endpoint + ' endpoint is failing with a correct input.')

        self.assertIsNotNone(res.get('json').get('triples') , self.entity_triples_endpoint + ' endpoint is failing with a correct input, triples key not found.')
        
    # should return 400 for unvalid entities
    def test_entity_triples_endpoint_unvalid_entity(self):
        entity_UID = '50'

        res = query_api('get', graph_query_url + self.entity_triples_endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 400 , self.entity_triples_endpoint + ' endpoint is not returning error code 400 when reciving an invalid entity.')

    # should return 400 for no label entities
    def test_entity_triples_endpoint_no_label_entity(self):
        entity_UID = 'Q27103826'

        res = query_api('get', graph_query_url + self.entity_triples_endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 400 , self.entity_triples_endpoint + ' endpoint is not returning error code 400 when reciving an entity with no associated en label.')

    # should return a list separated with ; for multiple value properties
    def test_entity_triples_endpoint_multiple_values(self):
        entity_UID = 'Q750'

        res = query_api('get', graph_query_url + self.entity_triples_endpoint + entity_UID, {}, {}, {})

        result = re.search('((\s)?(\w|:)+;\s(\w|:)+)+', res.get('json').get('triples'))

        self.assertTrue(result, self.entity_triples_endpoint + ' endpoint is not  returning multiple value properties in required format.')

    ### function unit tests
    # get_entity_data unit tests
    def test_get_entity_data_correct_input(self):
        entity_UID = 'Q750'
        # testing a correct case:
        res = get_entity_data(entity_UID)
        # testing if the returned UID is correct
        self.assertIsNotNone(res.get('id') , 'get_entity_data function is failing with a correct input, id key not found.')

        self.assertEqual(res.get('id') , entity_UID, 'get_entity_data function is failing with a correct input, id returned is incorrect.')

        # checking if the label is returned
        self.assertIsNotNone(res.get('labels') , 'get_entity_data function is failing with a correct input, labels key not found.')

        # checking if description is returned
        self.assertIsNotNone(res.get('descriptions') , 'get_entity_data function is failing with a correct input, descriptions key not found.')

        # checking if the label is returned
        self.assertIsNotNone(res.get('aliases') , 'get_entity_data function is failing with a correct input, aliases key not found.')

        # checking if properties are returned
        self.assertIsNotNone(res.get('claims') , 'get_entity_data function is failing with a correct input, claims key not found.')

    def test_get_value_by_type_function(self):
        # case quantity
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
        self.assertEqual('+2016-06-10', res, 'get_value_by_type funcion is failing in time case.')
        # case wikibase item
        res = get_value_by_type('wikibase-item', {
            "value": {
                "entity-type": "item",
                "numeric-id": 193858,
                "id": "Q193858"
            },
            "type": "wikibase-entityid"
        })
        self.assertEqual('http://www.wikidata.org/entity/Q193858', res, 'get_value_by_type funcion is failing in wikibase-item case.')
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
        self.assertIn(str(-9.67), res, 'get_value_by_type funcion is failing in global-coordinate case, latitude not found.')
        self.assertIn(str(-65.45), res, 'get_value_by_type funcion is failing in global-coordinate case, longitude not found.')
        self.assertIn(str(1), res, 'get_value_by_type funcion is failing in global-coordinate case, altitude not found.')        

    def test_sparql_query_kg_function_incorrect_inputs(self):
        # incorrect SPARQL
        res = sparql_query_kg('SELECT DISTINCT ?class WHERE  wd:$entity_UID wdt:$class_property_UID ?class .}', {'entity_UID' : 'Q750', 'class_property_UID' : 'P31'})
        self.assertEqual(res.get('code'), 400, ' Incorrect SPARQL is not reflecting error code 400')
        
        # not enough inputs
        res = sparql_query_kg('SELECT DISTINCT ?class WHERE  { wd:$entity_UID wdt:$class_property_UID ?class .}', {'entity_UID' : 'Q750'})
        self.assertEqual(res.get('code'), 500, ' Not enough parameters for the SPRAQL query error is not reflecting error code 500')


if __name__ == '__main__':
    unittest.main()