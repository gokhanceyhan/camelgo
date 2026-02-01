import pytest
from camelgo.domain.environment.camel import Camel
from camelgo.domain.environment.game_config import GameConfig, Color


def test_camel_basic():
    camel = Camel(color=Color.BLUE, track_pos=1, stack_pos=0)
    assert camel.color == Color.BLUE
    assert camel.track_pos == 1
    assert camel.stack_pos == 0
    assert camel.available_bets == GameConfig.BET_VALUES
    assert camel.dice_value is None
    assert not camel.finished
    assert not camel.is_crazy()


def test_camel_move():
    camel = Camel(color=Color.RED, track_pos=2, stack_pos=1)
    camel.move(track_pos=5, stack_pos=2)
    assert camel.track_pos == 5
    assert camel.stack_pos == 2


def test_camel_move_above_board_size():
    camel = Camel(color=Color.BLUE, track_pos=15, stack_pos=0)
    camel.move(track_pos=20)
    assert camel.track_pos == 20
    assert camel.finished is True


def test_camel_move_below_one():
    camel = Camel(color=Color.BLUE, track_pos=2, stack_pos=0)
    camel.move(track_pos=0)
    assert camel.track_pos == GameConfig.BOARD_SIZE


def test_camel_bet():
    camel = Camel(color=Color.RED, track_pos=2, stack_pos=1)
    bet = camel.bet()
    assert bet == GameConfig.BET_VALUES[0]
    assert camel.available_bets == GameConfig.BET_VALUES[1:]


def test_camel_bet_no_available_bets():
    camel = Camel(color=Color.RED, track_pos=2, stack_pos=1)
    camel.available_bets = []
    with pytest.raises(ValueError, match="No more bets available for camel red."):
        camel.bet()


def test_camel_reset():
    camel = Camel(color="green", track_pos=3, stack_pos=0)
    camel.dice_rolled(2)
    camel.reset_for_new_leg()
    assert camel.available_bets == GameConfig.BET_VALUES
    assert camel.dice_value is None
