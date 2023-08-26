# KGQA-with-different-QA-methods
The main goal of this project is to use different QA methods to build a KGQA pipeline, the methods used are TAPAS and LLMs (GPT). This system transforms the knowledge contained in the Wikidata Knowlege Graph to tables and text and used it with the QA methods to answer user natural language questions.

This project is designed using a microservice architechture, we work with the followin microservices:
- Entity linking Service
- Answer service
- Graph query service (currently  working with Wikidata)
- Main API

## Run the project
To run each service use the following commands:

- Translation service:

```
uvicorn translation_service.service:app  --reload --log-config translation_service/Logs/log_config.ini --port 8090
```

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
| prompt 1 |  singular      |  0.9100     |  0.7521  |  0.8235    |  74.38%             |
| prompt 1 |  multiple      |  0.8996     |  0.0307  |  0.0593    |  52.24%             |
| prompt 1 |  boolean       |  1.0000     |  0.6818  |  0.8108    |  68.18%             |
| prompt 1 |  aggregaation  |  0.7778     |  0.5000  |  0.6087    |  50.00%             |
|----------|----------------|-------------|----------|------------|---------------------|
| prompt 2 |  singular      |  0.8762     |  0.7603  |  0.8142    |  74.38%             |
| prompt 2 |  multiple      |  0.8957     |  0.0307  |  0.0593    |  52.24%             |
| prompt 2 |  boolean       |  1.0000     |  0.7273  |  0.8421    |  72.73%             |
| prompt 2 |  aggregaation  |  0.3846     |  0.3571  |  0.3704    |  35.71%             |

### Systems experiment
|  System  | Language |   Subset       |  Precision  |  Recall  |  F1 score  |  Correct answers(%) | 
|----------|----------|----------------|-------------|----------|------------|---------------------|
| GPT KGQA |  English |  singular      |  0.9100     |  0.7521  |  0.8235    |  74.38%             |
| GPT KGQA |  English |  multiple      |  0.8996     |  0.0307  |  0.0593    |  52.24%             |
| GPT KGQA |  English |  boolean       |  1.0000     |  0.6818  |  0.8108    |  68.18%             |
| GPT KGQA |  English |  aggregaation  |  0.7778     |  0.5000  |  0.6087    |  50.00%             |
|----------|----------|----------------|-------------|----------|------------|---------------------|
| GPT KGQA |  Spanish |  singular      |  0.8713     |  0.7273  |  0.7928    |  71.07%             |
| GPT KGQA |  Spanish |  multiple      |  0.9600     |  0.0321  |  0.0622    |  46.27%             |
| GPT KGQA |  Spanish |  boolean       |  0.8000     |  0.5454  |  0.6486    |  54.54%             |
| GPT KGQA |  Spanish |  aggregaation  |  0.4545     |  0.3571  |  0.4000    |  35.71%             |
|----------|----------|----------------|-------------|----------|------------|---------------------|
| TAPAS KGQA |  English |  singular      |  0.3709     |  0.4628  |  0.4118    |  45.45%             |
| TAPAS KGQA |  English |  multiple      |  0.4396     |  0.0059  |  0.0117    |  16.42%             |
| TAPAS KGQA |  English |  boolean       |  0.0000     |  0.0000  |  0.0000    |  00.00%             |
| TAPAS KGQA |  English |  aggregaation  |  0.4167     |  0.3571  |  0.3846    |  35.71%             |
|------------|----------|----------------|-------------|----------|------------|---------------------|
| TAPAS KGQA |  Spanish |  singular      |  0.1450     |  0.1570  |  0.1508    |  15.70%             |
| TAPAS KGQA |  Spanish |  multiple      |  0.2272     |  0.0032  |  0.0063    |  4.48%              |
| TAPAS KGQA |  Spanish |  boolean       |  0.0000     |  0.0000  |  0.0000    |  00.00%             |
| TAPAS KGQA |  Spanish |  aggregaation  |  0.1818     |  0.1429  |  0.1600    |  14.29%             |