# KGQA-with-TAPAS
Using TeBaQA to create a KGQA pipeline. The main idea is to transfor a KGQA problem to  QA over tables problem,  then use TAPAS to find an answer. We aim to achieve this by creating relevant tables for each question based on the class of all the question's entities.

This project is designed using a microservice architechture, we work with the followin microservices:
- Translation Service
- Entity linking Service
- Answer service
- Graph query service (currently  working with Wikidata)
- Classification service
- Main API

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