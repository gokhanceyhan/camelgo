"""Implements random-playing player agent in the game."""

import numpy as np

from camelgo.domain.agents.agent import Agent
from camelgo.domain.environment.action import Action
from camelgo.domain.environment.game import Game


class RandomPlayerAgent(Agent):
    
    """A player agent that selects moves randomly."""

    def __init__(self, name=None):
        self.name = name or "RandomPlayer"

    def play(self, game: Game) -> Action:
        # Random Move
        valid_actions = game.get_action_mask(self.name)
        valid_indices = np.where(valid_actions)[0]
        if len(valid_indices) == 0:
            # No moves? Should not happen.
            raise ValueError("No valid actions available for a player, should not happen.")
                
        idx = np.random.choice(valid_indices)
        return Action.from_int(idx, self.name)