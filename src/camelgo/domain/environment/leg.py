from collections import defaultdict
from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Optional, OrderedDict, Tuple, Any

from camelgo.domain.environment.action import Action
from camelgo.domain.environment.camel import Camel
from camelgo.domain.environment.dice import Dice
from camelgo.domain.environment.game_config import GameConfig
from camelgo.domain.environment.player import Player

class Leg(BaseModel):
    leg_number: int = 1  # Which leg of the game (1, 2, ...)
    players: OrderedDict[str, Player]  # Map of player names to player states
    camel_states: Dict[str, Camel]

    # reset the following at the start of each leg
    cheering_tiles: List[Tuple[int, str]] = Field(default_factory=list)  # Position and players of the cheering tiles, if placed
    booing_tiles: List[Tuple[int, str]] = Field(default_factory=list)  # Position and players of the booing tiles, if placed
    leg_points: Dict[str, int] = Field(default_factory=lambda: defaultdict(int))  # player -> points earned in this leg from dice rolls and tiles
    player_bets: Dict[str, Dict[str, List[int]]] = Field(default_factory=lambda: defaultdict(lambda: defaultdict(list)))  # player -> color -> bets to win the leg
    next_player: Optional[str] = None  # Player whose turn it is to play the next action

    @model_validator(mode="after")
    def ensure_defaultdicts(self):
        if not isinstance(self.leg_points, defaultdict):
            self.leg_points = defaultdict(int, self.leg_points)
        if not isinstance(self.player_bets, defaultdict):
            self.player_bets = defaultdict(lambda: defaultdict(list), {
                k: defaultdict(list, v) for k, v in self.player_bets.items()
            })
        return self

    def _move_to_next_player(self):
        player_names = list(self.players.keys())
        current_index = player_names.index(self.next_player) if self.next_player else 0
        self.next_player = player_names[(current_index + 1) % len(player_names)]

    def _move_camel(self, dice: Dice, player: str) -> bool:
        """
        Move a camel by a certain number of tiles.

        Args:
            dice (Dice): The dice rolled for the camel to move.

        Returns:
            bool: True if the game is finished, False otherwise.
        """
        if dice.color not in self.camel_states:
            raise ValueError(f"No camel exists with color {dice.color}.")
        camel = self.camel_states[dice.color]
        if camel.dice_value is not None:
            raise ValueError(f"Camel {dice.color} has already rolled its dice this leg.")
        
        # give one point to the player who rolled the dice
        self.leg_points[player] += 1

        # camels on top of the moving camel also move
        moving_stack = [c for c in self.camel_states.values() if c.track_pos == camel.track_pos and c.stack_pos >= camel.stack_pos]
        
        # find the new position
        next_pos = camel.track_pos + dice.number if not camel.is_crazy() else camel.track_pos - dice.number
        final_pos = next_pos
        if self.cheering_tiles and next_pos in [pos for pos, _ in self.cheering_tiles]:
            final_pos += 1 if not camel.is_crazy() else -1
            point_for_player = [player for pos, player in self.cheering_tiles if pos == next_pos][0]
            self.leg_points[point_for_player] += 1  # Award 1 point to the player who placed the cheering tile
        booed = False
        if self.booing_tiles and next_pos in [pos for pos, _ in self.booing_tiles]:
            booed = True
            final_pos += 1 if camel.is_crazy() else -1
            point_for_player = [player for pos, player in self.booing_tiles if pos == next_pos][0]
            self.leg_points[point_for_player] += 1  # Award 1 point to the player who placed the booing tile

        on_camels = [c for c in self.camel_states.values() if c.color != dice.color and c.track_pos == final_pos]
        if on_camels:
            if not booed:
                # stack on top of the existing camels
                max_stack_pos = max(c.stack_pos for c in on_camels)
                for idx, c in enumerate(moving_stack):
                    c.move(track_pos=final_pos, stack_pos=max_stack_pos + 1 + idx)
            else:
                # go under the existing camels
                # reset the stack positions of the moving camels
                for idx, c in enumerate(moving_stack):
                    c.move(track_pos=final_pos, stack_pos=idx)
                # update the stack positions of the existing camels
                for idx, c in enumerate(on_camels):
                    c.move(track_pos=c.track_pos, stack_pos=idx + len(moving_stack))
        else:
            # move to the new position, reset stack positions
            for idx, c in enumerate(moving_stack):
                c.move(track_pos=final_pos, stack_pos=idx)
        # check if game is finished
        if final_pos > GameConfig.BOARD_SIZE:
            return True
        return False

    def _place_tile(self, position: int, player: str, cheering: bool = True) -> None:
        # rules:
        # 1. The position must be within the board limits.
        if position < 1 or position > GameConfig.BOARD_SIZE:
            raise ValueError(f"Tile position must be between 1 and {GameConfig.BOARD_SIZE}.")
        # 2. It cannot be place on a tile already occupied by a camel.
        camel_tiles = {c.track_pos for c in self.camel_states.values()}
        if position in camel_tiles:
            raise ValueError("Cannot place a tile on a tile occupied by a camel.")
        # 3. It cannot be placed on or besides an already existing tile
        existing_tile_pos = [pos for pos, _ in (self.cheering_tiles + self.booing_tiles)]
        if existing_tile_pos and any(abs(pos - position) <= 1 for pos in existing_tile_pos):
            raise ValueError("Cannot place a tile on or beside an existing tile.")
        if cheering:
            self.cheering_tiles.append((position, player))
        else:
            self.booing_tiles.append((position, player))

    def _bet_camel_wins_leg(self, camel_color: str, player: str) -> None:
        camel = self.camel_states.get(camel_color)
        if not camel:
            raise ValueError(f"No camel exists with color {camel_color}.")
        bet_value = camel.bet()
        self.player_bets[player][camel_color].append(bet_value)

    def play_action(self, action: Action) -> Any:
        action_return = None
        if action.dice_rolled:
            action_return = self._move_camel(action.dice_rolled, action.player)
        if action.cheering_tile_placed is not None:
            action_return = self._place_tile(action.cheering_tile_placed, action.player, cheering=True)
        if action.booing_tile_placed is not None:
            action_return = self._place_tile(action.booing_tile_placed, action.player, cheering=False)
        if action.leg_bet is not None:
            action_return = self._bet_camel_wins_leg(action.leg_bet, action.player)
        self._move_to_next_player()
        return action_return

    def reset_leg(self) -> None:
        self.cheering_tiles = []
        self.booing_tiles = []
        self.leg_points = defaultdict(int)
        self.player_bets = defaultdict(lambda: defaultdict(list))
        for camel in self.camel_states.values():
            camel.reset_for_new_leg()

    def next(self, starting_player: str) -> None:
        self.reset_leg()
        self.leg_number += 1
        self.next_player = starting_player
