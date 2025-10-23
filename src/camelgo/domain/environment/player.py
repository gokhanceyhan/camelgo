from pydantic import BaseModel

from camelgo.domain.environment.game_config import GameConfig

class Player(BaseModel):
    name: str  # Player's name
    points: int = GameConfig.STARTING_MONEY  # Player's current points
