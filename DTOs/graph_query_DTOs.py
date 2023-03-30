from pydantic import BaseModel
from typing import Optional, List
from typing_extensions import TypedDict

class Table_template_property_DTO(BaseModel):
    UID: str
    label: str
    type: str

class Table_template_DTO(BaseModel):
    UID: str
    properties: List[Table_template_property_DTO]

class Table_templates_DTO(BaseModel):
    templates: List[Table_template_DTO]
    entities_UIDs: List[str]
