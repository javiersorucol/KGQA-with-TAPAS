# Before running this script make sure to run the main, linking, graph query and answer ser
import sys
import os
import json
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from utils.Request_utils import get_answer_tapas_method
from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json
from graph_query_service.service import get_label

system='TAPAS KGQA'
system_id='TAPAS_KGQA'
entity_prefix = 'http://www.wikidata.org/entity/'

# We will only evaluate over 'Simple' questions, we define simple question as questions where only one triple is required to get the answer
test_subset = read_json('evaluation/datasets/test_subsets.json').get('simple')
train_subset = read_json('evaluation/datasets/train_subsets.json').get('simple')

example_question = {
                "id": "128",
                "question": [
                    {
                        "language": "en",
                        "string": "In what year did Paraguay proclaim its independence?"
                    }
                ],
                "query": {
                    "sparql": " SELECT ?o1 WHERE { <http://www.wikidata.org/entity/Q359>  <http://www.wikidata.org/prop/direct/P50>  ?o1 .  }"
                },
                "answers": [
                    {
                        "head": {
                            "vars": [
                                "o1"
                            ]
                        },
                        "results": {
                            "bindings": [
                                {
                                    "o1": {
                                        "datatype": "http://www.w3.org/2001/XMLSchema#dateTime",
                                        "type": "literal",
                                        "value": "1811-01-01T00:00:00Z"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }

def evaluate(system_id=system_id, system=system):
    try:
        subsets = ['boolean','aggregation','singular','multiple']
        results = {
            'system': system
        }
        for subset in subsets:
            results[subset] = evaluate_subset(subset)
        
        save_json('evaluation/results/'+system_id+'_results.json', results)
    except Exception as e:
        print('Unkown error: ', str(e))

def evaluate_subset(selected_subset:str):
    global test_subset
    global train_subset
    print('Evaluating subset: ', selected_subset)
    print('Evaluating of the subset with the testing dataset...')
    test_results=evaluate_dataset(test_subset, selected_subset=selected_subset)
    print('Done')
    print('Evaluating of the subset with the training dataset...')
    train_results=evaluate_dataset(train_subset, selected_subset=selected_subset)
    print('Done')
    return {'train_results':train_results, 'test_results':test_results}

def evaluate_dataset(dataset: dict, selected_subset : str):
    results = {}
    try:
        for question in dataset.get(selected_subset):
            results[question.get('id')] = evaluate_question(question=question)

        return results
    except Exception as e:
        print('Unexpected error: ' + str(e))
        return results

def evaluate_question(question: dict, TP=0, FN=0, FP=0):
    print('Evaluation of question: ', question.get('id'))
    global entity_prefix
    en_question = next((x for x in question.get('question') if x.get('language') == 'en'), None).get('string')
    correct = True
    notes = 'None'
    if en_question is None:
        # questions with no english translation are not taken into account
        print('Question does not have an english translation')
        return {'TP': TP, 'FN': FN, 'FP': FP, 'correct': False, 'notes':'No english translation', 'error':True, 'actual_answers': [], 'expected_answers' : []}
    
    res = get_answer_tapas_method(question=en_question)
    
    actual_answers = []

    if res.get('code') != 200:
        # if main srvice fails the query (usually by tokens, dont take it into acccount)
        print('Error in question: ', question.get('id'))
        print ('Main service answered with an error. Code: ' + str(res))
        return {'TP': TP, 'FN': FN, 'FP': FP, 'correct': False, 'notes':'Main service returned an error code: ' + str(res), 'error':True, 'actual_answers': [], 'expected_answers' : []}
    
    elif res.get('json').get('answer') is None:
        notes = 'Error key answer not found for question: ' + question.get('id')
        print(notes)
        correct = False
        

    else:
        res = res.get('json').get('answer')

        if 'Answer not found' not in res:
            actual_answers = [x.strip() for x in res.replace('The answer of your question is: ','').rstrip('.').split(';')]
        else:
            notes = 'Answer not found'
            correct = False
    
    expected_answers = []

    if question.get('answers')[0].get('boolean') is not None:
        if question.get('answers')[0].get('boolean'):
            expected_answers.append('yes')
        else:
            expected_answers.append('no')
    else:

        for answer in question.get('answers')[0].get('results').get('bindings'):
            for var,value in answer.items():
                if value.get('type') == 'uri':
                    label = value.get('value')
                    if entity_prefix in label:
                        #print('Searching label for: ', label)
                        label = get_label(label.replace(entity_prefix,''))
                    expected_answers.append(label.lower())
                elif value.get('type') == 'literal':
                    if value.get('datatype') == 'http://www.w3.org/2001/XMLSchema#dateTime':
                        date = value.get('value')[0:10].lower()
                        expected_answers.append(date)
                    else:
                        expected_answers.append(value.get('value').lower())
                
    TP, FN, FP, correct = qualify_result(expected_answers=expected_answers, actual_answers=actual_answers, TP=TP, FN=FN, FP=FP, correct=correct)

    return {'TP': TP, 'FN': FN, 'FP': FP, 'correct': correct, 'notes': str(notes), 'error':False, 'actual_answers': json.dumps(list(actual_answers)), 'expected_answers' : list(expected_answers)}

def qualify_result(expected_answers, actual_answers, TP, FN, FP, correct):
    def compare_element_array(el, arr):
        for x in arr:
            if el.lower() in x.lower() or x.lower() in el.lower():
                return True
        return False
    
    for actual_answer in actual_answers:
        if compare_element_array(actual_answer, expected_answers):
            TP = TP + 1
        else:
            print('Actual answer: ', actual_answer)
            print('Not found in expected answers: ', expected_answers)
            correct = False
            FP = FP + 1
    
    for expected_answer in expected_answers:
        if not compare_element_array(expected_answer, actual_answers):
            print('Expected answer: ', expected_answer)
            print('Not found in actual answers: ', actual_answers)
            correct = False
            FN = FN + 1

    return TP, FN, FP, correct

evaluate()