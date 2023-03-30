# Before running this script make sure to run the translation Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import unittest
from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file

from graph_query_service.service  import get_value_by_type, sparql_query_kg

config = read_config_file('App_config.ini')

graph_query_service = dict(config.items('GRAPH_QUERY_SERVICE'))
graph_query_url = 'http://' + graph_query_service.get('ip') + ':' + graph_query_service.get('port')

class Graph_Query_testing(unittest.TestCase):

    # /entity/{entity_UID} unit tests
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
        self.assertIsNotNone(res.get('json').get('properties') , '/entity/ endpoint is failing with a correct input, properties key not found.')

        self.assertGreater(len(res.get('json').get('properties').keys()), 0, '/entity/endpoint is not returning properties')

        # check properties have a type and a value
        self.assertIsNotNone(res.get('json').get('properties').get('P30').get('data_type') , '/entity/ endpoint is failing with a correct input, property P30 data_type not found.')
        self.assertIsNotNone(res.get('json').get('properties').get('P30').get('value') , '/entity/ endpoint is failing with a correct input, property P30 value not found.')

    def test_entity_endpoint_invalid_entity(self):
        # testing with an unexisting entity
        endpoint = '/entity/'
        entity_UID = '50'
        res = query_api('get', graph_query_url + endpoint + entity_UID, {}, {}, {})
        self.assertEqual(res.get('code'), 400 , '/entity/ endpoint is working with an unexisting entity UID.')


    # /entity/classes/{entity_UID} unit tests
    def test_entity_classes_endpoint_correct_input(self):
        endpoint = '/entity/classes/'
        entity_UID = 'Q750'
        # testing a correct case:
        res = query_api('get', graph_query_url + endpoint + entity_UID, {}, {}, {})

        self.assertEqual(res.get('code'), 200 , '/entity/clases/ endpoint is failing with a correct input.')
    
    def test_entity_classes_endpoint_invalid_entity(self):
        # testing with an unexisting entity
        endpoint = '/entity/classes/'
        entity_UID = '50'
        res = query_api('get', graph_query_url + endpoint + entity_UID, {}, {}, {})
        self.assertEqual(res.get('code'), 400 , '/entity/clases/ endpoint is working with an unexisting entity UID.')

    # get class template endpoint
    def test_class_template_endpoint_correct_case(self):
        endpoint = '/class/template/'
        class_UID = 'Q6256'
        res = query_api('get', graph_query_url + endpoint + class_UID, {}, {}, {})
        self.assertEqual(res.get('code'), 200 , '/class/template/ endpoint is not working with correct data.')

        # check result contains frequency
        self.assertIsNotNone(res.get('json').get('frequency'), 'Frequency key is missing in/class/template/  endpoint response.')

        # check result contains subclasses
        self.assertIsNotNone(res.get('json').get('subclasses'), 'Subclasses key is missing in/class/template/  endpoint response.')

        # check result contains properties
        self.assertIsNotNone(res.get('json').get('properties'), 'Properties key is missing in/class/template/  endpoint response.')        
        
        # check banned dataa type property is not in the properties list
        self.assertIsNone(res.get('json').get('properties').get('P1566'), 'Banned data  type "ExternalID" property found in the template on /class/template/ endpoint.')

    def test_class_template_union_class_case(self):
        endpoint = '/class/template/'
        class_UID = 'Q187449'
        res = query_api('get', graph_query_url + endpoint + class_UID, {}, {}, {})
        self.assertEqual(res.get('code'), 200 , '/class/template/ endpoint is not working with correct union class.')

        # check the heritage class properties are returned
        self.assertIsNotNone(res.get('json').get('properties').get('P1435'), 'Expected properties in union class are missing in /class/template/ endpoint.')

    def test_class_template_parent_class_case(self):
        endpoint = '/class/template/'
        class_UID = 'Q1549591'
        res = query_api('get', graph_query_url + endpoint + class_UID, {}, {}, {})
        self.assertEqual(res.get('code'), 200 , '/class/template/ endpoint is not working with correct class that inherited its properties.')

        # check result contains properties
        self.assertNotEqual(len(res.get('json').get('properties')), 0, 'Properties are not inherited in /class/template/ endpoint.')
        
    def test_class_template_parent_class_extra_properties_case(self):
        endpoint = '/class/template/'
        class_UID = 'Q5119'
        res = query_api('get', graph_query_url + endpoint + class_UID, {}, {}, {})
        self.assertEqual(res.get('code'), 200 , '/class/template/ endpoint is not working with correct class that inherited its properties and have its own properties.')

        # check if result contains clas exclusive property
        self.assertIsNotNone(res.get('json').get('properties').get('P1376'), 'Expected non inherited properties are missing in /class/template/ endpoint.')
 
    # fill template endpoint
    def test_fill_templates_correct_case(self):
        endpoint = '/templates/fill/'
        res = query_api('post', graph_query_url + endpoint, {}, {}, {
            "templates": [
                {
                "UID": "Q515",
                "properties": [
                    {
                    "UID": "P17",
                    "label": "country",
                    "type": "WikibaseItem"
                    },
            {
                    "UID": "P2046",
                    "label": "area",
                    "type": "Quantity"
                    }
                ]
                }
            ],
            "entities_UIDs": [
                "Q60", "Q2807"
            ]
        })
        self.assertEqual(res.get('code'), 200 , '/templates/fill/ endpoint is not working with a correct input.')

    def test_fill_templates_incorrect_input(self):
        endpoint = '/templates/fill/'
        res = query_api('post', graph_query_url + endpoint, {}, {}, {
            "templates": [
                {
                "UID": "Q515",
                "properties": [
                    {
                    "UID": "P17",
                    "label": "country",
                    "type": "WikibaseItem"
                    },
            {
                    "UID": "P2046",
                    "label": "area",
                    "type": "Quantity"
                    }
                ]
                }
            ]
        })
        self.assertEqual(res.get('code'), 422 , '/templates/fill/ endpoint allows incorrect input.')



    ### function unit tests
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

    def test_sparql_query_kg_function_config_sparqls(self):
        # Verifying all the sparqls
        local_config = read_config_file('graph_query_service/Config/Config.ini')

        classes_sparql = local_config['SPARQL']['classes']
        subclasses_sparql = local_config['SPARQL']['subclasses']
        union_sparql = local_config['SPARQL']['union']
        extra_properties_sparql = local_config['SPARQL']['extra_properties']
        parents_sparql = local_config['SPARQL']['parents']
        properties_sparql = local_config['SPARQL']['properties']
        table_sparql = local_config['SPARQL']['table']

        all_params = {
            'class_property_UID' : local_config['KNOWLEDGE_GRAPH']['class_property_UID'],
            'subclass_property_UID' : local_config['KNOWLEDGE_GRAPH']['subclass_property_UID'],
            'union_of_property_UID' : local_config['KNOWLEDGE_GRAPH']['union_property_UID'],
            'extra_properties_UID' : local_config['KNOWLEDGE_GRAPH']['extra_properties_UID'],
            'class_properties_UID' : local_config['KNOWLEDGE_GRAPH']['class_properties_UID'],
            'entity_UID': 'Q750',
            'class_UID' : 'Q6256',
            'property_UID' : 'P6',
            'properties_declaration' : '',
            'properties_list' : '',
            'filter_conditions' : '1',
            'limit' : '10'
        }

        res = sparql_query_kg(classes_sparql, all_params)
        self.assertEqual(res.get('code'), 200, ' classes_sparql notworking.')

        res = sparql_query_kg(subclasses_sparql, all_params)
        self.assertEqual(res.get('code'), 200, ' subclasses_sparql notworking.')

        res = sparql_query_kg(union_sparql, all_params)
        self.assertEqual(res.get('code'), 200, ' union_sparql notworking.')

        res = sparql_query_kg(extra_properties_sparql, all_params)
        self.assertEqual(res.get('code'), 200, ' extra_properties_sparql notworking.')

        res = sparql_query_kg(parents_sparql, all_params)
        self.assertEqual(res.get('code'), 200, ' parents_sparql notworking.')

        res = sparql_query_kg(properties_sparql, all_params)
        self.assertEqual(res.get('code'), 200, ' properties_sparql notworking.')

        res = sparql_query_kg(table_sparql, all_params)
        self.assertEqual(res.get('code'), 200, ' table_sparql notworking.')



        



if __name__ == '__main__':
    unittest.main()