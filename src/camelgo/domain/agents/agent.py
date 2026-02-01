"""Abstract base class for player agents in the game."""

from abc import ABC, abstractmethod

from camelgo.domain.environment.game import Game
from camelgo.domain.environment.action import Action


class Agent(ABC):
    """Abstract base class for player agents in the game."""

    @abstractmethod
    def play(self, game: Game) -> Action:
        """Decide on an action to take given the current game state.

        Args:
            game (Game): The current state of the game.

        Returns:
            Action: The action chosen by the agent.
        """
        pass