from pydantic import BaseModel

class Table_DTO(BaseModel):
    question: str
    table: dict

class Triples_DTO(BaseModel):
    question : str
    triples : str

class Answer_DTO(BaseModel):
    answer : str