from collections import defaultdict
import pytest

from camelgo.domain.environment.action import Action
from camelgo.domain.environment.leg import Leg
from camelgo.domain.environment.camel import Camel
from camelgo.domain.environment.dice import Dice
from camelgo.domain.environment.game_config import GameConfig
from camelgo.domain.environment.player import Player


@pytest.fixture
def players():
    return {name: Player(name=name, points=3) for name in ["Alice", "Bob"]}

@pytest.fixture
def camels_on_different_tiles():
    camels = {}
    # Camels are placed on tiles 1 to 7
    for i, color in enumerate(GameConfig.ALL_CAMEL_COLORS):
        camels[color] = Camel(color=color, track_pos=i+1, stack_pos=0)
    return camels

def test_leg_basic(camels_on_different_tiles, players):
    camels = camels_on_different_tiles
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    assert leg.leg_number == 1
    assert leg.cheering_tiles == []
    assert leg.booing_tiles == []
    assert leg.leg_points == {}
    assert leg.player_bets == {}

def test_leg_move_single_camel_above_another(camels_on_different_tiles, players):
    camels = camels_on_different_tiles
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    dice = Dice(color="blue", number=2)
    # blue camel is at position 1
    # it has to move on top of the green camel at position 3
    player = "Alice"
    action = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action)
    assert not game_finished
    assert leg.leg_points[player] == 1
    assert leg.camel_states["blue"].track_pos == 3
    assert leg.camel_states["blue"].stack_pos == 1  # on top of green

