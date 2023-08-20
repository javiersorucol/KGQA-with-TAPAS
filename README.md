# KGQA-with-different-QA-methods
The main goal of this project is to use different QA methods to build a KGQA pipeline, the methods used are TAPAS and LLMs (GPT). This system transforms the knowledge contained in the Wikidata Knowlege Graph to tables and text and used it with the QA methods to answer user natural language questions.

This project is designed using a microservice architechture, we work with the followin microservices:
- Entity linking Service
- Answer service
- Graph query service (currently  working with Wikidata)
- Main API

## Run the project
To run each service use the following commands:

- Linking service:

```
uvicorn linking_service.service:app  --reload --log-config linking_service/Logs/log_config.ini --port 8091
```

- Graph Query service

```
uvicorn graph_query_service.service:app  --reload --log-config graph_query_service/Logs/log_config.ini --port 8092
```

- Answer service:

```
uvicorn answer_service.service:app  --reload --log-config answer_service/Logs/log_config.ini --port 8093
```

- Main service

```
uvicorn main_service.service:app  --reload --log-config main_service/Logs/log_config.ini --port 8094
```
## Evaluation
We performed 3 experiments, one to evaluate entity linking, other to evaluate the used prompts and one to compare the KGQA systems.

All the experiments can be found in the evalution folder, and are run using a selection of "simple" questions from QALD9-ES. We define a simple question as a question which resulting SPARQL only requires one triple to get an answer. The questions where also grouped by the answer type to check the performance of the systems over different type of questions (singular, multiple, boolean, aggregation). The used dataset can be found in the evaluation/datasets folder.

### Entity linking experiment
In this experiment we compare two versions of our GPT entity linker with Falcon 2.0 and OpenTapioca. For this experiment we added the expected entities to all the questions, we've achieved this using the entity_extractor.ipynb notebook in the evaluation/notebooks folder. This notebook looks for the required entities using the question SPARQL to look for all the used entities and store them under the key "linked_entities". In this experiment question type is not relevant therefore we present results for the complete evaluation set.
The results of the experiment are:
|    Method   |  endpoint |  Precision |  Recall  |  F1 score  |
|-------------|:---------:|:----------:|:--------:|:----------:|
|    GPT v1   | /link/gpt/v1/  |  0.8146  | 0.8196  |  0.8171  |
|    GPT v2   | /link/gpt/v2/  |  0.8098  |  0.8021  |  0.8059  |
|  Falcon 2.0  | /link/falcon/  |  0.4130  |  0.4733  |  0.4410  |
|  OpenTapioca  | /link/opentapioca/  |  0.5097  |  0.4582  |  0.4825  |

### Prompting experiment
|  Prompt  |   subset       |  Precision  |  Recall  |  F1 score  |  Correct answers(%) | 
|----------|----------------|-------------|----------|------------|---------------------|
| prompt 1 |  singular      |  0.7891     |  0.8080  |  0.7984    |  74.38%             |
| prompt 1 |  multiple      |  0.8028     |  0.0346  |  0.0664    |  50.75%             |
| prompt 1 |  boolean       |  0.7647     |  0.5909  |  0.6667    |  59.09%             |
| prompt 1 |  aggregaation  |  0.0600     |  0.2142  |  0.0938    |  21.43%             |
|----------|----------------|-------------|----------|------------|---------------------|
| prompt 2 |  singular      |  0.7966     |  0.7768  |  0.7866    |  75.21%             |
| prompt 2 |  multiple      |  0.7986     |  0.0340  |  0.0653    |  46.97%             |
| prompt 2 |  boolean       |  1.0000     |  0.7273  |  0.8421    |  72.73%             |
| prompt 2 |  aggregaation  |  0.2273     |  0.3571  |  0.2778    |  35.71%             |

### Systems experiment
|  System  |   subset       |  Precision  |  Recall  |  F1 score  |  Correct answers(%) | 
|----------|----------------|-------------|----------|------------|---------------------|
| GPT KGQA |  singular      |  0.7966     |  0.7768  |  0.7866    |  75.21%             |
| GPT KGQA |  multiple      |  0.7986     |  0.0340  |  0.0653    |  46.97%             |
| GPT KGQA |  boolean       |  1.0000     |  0.7273  |  0.8421    |  72.73%             |
| GPT KGQA |  aggregaation  |  0.2273     |  0.3571  |  0.2778    |  35.71%             |
|----------|----------------|-------------|----------|------------|---------------------|
| TAPAS KGQA |  singular      |  0.3529     |  0.4500  |  0.3956    |  44.17%             |
| TAPAS KGQA |  multiple      |  0.4124     |  0.0060  |  0.0118    |  14.93%             |
| TAPAS KGQA |  boolean       |  0.0000     |  0.0000  |  0.0000    |  00.00%             |
| TAPAS KGQA |  aggregaation  |  0.4286     |  0.4286  |  0.4286    |  42.86%             |
