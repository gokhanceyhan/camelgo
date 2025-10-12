from typing import Dict, List, Optional

from camelgo.domain.environment.camel import CamelState
from .game import GameState
from .leg import LegState
from .player import PlayerState

class StateManager:
    def __init__(self):
        self._game_state = None

    def game_state(self) -> Optional[GameState]:
        return self._game_state

    def start_game(self, 
                   players: List[str], 
                   dices_rolled: List[tuple[str, int]],
                   starting_player_index: int = 0):
        """
        Initialize and start a new game.

        Args:
            players (List[str]): List of player names.
            dices_rolled (List[Tuple[str, int]]): List of tuples representing dice rolls (camel color, value).
            starting_player_index (int, optional): Index of the player who starts the game. Defaults to 0.

        Sets up the initial game state using the provided players and dice rolls.
        """
        self._game_state = GameState.start_from(
            players=players,
            dices_rolled=dices_rolled,
            starting_player_index=starting_player_index
        )

    def start_next_leg(self):
        pass

    def finish_current_leg(self):
        pass

    def finish_game(self):
        pass

