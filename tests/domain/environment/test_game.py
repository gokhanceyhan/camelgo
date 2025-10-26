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
    return {name: Player(name=name) for name in ["Alice", "Bob"]}


@pytest.fixture
def action_alice_roll_red_3():
    return Action(player="Alice", dice_rolled=Dice(color="red", number=3))


def test_start_game(dice_roller):
    players = ["Alice", "Bob"]
    game = Game.start_game(players=players, dice_roller=dice_roller)
    assert game is not None
    assert game.players.keys() == {"Alice", "Bob"}
    assert len(game.current_leg.camel_states) == 6
    assert game.current_leg.camel_states["blue"].track_pos == 2
    assert game.current_leg.camel_states["blue"].stack_pos == 0
    assert game.first_camel().color == "green"
    assert game.last_camel().color == "red"


def test_player_dice_roll_action(players, dice_roller, action_alice_roll_red_3):
    # given
    camels = {color: Camel(color=color, track_pos=1, stack_pos=i) for i, color in enumerate(GameConfig.CAMEL_COLORS)}
    crazy_camels = {color: Camel(color=color, track_pos=GameConfig.BOARD_SIZE, stack_pos=i) for i, color in enumerate(GameConfig.CRAZY_CAMELS)}
    camels.update(crazy_camels)
    leg = Leg(leg_number=1, camel_states=camels)
    game = Game(players=players, current_leg=leg, dice_roller=dice_roller)

    # when
    game.play_action(action_alice_roll_red_3)

    # then
    assert game.current_leg.leg_points["Alice"] == 1
    assert game.current_leg.camel_states["red"].track_pos == 4
    assert game.current_leg.camel_states["red"].stack_pos == 0
