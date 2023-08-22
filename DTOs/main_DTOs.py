from pydantic import BaseModel

class QUERY_DTO(BaseModel):
    text: str
    lang: str

class FINAL_ANSWER_DTO(BaseModel):
    answer : str
    linked_elements : dict