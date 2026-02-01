"""Implements the Action classes for representing player actions in the game."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from camelgo.domain.environment.dice import Dice
from camelgo.domain.environment.game_config import Color


class ActionInt(Enum):
	ROLL_DICE = 0
	LEG_BET_BLUE = 1
	LEG_BET_YELLOW = 2
	LEG_BET_GREEN = 3
	LEG_BET_PURPLE = 4
	LEG_BET_RED = 5
	GAME_WINNER_BET_BLUE = 6
	GAME_WINNER_BET_YELLOW = 7
	GAME_WINNER_BET_GREEN = 8
	GAME_WINNER_BET_PURPLE = 9
	GAME_WINNER_BET_RED = 10
	GAME_LOSER_BET_BLUE = 11
	GAME_LOSER_BET_YELLOW = 12
	GAME_LOSER_BET_GREEN = 13
	GAME_LOSER_BET_PURPLE = 14
	GAME_LOSER_BET_RED = 15
	CHEERING_TILE_POS_1 = 16
	CHEERING_TILE_POS_2 = 17
	CHEERING_TILE_POS_3 = 18
	CHEERING_TILE_POS_4 = 19
	CHEERING_TILE_POS_5 = 20
	CHEERING_TILE_POS_6 = 21
	CHEERING_TILE_POS_7 = 22
	CHEERING_TILE_POS_8 = 23
	CHEERING_TILE_POS_9 = 24
	CHEERING_TILE_POS_10 = 25
	CHEERING_TILE_POS_11 = 26
	CHEERING_TILE_POS_12 = 27
	CHEERING_TILE_POS_13 = 28
	CHEERING_TILE_POS_14 = 29
	CHEERING_TILE_POS_15 = 30
	CHEERING_TILE_POS_16 = 31
	BOOING_TILE_POS_1 = 32
	BOOING_TILE_POS_2 = 33
	BOOING_TILE_POS_3 = 34
	BOOING_TILE_POS_4 = 35
	BOOING_TILE_POS_5 = 36
	BOOING_TILE_POS_6 = 37
	BOOING_TILE_POS_7 = 38
	BOOING_TILE_POS_8 = 39
	BOOING_TILE_POS_9 = 40
	BOOING_TILE_POS_10 = 41
	BOOING_TILE_POS_11 = 42
	BOOING_TILE_POS_12 = 43
	BOOING_TILE_POS_13 = 44
	BOOING_TILE_POS_14 = 45
	BOOING_TILE_POS_15 = 46
	BOOING_TILE_POS_16 = 47

	@classmethod
	def all_actions(cls) -> list[int]:
		return [action.value for action in ActionInt]


class Action(BaseModel):
	"""Represents a player's action in the game."""
	player: str  # Player performing the action
	# TODO: Make dice_rolled a boolean
	dice_rolled: Optional[Dice] = None
	cheering_tile_placed: Optional[int] = None # track position where cheering tile is placed
	booing_tile_placed: Optional[int] = None # track position where booing tile is placed
	leg_bet: Optional[Color] = None # color of the camel the player bets to win the leg
	game_winner_bet: Optional[Color] = None # color of the camel the player bets to win the game
	game_loser_bet: Optional[Color] = None # color of the camel the player bets to lose the game

	@classmethod
	def to_int(cls, self) -> int:
		"""Convert the action to its corresponding integer representation."""
		if self.dice_rolled is not None:
			return ActionInt.ROLL_DICE.value
		if self.leg_bet is not None:
			color_to_action = {
				Color.BLUE: ActionInt.LEG_BET_BLUE,
				Color.YELLOW: ActionInt.LEG_BET_YELLOW,
				Color.GREEN: ActionInt.LEG_BET_GREEN,
				Color.PURPLE: ActionInt.LEG_BET_PURPLE,
				Color.RED: ActionInt.LEG_BET_RED,
			}
			return color_to_action[self.leg_bet].value
		if self.game_winner_bet is not None:
			color_to_action = {
				Color.BLUE: ActionInt.GAME_WINNER_BET_BLUE,
				Color.YELLOW: ActionInt.GAME_WINNER_BET_YELLOW,
				Color.GREEN: ActionInt.GAME_WINNER_BET_GREEN,
				Color.PURPLE: ActionInt.GAME_WINNER_BET_PURPLE,
				Color.RED: ActionInt.GAME_WINNER_BET_RED,
			}
			return color_to_action[self.game_winner_bet].value
		if self.game_loser_bet is not None:
			color_to_action = {
				Color.BLUE: ActionInt.GAME_LOSER_BET_BLUE,
				Color.YELLOW: ActionInt.GAME_LOSER_BET_YELLOW,
				Color.GREEN: ActionInt.GAME_LOSER_BET_GREEN,
				Color.PURPLE: ActionInt.GAME_LOSER_BET_PURPLE,
				Color.RED: ActionInt.GAME_LOSER_BET_RED,
			}
			return color_to_action[self.game_loser_bet].value
		if self.cheering_tile_placed is not None:
			return ActionInt(f'CHEERING_TILE_POS_{self.cheering_tile_placed}').value
		if self.booing_tile_placed is not None:
			return ActionInt(f'BOOING_TILE_POS_{self.booing_tile_placed}').value
		raise ValueError("Invalid action: No valid action found.")
	
	@classmethod
	def from_int(cls, action_int: int, player: str) -> 'Action':
		"""Create an Action instance from its integer representation."""
		action_enum = ActionInt(action_int)
		if action_enum == ActionInt.ROLL_DICE:
			# TODO: Update to include dice rolled information when actual dice is moved out from action
			return Action(player=player)
		elif action_enum in {
			ActionInt.LEG_BET_BLUE, ActionInt.LEG_BET_YELLOW, ActionInt.LEG_BET_GREEN,
			ActionInt.LEG_BET_PURPLE, ActionInt.LEG_BET_RED
		}:
			color_map = {
				ActionInt.LEG_BET_BLUE: Color.BLUE,
				ActionInt.LEG_BET_YELLOW: Color.YELLOW,
				ActionInt.LEG_BET_GREEN: Color.GREEN,
				ActionInt.LEG_BET_PURPLE: Color.PURPLE,
				ActionInt.LEG_BET_RED: Color.RED,
			}
			return Action(player=player, leg_bet=color_map[action_enum])
		elif action_enum in {
			ActionInt.GAME_WINNER_BET_BLUE, ActionInt.GAME_WINNER_BET_YELLOW,
			ActionInt.GAME_WINNER_BET_GREEN, ActionInt.GAME_WINNER_BET_PURPLE,
			ActionInt.GAME_WINNER_BET_RED
		}:
			color_map = {
				ActionInt.GAME_WINNER_BET_BLUE: Color.BLUE,
				ActionInt.GAME_WINNER_BET_YELLOW: Color.YELLOW,
				ActionInt.GAME_WINNER_BET_GREEN: Color.GREEN,
				ActionInt.GAME_WINNER_BET_PURPLE: Color.PURPLE,
				ActionInt.GAME_WINNER_BET_RED: Color.RED,
			}
			return Action(player=player, game_winner_bet=color_map[action_enum])
		elif action_enum in {
			ActionInt.GAME_LOSER_BET_BLUE, ActionInt.GAME_LOSER_BET_YELLOW,
			ActionInt.GAME_LOSER_BET_GREEN, ActionInt.GAME_LOSER_BET_PURPLE,
			ActionInt.GAME_LOSER_BET_RED
		}:
			color_map = {
				ActionInt.GAME_LOSER_BET_BLUE: Color.BLUE,
				ActionInt.GAME_LOSER_BET_YELLOW: Color.YELLOW,
				ActionInt.GAME_LOSER_BET_GREEN: Color.GREEN,
				ActionInt.GAME_LOSER_BET_PURPLE: Color.PURPLE,
				ActionInt.GAME_LOSER_BET_RED: Color.RED,
			}
			return Action(player=player, game_loser_bet=color_map[action_enum])
		elif action_enum.name.startswith('CHEERING_TILE_POS_'):
			position = int(action_enum.name.split('_')[-1])
			return Action(player=player, cheering_tile_placed=position)
		elif action_enum.name.startswith('BOOING_TILE_POS_'):
			position = int(action_enum.name.split('_')[-1])
			return Action(player=player, booing_tile_placed=position)
		else:
			raise ValueError(f"Invalid action integer: {action_int}")
