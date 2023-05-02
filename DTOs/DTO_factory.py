from DTOs.graph_query_DTOs import Table_template_DTO, Table_template_property_DTO, Table_templates_DTO
from fastapi import HTTPException

def wikidata_to_Table(wikidata_response):
    try:
        table = {}
        results = wikidata_response.get('results').get('bindings')
        # for earch returned element
        for result in results:
            #for each varible of the element
            for key,value in result.items():
                # if key not in the table we will add it
                if key not in table.keys():
                    table[key] = []
                table[key].append(value.get('value'))
            
        return table
    
    except Exception as e:
        raise Exception('Error transforming wikidata table result to DTO. Error: ' + str(e))

