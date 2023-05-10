from DTOs.graph_query_DTOs import Table_templates_DTO, Table_template_DTO,Table_template_property_DTO
from fastapi import HTTPException

def wikidata_to_Table(wikidata_response, template:Table_template_DTO):
    try:
        table = {}
        results = wikidata_response.get('results').get('bindings')
        expected_properties = [property.UID for property in template.properties]
        # for earch returned element
        for result in results:
            # As properties are optional, some of the class expected properties might lack in each row, therefore we will fill it with None
            if len(result.keys()) - 2 < len(expected_properties):
                print('result with less properties than expected: ', str(len(result.keys())), ', expected: ', str(len(expected_properties)))
                for expected_property in expected_properties:
                    if expected_property not in result.keys():
                        print('adding none for property: ', expected_property)
                        result[expected_property] = {'type': str(None), 'value': str(None)}

                print('New number of keys: ', str(len(result.keys())))
            #for each varible of the element
            for key,value in result.items():
                # if key not in the table we will add it
                if key not in table.keys():
                    table[key] = []
                table[key].append(value.get('value'))
            
        
        return table
    
    except Exception as e:
        raise Exception('Error transforming wikidata table result to DTO. Error: ' + str(e))

