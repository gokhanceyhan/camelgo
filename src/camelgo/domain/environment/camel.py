from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

from camelgo.domain.environment.game_config import GameConfig

class CamelState(BaseModel):
    color: str  # Unique identifier for the camel (e.g., 'blue', 'yellow')
    track_pos: int  # Current position on the board (tile index, 1-16)
    stack_pos: int  # Stack order (0 = bottom, higher = on top)
    next_bet: int = GameConfig.BET_VALUES[0]  # Next bet value for this camel (5, 3, 2, 2)
    dice_value: Optional[int] = None  # Result of the camel's dice roll (1-3), None if not rolled yet

    def is_crazy(self) -> bool:
        return self.color in GameConfig.CRAZY_CAMELS