def test_leg_move_stacked_camels_above_another(players):
    camels = {
        "red": Camel(color="red", track_pos=3, stack_pos=0),
        "green": Camel(color="green", track_pos=3, stack_pos=1),
        "purple": Camel(color="purple", track_pos=5, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    dice = Dice(color="red", number=2)
    player = "Bob"
    action = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action)
    assert not game_finished
    assert leg.leg_points[player] == 1
    assert leg.camel_states["red"].track_pos == 5
    assert leg.camel_states["red"].stack_pos == 1
    assert leg.camel_states["green"].track_pos == 5
    assert leg.camel_states["green"].stack_pos == 2
    assert leg.camel_states["purple"].track_pos == 5
    assert leg.camel_states["purple"].stack_pos == 0

def test_leg_move_black_camel_with_red_above(players):
    camels = {
        "black": Camel(color="black", track_pos=4, stack_pos=0),
        "red": Camel(color="red", track_pos=4, stack_pos=1),
        "green": Camel(color="green", track_pos=2, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    dice = Dice(color="black", number=2)
    player = "Carol"
    action = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action)
    assert not game_finished
    # Both black and red should move together (since red is above black)
    assert leg.camel_states["black"].track_pos == 2  # black moves backwards
    assert leg.camel_states["red"].track_pos == 2    # red moves with black
    assert leg.camel_states["black"].stack_pos == 1
    assert leg.camel_states["red"].stack_pos == 2
    assert leg.camel_states["green"].track_pos == 2
    assert leg.camel_states["green"].stack_pos == 0
    assert leg.leg_points[player] == 1

def test_leg_move_camel_lands_on_cheering_tile(players):
    camels = {
        "blue": Camel(color="blue", track_pos=1, stack_pos=0),
        "green": Camel(color="green", track_pos=3, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    # Place a cheering tile at position 3 by player 'Dave'
    action_tile = Action(cheering_tile_placed=2, player="Dave")
    leg.play_action(action_tile)
    dice = Dice(color="blue", number=1)
    player = "Alice"
    action_roll = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action_roll)
    assert not game_finished
    # Blue lands on 2, then moves to 3 due to cheering tile
    assert leg.camel_states["blue"].track_pos == 3
    assert leg.camel_states["blue"].stack_pos == 1
    assert leg.leg_points[player] == 1  # for rolling
    assert leg.leg_points["Dave"] == 1  # for cheering tile

def test_leg_move_camel_lands_on_booing_tile(players):
    camels = {
        "blue": Camel(color="blue", track_pos=1, stack_pos=0),
        "green": Camel(color="green", track_pos=2, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    # Place a booing tile at position 3 by player 'Eve'
    action_tile = Action(booing_tile_placed=3, player="Eve")
    leg.play_action(action_tile)
    dice = Dice(color="blue", number=2)
    player = "Alice"
    action_roll = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action_roll)
    assert not game_finished
    # Blue lands on 3, then moves to 2 due to booing tile
    assert leg.camel_states["blue"].track_pos == 2
    assert leg.camel_states["blue"].stack_pos == 0
    assert leg.camel_states["green"].track_pos == 2
    assert leg.camel_states["green"].stack_pos == 1
    assert leg.leg_points[player] == 1  # for rolling
    assert leg.leg_points["Eve"] == 1  # for booing tile

def test_leg_move_crazy_camel_lands_on_cheering_tile(players):
    camels = {
        "white": Camel(color="white", track_pos=5, stack_pos=0),
        "black": Camel(color="black", track_pos=3, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    # Place a cheering tile at position 3 by player 'Frank'
    action_tile = Action(cheering_tile_placed=4, player="Frank")
    leg.play_action(action_tile)
    dice = Dice(color="white", number=1)
    player = "Alice"
    action_roll = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action_roll)
    assert not game_finished
    # White is crazy, moves backwards: 5 - 1 = 4, then cheering tile moves it to 3
    assert leg.camel_states["white"].track_pos == 3
    assert leg.camel_states["white"].stack_pos == 1
    assert leg.camel_states["black"].track_pos == 3
    assert leg.camel_states["black"].stack_pos == 0
    assert leg.leg_points[player] == 1  # for rolling
    assert leg.leg_points["Frank"] == 1  # for cheering tile

def test_leg_move_crazy_camel_lands_on_booing_tile(players):
    camels = {
        "white": Camel(color="white", track_pos=5, stack_pos=0),
        "black": Camel(color="black", track_pos=3, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    # Place a booing tile at position 2 by player 'Grace'
    action_tile = Action(booing_tile_placed=2, player="Grace")
    leg.play_action(action_tile)
    dice = Dice(color="white", number=3)
    player = "Alice"
    action_roll = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action_roll)
    assert not game_finished
    # White is crazy, moves backwards: 5 - 3 = 2, then booing tile moves it to 3
    assert leg.camel_states["white"].track_pos == 3
    assert leg.camel_states["white"].stack_pos == 0
    assert leg.camel_states["black"].track_pos == 3
    assert leg.camel_states["black"].stack_pos == 1
    assert leg.leg_points[player] == 1  # for rolling
    assert leg.leg_points["Grace"] == 1  # for booing tile

def test_leg_move_camel_finishes_game(players):
    camels = {
        "blue": Camel(color="blue", track_pos=15, stack_pos=0),
        "green": Camel(color="green", track_pos=10, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    dice = Dice(color="blue", number=2)
    player = "Alice"
    action = Action(dice_rolled=dice, player=player)
    game_finished = leg.play_action(action)
    assert game_finished  # Game should be finished
    assert leg.camel_states["blue"].track_pos > GameConfig.BOARD_SIZE
    assert leg.camel_states["blue"].finished is True
    assert leg.leg_points[player] == 1

def test_place_cheering_tile(players):
    camels = {
        "blue": Camel(color="blue", track_pos=1, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    action = Action(cheering_tile_placed=2, player="Alice")
    leg.play_action(action)
    assert (2, "Alice") in leg.cheering_tiles
    # Should raise if placed on camel
    with pytest.raises(ValueError):
        leg.play_action(Action(cheering_tile_placed=1, player="Bob"))
    # Should raise if placed beside existing tile
    with pytest.raises(ValueError):
        leg.play_action(Action(cheering_tile_placed=3, player="Bob"))

def test_place_booing_tile(players):
    camels = {
        "blue": Camel(color="blue", track_pos=1, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    action = Action(booing_tile_placed=2, player="Alice")
    leg.play_action(action)
    assert (2, "Alice") in leg.booing_tiles
    # Should raise if placed on camel
    with pytest.raises(ValueError):
        leg.play_action(Action(booing_tile_placed=1, player="Bob"))
    # Should raise if placed beside existing tile
    with pytest.raises(ValueError):
        leg.play_action(Action(booing_tile_placed=3, player="Bob"))

def test_bet_camel_wins_leg(players):
    camels = {
        "blue": Camel(color="blue", track_pos=1, stack_pos=0),
        "green": Camel(color="green", track_pos=3, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    player = "Alice"
    action = Action(leg_bet="blue", player=player)
    leg.play_action(action)
    assert leg.player_bets[player]["blue"]
    # Should raise if betting on a non-existent camel
    with pytest.raises(ValueError):
        leg.play_action(Action(leg_bet="red", player=player))

def test_reset_leg(players):
    camels = {
        "blue": Camel(color="blue", track_pos=1, stack_pos=0),
        "green": Camel(color="green", track_pos=3, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    leg.cheering_tiles.append((2, "Alice"))
    leg.booing_tiles.append((4, "Bob"))
    leg.leg_points["Alice"] = 5
    leg.player_bets["Alice"]["blue"] = [5]
    leg.reset_leg()
    assert leg.cheering_tiles == []
    assert leg.booing_tiles == []
    assert leg.leg_points == defaultdict(int)
    assert leg.player_bets == defaultdict(lambda: defaultdict(list))
    for camel in leg.camel_states.values():
        assert camel.dice_value is None
        assert camel.available_bets == GameConfig.BET_VALUES

def test_next_leg(players):
    camels = {
        "blue": Camel(color="blue", track_pos=1, stack_pos=0),
        "green": Camel(color="green", track_pos=3, stack_pos=0)
    }
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    leg.cheering_tiles.append((2, "Alice"))
    leg.booing_tiles.append((4, "Bob"))
    leg.leg_points["Alice"] = 5
    leg.player_bets["Alice"]["blue"] = [5]
    leg.next(starting_player="Alice")
    assert leg.leg_number == 2
    assert leg.cheering_tiles == []
    assert leg.booing_tiles == []
    assert leg.leg_points == defaultdict(int)
    assert leg.player_bets == defaultdict(lambda: defaultdict(list))
    for camel in leg.camel_states.values():
        assert camel.dice_value is None
        assert camel.available_bets == GameConfig.BET_VALUES
    assert leg.next_player == "Alice"

def test_leg_model_validate(players, camels_on_different_tiles):
    leg = Leg(leg_number=1, camel_states=camels_on_different_tiles, players=players)
    dumped = leg.model_dump()
    leg2 = Leg.model_validate(dumped)
    # Ensure defaultdicts are restored
    assert isinstance(leg2.leg_points, type(leg.leg_points))
    assert isinstance(leg2.player_bets, type(leg.player_bets))
