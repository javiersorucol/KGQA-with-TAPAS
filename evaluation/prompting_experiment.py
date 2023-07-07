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

selected_subset = 'multiple'
entity_prefix = 'http://www.wikidata.org/entity/'

# We will only evaluate over 'Simple' questions, we define simple question as questions where only one triple is required to get the answer
test_subset = read_json('evaluation/datasets/test_subsets.json').get('simple')
train_subset = read_json('evaluation/datasets/train_subsets.json').get('simple')

ignore_questions_test = [56, 136, 132, 182]
ignore_questions_train = [115, 1, 3, 392]

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

def evaluate_dataset(dataset: dict, selected_subset : str=selected_subset, ignored_list=[]):
    TP = FP = FN = correct = incorrect = 0
    for question in dataset.get(selected_subset):
        if int(question.get('id')) not in ignored_list:
            TP, FN, FP, correct, incorrect = evaluate_question(question=question, TP=TP, FN=FN, FP=FP, correct=correct, incorrect=incorrect)
    print('correct answers: ', correct)
    print('incorrect answers: ', incorrect)
    print('TP: ', TP)
    print('FP: ', FP)
    print('FN: ', FN)
    precision = get_precision(TP=TP, FP=FP)
    print('Precision: ', precision)
    recall = get_recall(TP=TP, FN=FN)
    print('Recall: ', recall)
    f1 = get_f1(TP=TP, FP=FP, FN=FN)
    print('F1: ', f1)

def evaluate_question(question: dict, TP, FN, FP, correct, incorrect):
    print('Evaluation of question: ', question.get('id'))
    global entity_prefix
    en_question = next((x for x in question.get('question') if x.get('language') == 'en'), None).get('string')
    good = True
    if en_question is None:
        # questions with no english translation are not taken into account
        print('Question does not have an english translation')
        return TP, FN, FP, correct, incorrect
    
    res = get_answer_gpt_method(question=en_question)
    
    actual_answers = []

    if res.get('code') != 200:
        # if main srvice fails the query (usually by tokens, dont take it into acccount)
        print('Error in question: ', question.get('id'))
        print ('Main service answered with an error. Code: ' + str(res),)
        return TP, FN, FP, correct, incorrect
    
    elif res.get('json').get('answer') is None:
        print('Error key answer not found for question: ', question.get('id'))
        good = False

    else:
        res = res.get('json').get('answer')

        if 'Answer not found' not in res:
            actual_answers = [x.strip() for x in res.replace('The answer of your question is: ','').rstrip('.').split(';')]
        else:
            good = False
    
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
                        print('Searching label for: ', label)
                        label = get_label(label.replace(entity_prefix,''))
                    expected_answers.append(label.lower())
                elif value.get('type') == 'literal':
                    if value.get('datatype') == 'http://www.w3.org/2001/XMLSchema#dateTime':
                        date = value.get('value')[0:10].lower()
                        expected_answers.append(date)
                    else:
                        expected_answers.append(value.get('value').lower())
                
    TP, FN, FP, good = qualify_result(expected_answers=expected_answers, actual_answers=actual_answers, TP=TP, FN=FN, FP=FP, good=good)
    if good:
        correct = correct + 1
    else:
        incorrect = incorrect + 1

    return TP, FN, FP, correct, incorrect

def qualify_result(expected_answers, actual_answers, TP, FN, FP, good):
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
            good = False
            FP = FP + 1
    
    for expected_answer in expected_answers:
        if not compare_element_array(expected_answer, actual_answers):
            print('Expected answer: ', expected_answer)
            print('Not found in actual answers: ', actual_answers)
            good = False
            FN = FN + 1

    return TP, FN, FP, good

# print(evaluate_question(example_question,0,0,0))
print('Evaluationg subset: ', selected_subset)
# print('Evaluation subset of the testing dataset...')
# evaluate_dataset(test_subset, ignored_list=ignore_questions_test)
print('Evaluation subset of the training dataset...')
evaluate_dataset(train_subset,ignored_list=ignore_questions_train)


