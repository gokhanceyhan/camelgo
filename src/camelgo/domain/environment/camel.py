from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional

from camelgo.domain.environment.game_config import GameConfig

class Camel(BaseModel):
    color: str  # Unique identifier for the camel (e.g., 'blue', 'yellow')
    track_pos: int  # Current position on the board (tile index, 1-16)
    stack_pos: int  # Stack order (0 = bottom, higher = on top)

    # below fields need to be reset at the start of each leg
    available_bets: List[int] = GameConfig.BET_VALUES  # Next bet values for this camel (5, 3, 2, 2)
    dice_value: Optional[int] = None  # Result of the camel's dice roll (1-3), None if not rolled yet
    finished: bool = False  # Whether the camel has finished the race

    def _set_track_pos(self, track_pos: int):
        if track_pos > GameConfig.BOARD_SIZE:
            # this means game is finished
            self.track_pos = track_pos
            self.finished = True
        elif track_pos < 1:
            # this means a crazy camel was able to make a complete tour
            # not sure if this is possible though
            # if so, lets reset its position
            self.track_pos = GameConfig.BOARD_SIZE
        else:
            self.track_pos = track_pos

    def is_crazy(self) -> bool:
        return self.color in GameConfig.CRAZY_CAMELS

    def move(self, track_pos: int, stack_pos: int = 0) -> None:
        self._set_track_pos(track_pos)
        self.stack_pos = stack_pos

    def bet(self) -> Optional[int]:
        if self.available_bets:
            next_bet = self.available_bets[0]
            self.available_bets = self.available_bets[1:] if len(self.available_bets) > 1 else []
            return next_bet
        raise ValueError(f"No more bets available for camel {self.color}.")
    
    def dice_rolled(self, value: int) -> None:
        self.dice_value = value

    def reset_for_new_leg(self) -> None:
        self.available_bets = GameConfig.BET_VALUES
        self.dice_value = None
