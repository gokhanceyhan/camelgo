from collections import defaultdict
from pydantic import BaseModel
from typing import Dict, Optional, List

from camelgo.domain.environment.action import Action
from camelgo.domain.environment.camel import Camel
from camelgo.domain.environment.game_config import GameConfig
from camelgo.domain.environment.leg import Leg
from camelgo.domain.environment.player import Player
from camelgo.domain.environment.dice import DiceRoller, Dice

class Game(BaseModel):
    model_config = {'arbitrary_types_allowed': True}
    """
    Stores the game state of a CamelUp game.
    """
    dice_roller: DiceRoller
    players: Dict[str, Player]  # Map of player names to player states
    current_leg: Leg
    legs_played: int = 0
    next_leg_player: int = 0  # Player index to start next leg
    finished: bool = False

    # the following two states are hidden
    hidden_game_winner_bets: Dict[str, List[str]] = defaultdict(list)  # camel color -> list of player names (first player bets first) who bet on it to win
    hidden_game_loser_bets: Dict[str, List[str]] = defaultdict(list)   # camel color -> list of player names (first player bets first) who bet on it to lose

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
        first_grey_dice = next(d for d in dice_roller.dices_rolled if d.color == 'white' or d.color == 'black')
        second_grey_dice = dice_roller.roll_grey_dice()
        if first_grey_dice.color == 'white':
            second_grey_dice = Dice(color='grey', number=second_grey_dice.number, number_color='black')
        else:
            second_grey_dice = Dice(color='grey', number=second_grey_dice.number, number_color='white')
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

    @classmethod
    def start_game(cls, 
                   players: List[str], 
                   starting_player_index: int = 0, 
                   dice_roller: DiceRoller=None) -> 'Game':
        dice_roller = dice_roller or DiceRoller()
        camels = cls._find_camel_start_positions(dice_roller)
        return cls(
            dice_roller=dice_roller,
            players={p: Player(name=p) for p in players},
            current_leg=Leg(
                camel_states={camel.color: camel for camel in camels}),
            next_leg_player=starting_player_index
        )

    def move_to_next_leg(self):
        self._distribute_leg_points()
        self.legs_played += 1
        self.current_leg.next()
        self.next_leg_player = (self.next_leg_player + 1) % len(self.players)

    def finish_game(self):
        self._distribute_leg_points()
        self.legs_played += 1
        self._distribute_game_points()
        self.finished = True

    def play_action(self, action: Action):
        # Action 1: Player rolls a dice
        if action.dice_rolled is not None:
            game_finished = self.current_leg.move_camel(dice=action.dice_rolled, player=action.player)
            if game_finished:
                self.finish_game()
            return
        # Action 2: Player places cheering or booing tile
        if action.cheering_tile_placed is not None:
            self.current_leg.place_tile(position=action.cheering_tile_placed, player=action.player, cheering=True)
            return
        if action.booing_tile_placed is not None:
            self.current_leg.place_tile(position=action.booing_tile_placed, player=action.player, cheering=False)
            return
        # Action 3: Player places leg bet
        if action.leg_bet is not None:
            self.current_leg.bet_camel_wins_leg(camel_color=action.leg_bet, player=action.player)
            return
        # Action 4: Player places game winner bet
        if action.game_winner_bet is not None:
            self.hidden_game_winner_bets[action.game_winner_bet].append(action.player)
            return
        # Action 5: Player places game loser bet
        if action.game_loser_bet is not None:
            self.hidden_game_loser_bets[action.game_loser_bet].append(action.player)
            return
        
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

    def reset(self):
        self.players = {p: Player(name=p) for p in self.players.keys()}
        self.legs_played = 0
        self.current_leg = Leg(
            camel_states={camel.color: camel for camel in Game._find_camel_start_positions(self.dice_roller)}
        )
        self.next_leg_player = 0
        self.hidden_game_winner_bets = defaultdict(list)
        self.hidden_game_loser_bets = defaultdict(list)
