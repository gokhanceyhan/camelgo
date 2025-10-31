import pytest

from camelgo.domain.environment.action import Action
from camelgo.domain.environment.game import Game
from camelgo.domain.environment.player import Player
from camelgo.domain.environment.leg import Leg
from camelgo.domain.environment.camel import Camel
from camelgo.domain.environment.dice import DiceRoller, Dice
from camelgo.domain.environment.game_config import GameConfig


@pytest.fixture
def dice_roller():
    return DiceRoller(seed=123)


@pytest.fixture
def players():
    return {name: Player(name=name, points=3) for name in ["Alice", "Bob"]}

@pytest.fixture
def game_new_start(players, dice_roller):
    camels = {color: Camel(color=color, track_pos=1, stack_pos=i) for i, color in enumerate(GameConfig.CAMEL_COLORS)}
    crazy_camels = {color: Camel(color=color, track_pos=GameConfig.BOARD_SIZE, stack_pos=i) for i, color in enumerate(GameConfig.CRAZY_CAMELS)}
    camels.update(crazy_camels)
    leg = Leg(leg_number=1, camel_states=camels, players=players)
    game = Game(
        players=players, 
        current_leg=leg, 
        dice_roller=dice_roller, 
        next_leg_starting_player="Alice"
    )
    return game

@pytest.fixture
def game_about_to_end(players, dice_roller):
    """Fixture for a Game instance where the game is about to end (one camel near finish)."""
    # Place one camel at the last tile, others far behind
    camels = {
        "red": Camel(color="red", track_pos=GameConfig.BOARD_SIZE, stack_pos=0),
        "blue": Camel(color="blue", track_pos=1, stack_pos=0),
        "green": Camel(color="green", track_pos=2, stack_pos=0),
        "yellow": Camel(color="yellow", track_pos=3, stack_pos=0),
        "purple": Camel(color="purple", track_pos=1, stack_pos=1),
        "white": Camel(color="white", track_pos=10, stack_pos=0),
        "black": Camel(color="black", track_pos=11, stack_pos=0),
    }
    leg = Leg(
        leg_number=10, 
        players=players,
        camel_states=camels,
        leg_points={
            "Alice": 5,
            "Bob": 3
        }, 
        player_bets={
            "Alice": {"red": [5, 3], "yellow": [5]}, # Alice will get 9 points from the leg if the camel order holds
            "Bob": {"green": [5], "yellow": [3]} # Bob will get 0 points from the leg if the camel order holds
        }
    )
    return Game(
        players=players, 
        current_leg=leg, 
        dice_roller=dice_roller, 
        legs_played=10, 
        finished=False,
        next_leg_starting_player='Bob', 
        hidden_game_winner_bets={
            'red': ['Alice'],
            'blue': ['Bob']
        }, 
        hidden_game_loser_bets={
            'green': ['Bob'],
            'yellow': ['Alice']
        }
    )

@pytest.fixture
def action_alice_roll_red_3():
    return Action(player="Alice", dice_rolled=Dice(color="red", number=3))


def test_start_game(dice_roller):
    player_names = ["Alice", "Bob"]
    game = Game.start_game(player_names=player_names, dice_roller=dice_roller)
    assert game is not None
    assert game.players.keys() == {"Alice", "Bob"}
    assert len(game.current_leg.camel_states) == 7
    assert game.current_leg.camel_states["blue"].track_pos == 2
    assert game.current_leg.camel_states["blue"].stack_pos == 1
    assert game.first_camel().color == "green"
    assert game.last_camel().color == "purple"

def test_player_dice_roll_action(game_new_start, action_alice_roll_red_3):
    # given
    game = game_new_start

    # when
    action = action_alice_roll_red_3
    game.play_action(action)

    # then
    assert game.current_leg.leg_points["Alice"] == 1
    assert game.current_leg.camel_states["red"].track_pos == 4
    assert game.current_leg.camel_states["red"].stack_pos == 0

