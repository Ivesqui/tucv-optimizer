from pydantic import BaseModel, Field
from typing import List, Optional

class ProjectSchema(BaseModel):
    title: str = Field(default="")
    description: str = Field(default="")
    link: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)