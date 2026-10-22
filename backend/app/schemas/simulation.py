from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CircuitModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Optional[str] = None
    components: List[Dict[str, Any]] = Field(default_factory=list)
    connections: List[Dict[str, Any]] = Field(default_factory=list)


class CircuitData(BaseModel):
    """Vision-shaped data object shared by analysis and simulation endpoints."""

    model_config = ConfigDict(extra="allow")

    problem: Optional[Dict[str, Any]] = None
    circuit: CircuitModel
    visual: Optional[Dict[str, Any]] = None
