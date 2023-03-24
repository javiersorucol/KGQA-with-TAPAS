from pydantic import BaseModel

class Table_DTO(BaseModel):
    question: str
    table: dict