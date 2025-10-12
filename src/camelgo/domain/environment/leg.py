from pydantic import BaseModel
from typing import Dict, List, Optional

from camelgo.domain.environment.camel import CamelState

class LegState(BaseModel):
    leg_number: int = 1  # Which leg of the game (1, 2, ...)
    camel_states: Dict[str, CamelState]
    cheering_tile_position: Optional[int] = None  # Position of the cheering tile, if placed
    booming_tile_position: Optional[int] = None  # Position of the booming tile, if placed

    
    
    
