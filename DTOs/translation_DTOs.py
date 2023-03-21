from pydantic import BaseModel

class Question_DTO(BaseModel):
    text: str
    mode: str