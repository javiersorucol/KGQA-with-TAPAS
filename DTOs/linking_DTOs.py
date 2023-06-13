from pydantic import BaseModel

class Linked_data_DTO(BaseModel):
    entities : list
    relations : list

class Question_DTO(BaseModel):
    text: str