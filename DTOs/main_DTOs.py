from pydantic import BaseModel


class QUERY_DTO(BaseModel):
    text: str
    lang: str