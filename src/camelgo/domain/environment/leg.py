from collections import defaultdict
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple

from camelgo.domain.environment.camel import Camel
from camelgo.domain.environment.dice import Dice
from camelgo.domain.environment.game_config import GameConfig

class Leg(BaseModel):
    leg_number: int = 1  # Which leg of the game (1, 2, ...)
    camel_states: Dict[str, Camel]

    # reset the following at the start of each leg
    cheering_tiles: List[Tuple[int, str]] = []  # Position and players of the cheering tiles, if placed
    booming_tiles: List[Tuple[int, str]] = []  # Position and players of the booming tiles, if placed
    leg_points: Dict[str, int] = defaultdict(int)  # player -> points earned in this leg from dice rolls and tiles
    player_bets: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))  # player -> color -> bets to win the leg

    def move_camel(self, dice: Dice, player: str) -> bool:
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
        next_pos = camel.track_pos + dice.value if not camel.is_crazy() else camel.track_pos - dice.value
        final_pos = next_pos
        if self.cheering_tiles and next_pos in [pos for pos, _ in self.cheering_tiles]:
            final_pos += 1 if not camel.is_crazy() else -1
            point_for_player = [player for pos, player in self.cheering_tiles if pos == next_pos][0]
            self.leg_points[point_for_player] += 1  # Award 1 point to the player who placed the cheering tile
        boomed = False
        if self.booming_tiles and next_pos in [pos for pos, _ in self.booming_tiles]:
            boomed = True
            final_pos += 1 if camel.is_crazy() else -1
            point_for_player = [player for pos, player in self.booming_tiles if pos == next_pos][0]
            self.leg_points[point_for_player] += 1  # Award 1 point to the player who placed the booming tile

        on_camels = [c for c in self.camel_states.values() if c.color != dice.color and c.track_pos == final_pos]
        if on_camels:
            if not boomed:
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

    def place_tile(self, position: int, player: str, cheering: bool = True) -> None:
        # rules:
        # 1. The position must be within the board limits.
        if position < 1 or position > GameConfig.BOARD_SIZE:
            raise ValueError(f"Tile position must be between 1 and {GameConfig.BOARD_SIZE}.")
        # 2. It cannot be place on a tile already occupied by a camel.
        camel_tiles = {c.track_pos for c in self.camel_states.values()}
        if position in camel_tiles:
            raise ValueError("Cannot place a tile on a tile occupied by a camel.")
        # 3. It cannot be placed on or besides an already existing tile
        existing_tile_pos = [pos for pos, _ in (self.cheering_tiles + self.booming_tiles)]
        if existing_tile_pos and any(abs(pos - position) <= 1 for pos in existing_tile_pos):
            raise ValueError("Cannot place a tile on or beside an existing tile.")
        if cheering:
            self.cheering_tiles.append((position, player))
        else:
            self.booming_tiles.append((position, player))

    def bet_camel_wins_leg(self, camel_color: str, player: str) -> None:
        camel = self.camel_states.get(camel_color)
        if not camel:
            raise ValueError(f"No camel exists with color {camel_color}.")
        bet_value = camel.bet()
        self.player_bets[player][camel_color].append(bet_value)

    def reset_leg(self) -> None:
        self.cheering_tiles = []
        self.booming_tiles = []
        self.leg_points = defaultdict(int)
        self.player_bets = defaultdict(lambda: defaultdict(list))
        for camel in self.camel_states.values():
            camel.reset_for_new_leg()

    def next(self) -> None:
        self.reset_leg()
        self.leg_number += 1
