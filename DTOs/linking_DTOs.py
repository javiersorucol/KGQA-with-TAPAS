from pydantic import BaseModel

class Linked_Data_DTO(BaseModel):
    entities : list

class Question_DTO(BaseModel):
    text: str