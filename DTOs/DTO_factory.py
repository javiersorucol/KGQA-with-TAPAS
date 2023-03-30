from DTOs.graph_query_DTOs import Table_template_DTO, Table_template_property_DTO, Table_templates_DTO
from fastapi import HTTPException

def wikidata_to_Table(wikidata_response):
    try:
        table = []
        results = wikidata_response.get('results').get('bindings')
        while len(results) > 0:
            same_items = list(filter((lambda x: x.get('item').get('value') == results[0].get('item').get('value') ) ,results))
            results = list(filter((lambda x: x.get('item').get('value') != results[0].get('item').get('value') ) ,results))
            
            new_item = same_items.pop(0)
            for item in same_items:
                for key,value in item.items():
                    if key != 'item' and key != 'itemLabel':
                        if type(new_item.get(key).get('value')) is not list:
                            new_item[key]['value'] = [ new_item.get(key).get('value') ]
                            
                        if value.get('value') not in new_item.get(key).get('value'):
                            new_item[key]['value'].append(value.get('value'))
            
            table.append(new_item)
    
    #table = {}
    # for prop in template.props:
    #     table[prop.UID] = {
    #         'type' : prop.type,
    #         'label' : prop.label,
    #         'values' : []
    #     }

    # table['item'] = {
    #     'type' : 'wikidatabase-item',
    #     'label' : 'item URI',
    #     'values' : []
    # }
    # table['itemLabel'] = {
    #     'type' : 'string',
    #     'label' : 'item label',
    #     'values' : []
    # }

    # for result in wikidata_response.get('results').get('bindings'):
    #     for key,value in result.items():
    #         table[key]['values'].append(value.get('value'))

        return table
    
    except Exception as e:
        raise Exception('Error transforming wikidata table result to DTO. Error: ' + str(e))

