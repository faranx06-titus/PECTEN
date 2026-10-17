from pydantic import BaseModel, Field
from typing import List, Optional

class ParsedElement(BaseModel):
    label: str = Field(..., description="The label found in the diagram (e.g., 'R1')")
    type: str = Field(..., description="The inferred type of the element")
    value: Optional[float] = None
    coordinates: Optional[List[float]] = None

class QuestionParserModel(BaseModel):
    raw_text: str = Field(..., description="The original question text")
    extracted_elements: List[ParsedElement] = Field(default_factory=list)
    goal: str = Field(..., description="What the user wants to calculate (e.g., 'total current')")
    constraints: List[str] = Field(default_factory=list, description="Given conditions or constraints")