def test_game_about_to_end(game_about_to_end, action_alice_roll_red_3):
    # given
    game = game_about_to_end

    # when
    action = action_alice_roll_red_3
    game.play_action(action)

    # then
    assert game.finished is True
    assert game.legs_played == 11
    assert game.current_leg.leg_points["Alice"] == 6
    assert game.current_leg.camel_states["red"].track_pos > GameConfig.BOARD_SIZE  # red camel should have finished
    assert game.current_leg.camel_states["red"].finished is True
    assert game.first_camel().color == "red"
    assert game.last_camel().color == "blue"
    assert game.players["Alice"].points == 25 # 3 (initial) + 6 (leg points) + 9 (won by leg bets) + 7 (won by game bets)
    assert game.players["Bob"].points == 4 # 3 (initial) + 3 (leg points) + 0 (won by leg bets) + -2 (won by game bets)

def test_player_places_cheering_tile(game_new_start):
    # given
    game = game_new_start
    position = 5
    player = "Alice"
    # when
    action = Action(player=player, cheering_tile_placed=position)
    game.play_action(action)
    # then
    assert (position, player) in game.current_leg.cheering_tiles
    assert position not in [c.track_pos for c in game.current_leg.camel_states.values()]

def test_player_places_booing_tile(game_new_start):
    # given
    game = game_new_start
    position = 6
    player = "Bob"
    # when
    action = Action(player=player, booing_tile_placed=position)
    game.play_action(action)
    # then
    assert (position, player) in game.current_leg.booing_tiles
    assert position not in [c.track_pos for c in game.current_leg.camel_states.values()]

def test_player_places_leg_bet(game_new_start):
    # given
    game = game_new_start
    player = "Alice"
    camel_color = "red"
    # when
    action = Action(player=player, leg_bet=camel_color)
    game.play_action(action)
    # then
    assert camel_color in game.current_leg.player_bets[player]
    assert len(game.current_leg.player_bets[player][camel_color]) == 1

def test_player_places_game_winner_bet(game_new_start):
    # given
    game = game_new_start
    player = "Bob"
    camel_color = "green"
    # when
    action = Action(player=player, game_winner_bet=camel_color)
    game.play_action(action)
    # then
    assert player in game.hidden_game_winner_bets[camel_color]

def test_player_places_game_loser_bet(game_new_start):
    # given
    game = game_new_start
    player = "Alice"
    camel_color = "purple"
    # when
    action = Action(player=player, game_loser_bet=camel_color)
    game.play_action(action)
    # then
    assert player in game.hidden_game_loser_bets[camel_color]

def test_move_to_next_leg(game_about_to_end):
    # given
    game = game_about_to_end
    initial_leg_number = game.current_leg.leg_number
    initial_legs_played = game.legs_played
    # when
    game.move_to_next_leg()
    # then
    assert game.current_leg.leg_number == initial_leg_number + 1
    assert game.legs_played == initial_legs_played + 1
    assert game.current_leg.cheering_tiles == []
    assert game.current_leg.booing_tiles == []
    assert game.current_leg.leg_points == {}
    assert game.current_leg.player_bets == {}
    for camel in game.current_leg.camel_states.values():
        assert camel.available_bets == GameConfig.BET_VALUES
        assert camel.dice_value is None
    assert game.current_leg.next_player == "Bob"
    assert game.next_leg_starting_player == "Alice"
    assert game.players["Alice"].points == 17
    assert game.players["Bob"].points == 6

def test_game_reset(game_new_start):
    # given
    game = game_new_start
    # simulate some state changes
    game.current_leg.cheering_tiles.append((5, "Alice"))
    game.current_leg.booing_tiles.append((6, "Bob"))
    game.current_leg.leg_points["Alice"] = 2
    game.current_leg.player_bets["Alice"]["red"] = [5]
    game.legs_played = 3
    game.hidden_game_winner_bets["red"].append("Alice")
    game.hidden_game_loser_bets["blue"].append("Bob")
    # when
    game.reset()
    # then
    assert game.legs_played == 0
    assert game.current_leg.leg_number == 1
    assert game.current_leg.cheering_tiles == []
    assert game.current_leg.booing_tiles == []
    assert game.current_leg.leg_points == {}
    assert game.current_leg.player_bets == {}
    assert game.hidden_game_winner_bets == {}
    assert game.hidden_game_loser_bets == {}
    for player in game.players.values():
        assert player.points == GameConfig.STARTING_MONEY
