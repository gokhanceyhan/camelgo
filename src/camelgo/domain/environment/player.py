from pydantic import BaseModel

from camelgo.domain.environment.game_config import GameConfig

class Player(BaseModel):
    name: str  # Player's name
    points: int = GameConfig.STARTING_MONEY  # Player's current points

    def add_points(self, amount: int):
        """Add points to the player's total."""
        self.points += amount
