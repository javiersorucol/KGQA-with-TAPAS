# Before running this script make sure to run the linking Service
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from utils.Request_utils import query_api
from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json
from utils.Metrics_utils import get_f1, get_precision, get_recall

# read required configurations to call the service, do not forget to run the linking service using the command from the readme file
config = read_config_file('App_config.ini')

linking_service = dict(config.items('LINKING_SERVICE'))
linking_url = 'http://' + linking_service.get('ip') + ':' + linking_service.get('port')

link_endpoint_gpt_v1 = linking_service.get('link_endpoint_gpt_v1')
link_endpoint_falcon = linking_service.get('link_endpoint_falcon')
link_endpoint_opentapioca = linking_service.get('link_endpoint_opentapioca')

# modify this var depending what endpoint you want to evaluate
selected_endpoint = link_endpoint_opentapioca
print('Testing endpoind: ', selected_endpoint)

results = {}
# We will only evaluate over 'Simple' questions, we define simple question as questions where only one triple is required to get the answer
test_subset = read_json('evaluation/datasets/test_subsets.json').get('simple')
train_subset = read_json('evaluation/datasets/train_subsets.json').get('simple')

# We have organized QALD9-ES simple question by the answer type: singular, multiple, boolean and aggregation. 
# For this experiment we do not care about the question type, we will run all the questions and group the answer over one group

def evaluate_dataset(dataset: dict):
    global selected_endpoint, linking_url

    def compare_answers(actual_answers, expected_answers, TP, FP, FN):
        TP = TP + len(list(filter(lambda x: x in expected_answers, actual_answers)))
        FP = FP + len(list(filter(lambda x: x not in expected_answers, actual_answers)))
        FN = FN + len(list(filter(lambda x: x not in actual_answer, expected_answers)))
        return TP, FP, FN

    question_types = ['singular', 'multiple', 'boolean', 'aggregation']
    TP = FP = FN = 0
    for subset in  question_types:
        print('Evaluating questions from the subset: ', subset)
        for question in dataset.get(subset):
            en_question = next((x for x in question.get('question') if x.get('language') == 'en'), None).get('string')
            if en_question is None:
                raise Exception('Question does not have an english translation: ' + str(question))
            
            res = query_api('post', linking_url + selected_endpoint, {}, {}, {
                'text': en_question
            })

            if res.get('code') != 200:
                raise Exception('Entity linking service answered with an error. Code: ' + str(res.get('code')) + ' Error: ' + res.get('text'))
            
            actual_answer = [x.get('UID') for x in res.get('json').get('entities')]
            TP, FP, FN = compare_answers(actual_answers=actual_answer, expected_answers=question.get('linked_entities'), TP=TP, FP=FP, FN=FN)
        
        print('Subset evaluation terminated.')

    print('Evaluation finished. Results: ')
    print('TP: ', TP, ' FP: ', FP, ' FN: ', FN)
    return TP, FP, FN

print('Evaluating test dataset...')
TP, FP, FN = evaluate_dataset(test_subset)
results['testset_precision'] = get_precision(TP=TP, FP=FP)
results['testset_recall'] = get_recall(TP=TP, FN=FN)
results['testset_f1'] = get_f1(TP=TP, FN=FN, FP=FP)
print('Results for the test dataset: ')
print('Precision: ', results['testset_precision'])
print('Recall: ', results['testset_recall'])
print('F1: ', results['testset_f1'])

print('Evaluating train dataset...')
TP, FP, FN = evaluate_dataset(train_subset)
results['trainset_precision'] = get_precision(TP=TP, FP=FP)
results['trainset_recall'] = get_recall(TP=TP, FN=FN)
results['trainset_f1'] = get_f1(TP=TP, FN=FN, FP=FP)
print('Results for the train dataset: ')
print('Precision: ', results['trainset_precision'])
print('Recall: ', results['trainset_recall'])
print('F1: ', results['trainset_f1'])
