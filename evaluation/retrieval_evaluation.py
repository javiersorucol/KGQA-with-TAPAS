import sys
import os
from pathlib import Path
import time
import string
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

import re
from utils.Configuration_utils import read_config_file
from utils.Json_utils import read_json, save_json
from utils.Request_utils import get_entity_triples_lang_chain

# In this experimnt we will evaluate the retrieval of our pipeline,
# First evaluation metric is data_corpus recall, with this we mean the number of questions where the data retrieved
# from the Wikidata KG actually contain the answer to the question
# The next evaluation metric is context recall, wich works the same as data_corpus recall, but operating with
# the context retrieved from the vector store instead of the data corpus
# Following we will set an example of a list containing one example question to test this script

example = {
    'complex' : {
        'singular' : [
            {
                'id' : '88',
                'question' : [
                    {
                        'language' : 'en',
                        'string' : 'Who  is the president of Bolivia?'
                    },
                ],
                'query' : {
                    'sparql' : 'PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/> SELECT ?x WHERE { wd:Q750 wdt:P6 ?x  }'
                },
                "answers": [
                    {
                        "head" : {
                        "vars" : [ "x" ]
                        },
                        "results" : {
                        "bindings" : [ {
                            "x" : {
                            "type" : "uri",
                            "value" : "http://www.wikidata.org/entity/Q16149892"
                            }
                        } ]
                        }
                    }
                ],
                "linked_entities": [
                    "Q750"
                ]
            }
        ]
    }
}

# For each question we want to save different data to be able to analyze the results in dept if necessary,
# here we will show an example of how the results will be stored
# [
#   '88' : {
#       'question_string': 'Who is the president of Bolivia?'
#       'linked_entities': ['Q750']
#       'error' : False
#       'ground_truth' : []
#       'error_message' : None
#       'data_corpus' : {
#           'text': '...',
#           'correct': 2
#           'incorrect' : 0,
#           'list_of_errors' : [...]        
#        }
#        'context' : {
#           'text': '...',
#           'correct': 2
#           'incorrect' : 0
#           'list_of_errors' : [...]        
#        }
#   } 
# ]
#
## First we will make a function to return the entities list in the expected format to contact the service

def get_linked_entities_DTO(entities):
    res = { 'entities': [] }
    for entity in entities:
        res['entities'].append({
            'UID': entity,
            'label': ''
        })
    return res

# We will need to define a function to retrieve labels only from the cache of the service

def get_label(uri):
    cache = read_json('graph_query_service/Data/labels_map.json')
    return cache.get(uri.replace('http://www.wikidata.org/entity/',''))

# for both metrics we need to be able to find a ground truth, we will achive this by generating regular expressions from the question SPARQL

def get_question_ground_truth(sparql:str):

  # Modify URIs to keep only uids
  sparql = sparql.replace('<http://www.wikidata.org/entity/', '').replace('<http://www.wikidata.org/prop/direct/','').replace('>','')

  # Let's find the question triples
  triples = re.findall(r'(WHERE|ASK)(\s*{.+})', sparql.upper())[0][1].strip()[1:-1].split('.')

  # Filter extra operator lines (e.g. FILTER)
  compiler = re.compile(r'(<|>|\/|:|\.|\w|\?|\*|\+|\^|\(|\)|\||\!|\s)+\s+(<|>|\/|:|\.|\w|\?|\*|\+|\^|\(|\)|\||\s|\!)+\s+(<|>|\/|:|\.|\w|\?|\*|\+|\^|\(|\)|\||\!|\s)+')
  triples = [ triple for triple in triples if compiler.match(triple.strip(), re.IGNORECASE ) ]

  # let's transform each triple in the format ('Q**', 'P**' , '?**')
  triples = [ [ re.sub(r'\s*(WDT|WD)\s*:\s*','', y.strip()) for y in re.split(r'\s+', x.strip())] for x in triples]

  # We need to deal with posible operators in the property of each triple
  for (i, triple) in enumerate(triples):
        property_value = triple [1]
        # remove +,*,? operators
        property_value = property_value.replace('*','').replace('+','').replace('?','').replace('(','').replace(')','')
        # Case ^: Inverse path, we need to modify the triple to change subjectnd object
        if '^' in property_value:
          property_value = property_value.replace('^','')
          triples[i] = [triple[2], property_value, triple[0]]
        # When working with | we need to append all the properties to modify when generating the Regular expresion
        elif '|' in property_value:
          properties = [x.strip() for x in re.split(r'\|', property_value)]
          triples[i] = [triple[0]] + properties + [triple[2]]
        # When working with / we will add more than one triple that connects the question
        elif '/' in property_value:
          properties = [x.strip() for x in re.split(r'/', property_value)]
          triples[i] = [triple[0], properties[0], '?x']
          for i in range(1,len(properties)):
            if i < len(properties) - 1:
              triples.append(['?x', properties[i], '?x'])
            else:
              triples.append(['?x', properties[i], triple[2]])
        else:
          triples[i] = [triple[0], property_value, triple[2]]

        # Ignoring negation case (!)

  # Generating the regular expresion for the triple

  expressions = []
  for triple in triples:
    # Get labels
    labels = [ get_label(element) if '?' not in element else '.+'  for element in triple]
    # Normal case
    if len(triple) == 3:
      expressions.append(' '.join(labels))
    # | case
    else:
      expressions.append(labels[0] + ' (' + '|'.join(labels[1:-1]) + ') ' + labels[-1])

  return expressions

