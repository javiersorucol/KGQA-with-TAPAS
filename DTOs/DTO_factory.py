from DTOs.graph_query_DTOs import Table_templates_DTO, Table_template_DTO,Table_template_property_DTO
from fastapi import HTTPException

def wikidata_to_Table(wikidata_response, template:Table_template_DTO):
    try:
        table = {}
        results = wikidata_response.get('results').get('bindings')
        # for earch returned element
        for result in results:
            keys = list(result.keys())
            # As properties are optional, some of the class expected properties might lack in each row, therefore we will fill it with None
            for expected_property in template.properties:
                if expected_property.UID not in result.keys():
                    # print('adding none for property: ', expected_property)
                    result[expected_property.UID] = {'type': str(None), 'value': str(None)}
                    if expected_property.type == 'WikibaseItem':
                        result[expected_property.UID +'Label'] = {'type': str(None), 'value': str(None)}

            #for each varible of the element
            for key,value in result.items():
                if key == 'item' or key == 'itemLabel':
                    # if key not in the table we will add it
                    if key not in table.keys():
                        table[key] = []
                    table[key].append(value.get('value'))
                elif 'Label' not in key:
                    # if key not in the table we will add it
                    if key not in table.keys():
                        table[key] = []
                    value = value.get('value') if result.get(key + 'Label') is None else result.get(key + 'Label').get('value')
                    table[key].append(value)
            
        
        if len(table.keys()) == 0:
            for header in wikidata_response.get('head').get('vars'):
                if 'Label' not in header:
                    table[header] = []
            table['itemLabel'] = []
        return table
    
    except Exception as e:
        raise Exception('Error transforming wikidata table result to DTO. Error: ' + str(e))

