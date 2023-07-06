# Before running this script make sure to run the main, linking, graph query and answer ser
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from utils.Request_utils import get_answer_gpt_method
from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json
from utils.Metrics_utils import get_f1, get_precision, get_recall
from graph_query_service.service import get_label

import datetime

# read required configurations to call the service, do not forget to run the linking service using the command from the readme file
config = read_config_file('App_config.ini')

main_service = dict(config.items('MAIN_SERVICE'))
main_service_url = 'http://' + main_service.get('ip') + ':' + main_service.get('port')

main_service_gpt_endpoint = main_service.get('gpt_endpoint')

selected_subset = 'aggregation'
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

def evaluate_dataset(dataset: dict, selected_subset : str=selected_subset):
    TP = FP = FN = 0
    for question in dataset.get(selected_subset):
        TP, FN, FP = evaluate_question(question=question, TP=TP, FN=FN, FP=FP)
    print('TP: ', TP)
    print('FP: ', FP)
    print('FN: ', FN)
    precision = get_precision(TP=TP, FP=FP)
    print('Precision: ', precision)
    recall = get_recall(TP=TP, FN=FN)
    print('Recall: ', recall)
    f1 = get_f1(TP=TP, FP=FP, FN=FN)
    print('F1: ', f1)

def evaluate_question(question: dict, TP, FN, FP):
    global entity_prefix
    en_question = next((x for x in question.get('question') if x.get('language') == 'en'), None).get('string')
    if en_question is None:
        print('Question does not have an english translation')
        return TP, FN, FP
    
    res = get_answer_gpt_method(question=en_question)

    if res.get('code') != 200:
        print ('Main service answered with an error. Code: ' + str(res))
        actual_answers = []
    
    if res.get('json').get('answer') is None:
        actual_answers = []
    
    res = res.get('json').get('answer')
    actual_answers = []
    if 'Answer not found' in res:
        actual_answers = []
    actual_answers = [x.strip() for x in res.replace('The answer of your question is: ','').rstrip('.').split(';')]
    #print(actual_answer)
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
                        label = get_label(label.replace(entity_prefix,''))
                    expected_answers.append(label.lower())
                elif value.get('type') == 'literal':
                    if value.get('datatype') == 'http://www.w3.org/2001/XMLSchema#dateTime':
                        date = value.get('value')[0:10].lower()
                        expected_answers.append(date)
                    else:
                        expected_answers.append(value.get('value').lower())
                
    TP, FN, FP = qualify_result(expected_answers=expected_answers, actual_answers=actual_answers, TP=TP, FN=FN, FP=FP)
    return TP, FN, FP

def qualify_result(expected_answers, actual_answers, TP, FN, FP):
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
            FP = FP + 1
    
    for expected_answer in expected_answers:
        if not compare_element_array(expected_answer, actual_answers):
            print('Expected answer: ', expected_answer)
            print('Not found in actual answers: ', actual_answers)
            FN = FN + 1

    return TP, FN, FP

# print(evaluate_question(example_question,0,0,0))
print('Evaluationg subset: ', selected_subset)
# print('Evaluation subset of the testing dataset...')
# evaluate_dataset(test_subset)
print('Evaluation subset of the training dataset...')
evaluate_dataset(train_subset)
###################################
# singular subset
##
# testing
# TP:  22
# FP:  3
# FN: 3
# Precision:  0.88
# Recall:  0.88
# F1:  0.88
## training
# TP:  73
# FP:  30
# FN:  10
# Precision:  0.7087378640776699
# Recall:  0.8795180722891566
# F1:  0.7849462365591398
######################################################
# boolean subset
##
## testing
# TP:  0
# FP:  1
# FN:  1
# Precision:  0.0
# Recall:  0.0
# F1:  0.0
## training
# TP:  13
# FP:  3
# FN:  3
# Precision:  0.8125
# Recall:  0.8125
# F1:  0.8125
########################################################
# multiple subset
## testing
# TP:  75
# FP:  49
# FN:  83
# Precision:  0.6048387096774194
# Recall:  0.47468354430379744
# F1:  0.5319148936170213
## training
# TP:  139
# FP:  27
# FN:  165
# Precision:  0.8373493975903614
# Recall:  0.45723684210526316
# F1:  0.5914893617021276
########################################################
# aggregation subset
## testing
# TP:  0
# FP:  7
# FN:  1
# Precision:  0.0
# Recall:  0.0
# F1:  0.0
## training
# TP:  3
# FP:  76
# FN:  7
# Precision:  0.0379746835443038
# Recall:  0.3
# F1:  0.06741573033707865
