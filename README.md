# KGQA-with-TAPAS
Using TeBaQA to create a KGQA pipeline. The main idea is to transfor a KGQA problem to  QA over tables problem,  then use TAPAS to find an answer. We aim to achieve this by creating relevant tables for each question based on the class of all the question's entities.

This project is designed using a microservice architechture, we work with the followin microservices:
- Translation Service
- Entity linking Service
- Answer service
- Graph query service (currently  working with Wikidata)
- Classification service
- Main API

## Run the project
To run each service use the following commands:

- Translation service:

```
uvicorn translation_service.service:app  --reload --log-config translation_service/Logs/log_config.ini --port 8091
```

- Linking service:

```
uvicorn linking_service.service:app  --reload --log-config linking_service/Logs/log_config.ini --port 8092
```

- Graph Query service

```
uvicorn graph_query_service.service:app  --reload --log-config graph_query_service/Logs/log_config.ini --port 8093
```

- Answer service:

```
uvicorn answer_service.service:app  --reload --log-config answer_service/Logs/log_config.ini --port 8094
```

- Main service

```
uvicorn main_service.service:app  --reload --log-config main_service/Logs/log_config.ini --port 8097
```
## Evaluation
We performed 3 experiments, one to evaluate entity linking, other to evaluate the used prompts and one to compare the KGQA systems.

All the experiments can be found in the evalution folder, and are run using a selection of "simple" questions from QALD9-ES. We define a simple question as a question which resulting SPARQL only requires one triple to get an answer. The questions where also grouped by the answer type to check the performance of the systems over different type of questions (singular, multiple, boolean, aggregation). The used dataset can be found in the evaluation/datasets folder.

### Entity linking experiment
In this experiment we compare two versions of our GPT entity linker with Falcon 2.0 and OpenTapioca. For this experiment we added the expected entities to all the questions, we've achieved this using the entity_extractor.ipynb notebook in the evaluation/notebooks folder. This notebook looks for the required entities using the question SPARQL to look for all the used entities and store them under the key "linked_entities".
The results of the experiment are:
|    Method   |  endpoint |  Precision (test set)  |  Recall (test set)  |  F1 score (test set)  |  Precision (train set)  |  Recall (train set)  |  F1 score (train set)  |
|-------------|:---------:|:----------------------:|:-------------------:|:---------------------:|:-----------------------:|:--------------------:|:-----------------:|
|    GPT v1   | /link/gpt/v1/  |  0.38095  |  0.73846  |  0.50262  |  0.40701  |  0.79474  |  0.53832  |
|    GPT v2   | /link/gpt/v2/  |    |    |    |    |    |    |
|  Falcon 2.0  | /link/falcon/  |  0.3625  |  0.4462  |  0.4  |  0.3857  |  0.4263  |  0.405  |
|  OpenTapioca  | /link/opentapioca/  |  0.4308  |  0.56  |  0.487  |  0.5658  |  0.4526  |  0.5029  |