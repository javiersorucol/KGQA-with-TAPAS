from typing import Optional
from pydantic import BaseModel

class Entity_Table_DTO(BaseModel):
    labels_table : dict
    uri_table : dict

class Entity_Triples_DTO(BaseModel):
    triples : str
    data_corpus: Optional[str] = None