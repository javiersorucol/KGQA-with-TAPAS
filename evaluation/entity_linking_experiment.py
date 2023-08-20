# Before running this script make sure to run the linking Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json

# read required configurations to call the service, do not forget to run the linking service using the command from the readme file
config = read_config_file('App_config.ini')

linking_service = dict(config.items('LINKING_SERVICE'))
linking_url = 'http://' + linking_service.get('ip') + ':' + linking_service.get('port')

link_endpoint_gpt_v1 = linking_service.get('link_endpoint_gpt_v1')
link_endpoint_gpt_v2 = linking_service.get('link_endpoint_gpt_v2')
link_endpoint_falcon = linking_service.get('link_endpoint_falcon')
link_endpoint_opentapioca = linking_service.get('link_endpoint_opentapioca')

results = {}

# We have organized QALD9-ES simple question by the answer type: singular, multiple, boolean and aggregation. 
# For this experiment we do not care about the question type, we will run all the questions and group the answer over one group

def evaluate_dataset(selected_endpoint : str):
    global linking_url, results

    print('Testing endpoind: ', selected_endpoint)

    results[selected_endpoint] = {}

    def compare_answers(actual_answers, expected_answers, TP, FP, FN):
        TP = TP + len(list(filter(lambda x: x in expected_answers, actual_answers)))
        FP = FP + len(list(filter(lambda x: x not in expected_answers, actual_answers)))
        FN = FN + len(list(filter(lambda x: x not in actual_answer, expected_answers)))
        correct = FP == 0 and FN == 0
        return TP, FP, FN, correct

    question_types = ['singular', 'multiple', 'boolean', 'aggregation']
    correct = True
    TP = FP = FN = 0
    for subset in  question_types:
        print('Evaluating questions from the subset: ', subset)
        results[selected_endpoint][subset] = {'train_results' : {}, 'test_results': {}}
        ### TRAIN
        print(' Evaluation for training dataset')
        dataset = read_json('evaluation/datasets/train_subsets.json').get('simple')
        # dataset = {'singular' : [], 'boolean': [{
        #     'id':'1', 
        #     'question':[{
        #                 "language": "en",
        #                 "string": "Who is the president of Bolivia?"
        #             }], 
        #             'linked_entities' : ["Q750"]}], 'multiple': [], 'aggregation':[]}
        for question in dataset.get(subset):
            answer = {}
            en_question = next((x for x in question.get('question') if x.get('language') == 'en'), None)
            if en_question is None:
                answer = { 'TP' : 0, 'FP' : 0, 'FN' : 0, 'correct' : False, 'notes': 'No english translation avilable', 'error': True, 'actual_answers' : [], 'expected_answers':[]}
            
            res = query_api('post', linking_url + selected_endpoint, {}, {}, {
                'text': en_question.get('string')
            })

            if res.get('code') != 200:
                answer = { 'TP' : 0, 'FP' : 0, 'FN' : 0, 'correct' : False, 'notes': 'Entity linking service answered with an error. Code: ' + str(res), 'error': True, 'actual_answers' : [], 'expected_answers':[]}
            else :
                actual_answer = [x.get('UID') for x in res.get('json').get('entities')]
                TP, FP, FN, correct = compare_answers(actual_answers=actual_answer, expected_answers=question.get('linked_entities'), TP=TP, FP=FP, FN=FN)
            
                answer = { 'TP' : TP, 'FP' : FP, 'FN' : FN, 'correct' : correct, 'notes': 'None', 'error': False, 'actual_answers' : actual_answer, 'expected_answers':question.get('linked_entities')}
            
            results[selected_endpoint][subset]['train_results'][question.get('id')] = answer

        ### TEST

        print(' Evaluation for testing dataset')
        dataset = read_json('evaluation/datasets/test_subsets.json').get('simple')
        # dataset = {'singular' : [], 'boolean': [{'id':'12', 'question':[{
        #                 "language": "en",
        #                 "string": "Was Marc Chagall a jew?"
        #             }], 'linked_entities' : ["Q7325",
        #             "Q93284"]}], 'multiple': [], 'aggregation':[]}
        for question in dataset.get(subset):
            answer = {}
            en_question = next((x for x in question.get('question') if x.get('language') == 'en'), None)
            if en_question is None:
                answer = { 'TP' : 0, 'FP' : 0, 'FN' : 0, 'correct' : False, 'notes': 'No english translation avilable', 'error': True, 'actual_answers' : [], 'expected_answers':[]}
            
            res = query_api('post', linking_url + selected_endpoint, {}, {}, {
                'text': en_question.get('string')
            })

            if res.get('code') != 200:
                answer = { 'TP' : 0, 'FP' : 0, 'FN' : 0, 'correct' : False, 'notes': 'Entity linking service answered with an error. Code: ' + str(res), 'error': True, 'actual_answers' : [], 'expected_answers':[]}
            else :
                actual_answer = [x.get('UID') for x in res.get('json').get('entities')]
                TP, FP, FN, correct = compare_answers(actual_answers=actual_answer, expected_answers=question.get('linked_entities'), TP=TP, FP=FP, FN=FN)
            
                answer = { 'TP' : TP, 'FP' : FP, 'FN' : FN, 'correct' : correct, 'notes': 'None', 'error': False, 'actual_answers' : actual_answer, 'expected_answers':question.get('linked_entities')}
            
            results[selected_endpoint][subset]['test_results'][question.get('id')] = answer

        print('Subset evaluation terminated.')

    #return results

evaluate_dataset(link_endpoint_falcon)
evaluate_dataset(link_endpoint_opentapioca)
evaluate_dataset(link_endpoint_gpt_v1)
evaluate_dataset(link_endpoint_gpt_v2)
save_json('evaluation/results/entity_linking_results.json',results)
