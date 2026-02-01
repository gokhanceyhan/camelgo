"""Implements the Game state for CamelUp."""

from collections import defaultdict
from typing import ClassVar, Dict, Optional, List, OrderedDict

import numpy as np
from pydantic import BaseModel, model_validator

from camelgo.domain.environment.action import Action
from camelgo.domain.environment.camel import Camel
from camelgo.domain.environment.game_config import GameConfig, Color
from camelgo.domain.environment.leg import Leg
from camelgo.domain.environment.player import Player
from camelgo.domain.environment.dice import DiceRoller, Dice

class Game(BaseModel):
    """
    Stores the game state of a CamelUp game.
    """
    model_config = {'arbitrary_types_allowed': True}

    NUM_ACTIONS: ClassVar[int] = 48  # Total number of possible actions

    dice_roller: DiceRoller
    players: OrderedDict[str, Player]  # Map of player names to player states
    next_leg_starting_player: str
    current_leg: Leg
    legs_played: int = 0
    finished: bool = False

    # the following two states are hidden
    hidden_game_winner_bets: Dict[Color, List[str]] = defaultdict(list)  # camel color -> list of player names (first player bets first) who bet on it to win
    hidden_game_loser_bets: Dict[Color, List[str]] = defaultdict(list)   # camel color -> list of player names (first player bets first) who bet on it to lose

    @model_validator(mode="after")
    def ensure_defaultdicts(self):
        if not isinstance(self.hidden_game_winner_bets, defaultdict):
            self.hidden_game_winner_bets = defaultdict(list, self.hidden_game_winner_bets)
        if not isinstance(self.hidden_game_loser_bets, defaultdict):
            self.hidden_game_loser_bets = defaultdict(list, self.hidden_game_loser_bets)
        return self

    def _distribute_leg_points(self):
        # determine camels' positions in the leg
        camels_in_order = sorted(
            [c for c in self.current_leg.camel_states.values() if not c.is_crazy()],
            key=lambda c: (c.track_pos, c.stack_pos),
            reverse=True
        )

        for player in self.players.values():
            # distribute leg bets
            for camel_color, bets in self.current_leg.player_bets[player.name].items():
                camel = self.current_leg.camel_states.get(camel_color)
                if not camel:
                    # this should not happen
                    continue
                camel_position = camels_in_order.index(camel) + 1  # 1-based position
                if camel_position == 1:
                    player.add_points(sum(bets))
                elif camel_position == 2:
                    player.add_points(len(bets))
                else:
                    player.add_points(max(-player.points, -len(bets)))
            # collect points from dice rolls and tiles
            player.add_points(self.current_leg.leg_points[player.name])

    def _distribute_game_points(self):
        winner_camel = self.first_camel()
        loser_camel = self.last_camel()
        # distribute points to the players who knew winner or the loser camel
        winner_points = GameConfig.CORRECT_GAME_BET_POINTS[:]
        for player_name in self.hidden_game_winner_bets.get(winner_camel.color, []):
            player = self.players[player_name]
            player.add_points(winner_points.pop(0) if winner_points else 0)
        loser_points = GameConfig.CORRECT_GAME_BET_POINTS[:]
        for player_name in self.hidden_game_loser_bets.get(loser_camel.color, []):
            player = self.players[player_name]
            player.add_points(loser_points.pop(0) if loser_points else 0)
        # collect penalty points from the players who bet on the wrong camels
        for camel_color, player_names in self.hidden_game_winner_bets.items():
            if camel_color == winner_camel.color:
                continue
            for player_name in player_names:
                player = self.players[player_name]
                player.add_points(max(-player.points, -GameConfig.INCORRECT_GAME_BET_PENALTY))
        for camel_color, player_names in self.hidden_game_loser_bets.items():
            if camel_color == loser_camel.color:
                continue
            for player_name in player_names:
                player = self.players[player_name]
                player.add_points(max(-player.points, -GameConfig.INCORRECT_GAME_BET_PENALTY))

    @classmethod
    def _find_camel_start_positions(cls, 
                                    dice_roller: DiceRoller) -> List[Camel]:
        # roll the dices to determine starting positions of camels
        dice_roller.reset()
        for i in range(len(DiceRoller.DICE_COLORS)):
            dice_roller.roll_dice()
        dices_rolled = dice_roller.dices_rolled[:]
        # find first grey dice color
        first_grey_dice = next(d for d in dice_roller.dices_rolled if d.color == Color.WHITE or d.color == Color.BLACK)
        second_grey_dice = dice_roller.roll_grey_dice()
        if first_grey_dice.color == Color.WHITE:
            second_grey_dice = Dice(base_color=Color.GREY, number=second_grey_dice.number, number_color=Color.BLACK)
        else:
            second_grey_dice = Dice(base_color=Color.GREY, number=second_grey_dice.number, number_color=Color.WHITE)
        dices_rolled.append(second_grey_dice)
        dice_roller.reset()

        camels = []
        stacks = {i: 0 for i in range(1, GameConfig.BOARD_SIZE + 1)}
        for dice in dices_rolled:
            track_pos = dice.number if not GameConfig.is_camel_crazy(dice.color) else GameConfig.BOARD_SIZE - dice.number + 1
            stack_pos = stacks[track_pos]
            camels.append(Camel(color=dice.color, track_pos=track_pos, stack_pos=stack_pos))
            stacks[track_pos] += 1  # Increment stack position for that tile
        return camels

    def _move_to_next_leg_starting_player(self):
        player_names = list(self.players.keys())
        current_index = player_names.index(self.next_leg_starting_player)
        next_index = (current_index + 1) % len(player_names)
        self.next_leg_starting_player = player_names[next_index]

    @classmethod
    def start_game(cls, 
                   player_names: List[str], 
                   starting_player_index: int = 0, 
                   dice_roller: DiceRoller=None) -> 'Game':
        dice_roller = dice_roller or DiceRoller()
        players = {p: Player(name=p) for p in player_names}
        camels = cls._find_camel_start_positions(dice_roller)
        return cls(
            dice_roller=dice_roller,
            players=players,
            current_leg=Leg(
                leg_number=1,
                players=players,
                camel_states={camel.color: camel for camel in camels},
                next_player=player_names[starting_player_index]
            ),
            next_leg_starting_player=player_names[starting_player_index]
        )
    
    def roll_dice(self) -> Dice:
        return self.dice_roller.roll_dice()
    
    def leg_finished(self) -> bool:
        return len(self.dice_roller.remaining_colors()) <= 1

    def move_to_next_leg(self):
        self._distribute_leg_points()
        self.legs_played += 1
        self.current_leg.next(self.next_leg_starting_player)
        self._move_to_next_leg_starting_player()
        self.dice_roller.reset()
        
    def finish_game(self):
        self._distribute_leg_points()
        self.legs_played += 1
        self._distribute_game_points()
        self.finished = True

    def play_action(self, action: Action) -> bool:
        """
        Play an action in the game.
        Args:
            action (Action): The action to be played.
        Returns:
            bool: True if the game is finished after the action, False otherwise.
        """
        # Action 1: Player rolls a dice
        if action.dice_rolled is not None:
            game_finished = self.current_leg.play_action(action)
            if game_finished:
                self.finish_game()
                return True
            if self.leg_finished():
                self.move_to_next_leg()
            return False
        # Action 2: Player places cheering or booing tile
        if action.cheering_tile_placed is not None:
            self.current_leg.play_action(action)
            return False
        if action.booing_tile_placed is not None:
            self.current_leg.play_action(action)
            return False
        # Action 3: Player places leg bet
        if action.leg_bet is not None:
            self.current_leg.play_action(action)
            return False
        # The following two actions are hidden from other players
        # These actions do not use the play_action method of Leg, 
        # hence moving the next player is handled here.
        # Action 4: Player places game winner bet
        if action.game_winner_bet is not None:
            self.hidden_game_winner_bets[action.game_winner_bet].append(action.player)
            self.current_leg.move_to_next_player()
            return False
        # Action 5: Player places game loser bet
        if action.game_loser_bet is not None:
            self.hidden_game_loser_bets[action.game_loser_bet].append(action.player)
            self.current_leg.move_to_next_player()
            return False
        
    def first_camel(self) -> Camel:
        camels_in_order = sorted(
            [c for c in self.current_leg.camel_states.values() if not c.is_crazy()],
            key=lambda c: (c.track_pos, c.stack_pos),
            reverse=True
        )
        return camels_in_order[0]

    def last_camel(self) -> Camel:
        camels_in_order = sorted(
            [c for c in self.current_leg.camel_states.values() if not c.is_crazy()],
            key=lambda c: (c.track_pos, c.stack_pos),
            reverse=False
        )
        return camels_in_order[0]
    
    def current_player_points(self, player_name: str) -> int:
        player = self.players[player_name]
        if self.finished:
            # legs points have already been distributed
            return player.points
        # because leg points are only distributed at the end of the leg
        return player.points + self.current_leg.leg_points[player_name]
    
    def winner_player(self) -> Optional[Player]:
        if not self.finished:
            return None
        return max(self.players.values(), key=lambda p: p.points)

    def reset(self):
        self.dice_roller.reset()
        self.players = {p: Player(name=p) for p in self.players.keys()}
        self.legs_played = 0
        self.current_leg = Leg(
            leg_number=1,
            players=self.players,
            camel_states={camel.color: camel for camel in Game._find_camel_start_positions(self.dice_roller)}
        )
        self.next_leg_starting_player = 0
        self.hidden_game_winner_bets = defaultdict(list)
        self.hidden_game_loser_bets = defaultdict(list)

    def get_action_mask(self, player_name) -> np.ndarray:
        # 1=Valid, 0=Invalid
        mask = np.ones(Game.NUM_ACTIONS, dtype=bool)
        
        # 0: Roll Dice (Valid unless leg ended, but step handles that. Always valid if turn exists)
        
        # 1-5: Leg Bets
        # Check if tickets available for color
        for i, color in enumerate(GameConfig.CAMEL_COLORS):
            # Count total bets
            count = 0 
            for p in self.players.values():
                count += len(self.current_leg.player_bets[p.name][color])
            if count >= 4: # 5,3,2,2
                mask[1+i] = False
                
        # 6-10: Game Win (One per color per player)
        # Logic: Can usually bet once per turn. Always valid if not already bet
        for i, color in enumerate(GameConfig.CAMEL_COLORS):
            if player_name in self.hidden_game_winner_bets[color]:
                mask[6+i] = False

        # 11-15: Game Lose (Same logic as above)
        for i, color in enumerate(GameConfig.CAMEL_COLORS):
            if player_name in self.hidden_game_loser_bets[color]:
                mask[11+i] = False
        
        # 16-47: Tiles
        # Indices: Cheer (16-31) -> pos (1-16). Boo (32-47).
        # TODO: no need for having for both cheer and boo separately.
        
        # A player can place only one tile per leg
        tile_played_players = {p for _, p in self.current_leg.cheering_tiles} | \
            {p for _, p in self.current_leg.booing_tiles}
        if player_name in tile_played_players:
            mask[16:48] = [False] * 32
        
        # Invalid if occupied by camel or existing tile
        # Also adjacent rule: cannot place on X if X-1 or X+1 has a tile
        camel_positions = {
            c.track_pos for c in self.current_leg.camel_states.values()}
        
        tile_positions = {pos for pos, _ in self.current_leg.cheering_tiles} | \
            {pos for pos, _ in self.current_leg.booing_tiles}
                   
        for pos in range(1, 17):
            is_invalid = (pos in camel_positions) or (pos in tile_positions) or \
                (pos - 1 in tile_positions) or (pos + 1 in tile_positions)
            if is_invalid:
                mask[16 + (pos-1)] = False
                mask[32 + (pos-1)] = False
                
        return mask

