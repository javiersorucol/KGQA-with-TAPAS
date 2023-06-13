from pydantic import BaseModel
from typing import Optional, List

class QALD_json_question_DTO(BaseModel):
    language : str
    string : str

class QALD_json_answer_DTO(BaseModel):
    head : dict
    results : dict

class QALD_json_element_DTO(BaseModel):
    id : str
    question : List[QALD_json_question_DTO]
    query : Optional[dict] = {}
    answers : Optional[List[QALD_json_answer_DTO]] = []

class QALD_json_DTO(BaseModel):
    questions : List[QALD_json_element_DTO]