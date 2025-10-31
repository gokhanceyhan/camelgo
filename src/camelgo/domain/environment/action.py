from pydantic import BaseModel
from typing import Optional

from camelgo.domain.environment.dice import Dice

class Action(BaseModel):
	player: str  # Player performing the action
	dice_rolled: Optional[Dice] = None
	cheering_tile_placed: Optional[int] = None # track position where cheering tile is placed
	booing_tile_placed: Optional[int] = None # track position where booing tile is placed
	leg_bet: Optional[str] = None # color of the camel the player bets to win the leg
	game_winner_bet: Optional[str] = None # color of the camel the player bets to win the game
	game_loser_bet: Optional[str] = None # color of the camel the player bets to lose the game