# definimos una funcion que permita hacer match a partir de un texto y una lista de RE
def check_expressions(ground_truth, text):
    correct = 0
    incorrect = 0
    list_of_errors = []

    text = text.replace('\"','')

    for  expression in ground_truth:
        if re.search(expression, text, flags=re.IGNORECASE):
            correct = correct + 1

    else:
      incorrect = incorrect + 1
      list_of_errors.append(expression)

    return correct, incorrect, list_of_errors

# Ahora vamos a crear una funcion para evaluar cada pregunta generando el resultado presentado previamente

def evaluate_question(question):
    try:
        context = None
        data_corpus = None
        error = False
        error_message = None
        question_string = None
        linked_entities = None
        ground_truth = None

        question_string = next((x for x in question.get('question') if x.get('language') == 'en'), None).get('string')
        linked_entities = get_linked_entities_DTO(question.get('linked_entities'))
        ground_truth = get_question_ground_truth(question.get('query').get('sparql'))
        
        # retrieve the corpus data and the context from the graph query service
        res = get_entity_triples_lang_chain(linked_entities, question_string)
        correct, incorrect, list_of_errors= check_expressions(ground_truth, res.get('data_corpus'))
        data_corpus = {
           'text' : res.get('data_corpus'),
           'correct' : correct,
           'incorrect' : incorrect,
           'list_of_errors' : list_of_errors
        }

        correct, incorrect, list_of_errors= check_expressions(ground_truth, res.get('triples'))

        context = {
           'text' : res.get('triples'),
           'correct' : correct,
           'incorrect' : incorrect,
           'list_of_errors' : list_of_errors
        }



    except Exception as e:
       error = True
       error_message = str(e)

    finally:

        return  {
        'question_string' : question_string,
        'linked_entities' : linked_entities,
        'error' : error,
        'ground_truth' : ground_truth,
        'error_message' : error_message,
        'data_corpus' : data_corpus,
        'context' : context
        }

# Finally, we will implement the method to evaluate all the questions and save them in an evaluation file
def evaluate(data, destiny='retrieval_evaluation.json'):
    # check if the file already exists and read it
    results = None
    if not Path('evaluation/results/' + destiny).is_file():
        results = {}
    else:
      results = read_json('evaluation/results/' + destiny)

      print('Starting evaluation')

    # for each type of questions in the complex category
    for type,list_of_questions in data.get('complex').items():
        print(f'Evaluating {type} questions')
        # for each question
        for question in list_of_questions:
            print(f'Evaluating question: {question.get('id')}')
           # if question has not been evaluated before
            if  results.get(type) is not None: 
                if results.get(type).get(question.get('id')) is not None:
                    results.get(type)[question.get('id')] = evaluate_question(question)
                    save_json('evaluation/results/' + destiny ,results)
            
            else:
                results[type] = {}
                results.get(type)[question.get('id')] = evaluate_question(question)
                save_json('evaluation/results/' + destiny ,results)



evaluate(example)