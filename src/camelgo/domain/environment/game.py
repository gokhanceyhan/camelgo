from pydantic import BaseModel
from typing import Dict, Optional, List

from camelgo.domain.environment.camel import CamelState
from camelgo.domain.environment.game_config import GameConfig
from camelgo.domain.environment.leg import LegState
from camelgo.domain.environment.player import PlayerState

class GameState(BaseModel):
    """
    Stores the game state of a CamelUp game.
    """
    players: List[PlayerState] = []  # List of player states
    legs_played: int = 0
    current_leg: LegState
    next_leg_player: Optional[int] = None  # Player index to start next leg

    @classmethod
    def start_from(cls, 
                   players: List[str], 
                   dices_rolled: List[tuple[str, int]],
                   starting_player_index: int = 0) -> 'GameState':
        
        players=[PlayerState(name=p) for p in players]
        camels = []
        stacks = {i: 0 for i in range(1, GameConfig.BOARD_SIZE + 1)}
        for color, value in dices_rolled:
            track_pos = value if not GameConfig.is_camel_crazy(color) else GameConfig.BOARD_SIZE - value + 1
            stack_pos = stacks[track_pos]
            camels.append(CamelState(color=color, track_pos=track_pos, stack_pos=stack_pos))
            stacks[track_pos] += 1  # Increment stack position for that tile
        
        return cls(
            players=players,
            current_leg=LegState(
                camel_states={camel.color: camel for camel in camels}),
            next_leg_player=starting_player_index
        )
