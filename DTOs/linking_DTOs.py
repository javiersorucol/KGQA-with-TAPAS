from pydantic import BaseModel
from typing import Optional

class Linked_data_DTO(BaseModel):
    entity_list : list
    relations_list : list

class Question_DTO(BaseModel):
    text: str
    mode: Optional[str] = None