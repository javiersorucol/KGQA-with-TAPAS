from pydantic import BaseModel

class Linked_data_DTO(BaseModel):
    entity_list : list
    relations_list : list

class Question_DTO(BaseModel):
    text: str