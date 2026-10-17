from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum

class ComponentType(str, Enum):
    RESISTOR = "resistor"
    BATTERY = "battery"
    BULB = "bulb"
    WIRE = "wire"

class ComponentModel(BaseModel):
    id: str = Field(..., description="Unique identifier for the component (e.g., R1, B1)")
    type: ComponentType = Field(..., description="Type of the electrical component")
    value: float = Field(..., description="Numerical value (Resistance in ohms or Voltage in Volts)")
    unit: str = Field(..., description="Unit of measurement (e.g., 'ohm', 'V')")
    terminals: List[str] = Field(default=["1", "2"], description="The connection points of the component")

class ConnectionModel(BaseModel):
    from_comp: str = Field(..., description="ID of the starting component")
    from_terminal: str = Field(..., description="Terminal ID of the starting component")
    to_comp: str = Field(..., description="ID of the ending component")
    to_terminal: str = Field(..., description="Terminal ID of the ending component")

class CircuitModel(BaseModel):
    circuit_id: Optional[str] = None
    components: List[ComponentModel] = Field(default_factory=list)
    connections: List[ConnectionModel] = Field(default_factory=list)
    metadata: Optional[dict] = None
