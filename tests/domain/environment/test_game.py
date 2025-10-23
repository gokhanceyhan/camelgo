import pytest

from camelgo.domain.environment.game import Game

@pytest.fixture
def players():
    return ["Alice", "Bob"]

@pytest.fixture
def dices_at_game_start():
    return [("red", 1), ("blue", 2), ("green", 3), ("purple", 3), ("black", 1), ("white", 1)]

def test_start_game(players, dices_at_game_start):
    game = Game.start_game(players=players, dices_rolled=dices_at_game_start)
    assert game is not None
    assert game.players[0].name == "Alice"
    assert game.players[1].name == "Bob"
    assert len(game.current_leg.camel_states) == 6
    assert game.current_leg.camel_states["red"].track_pos == 1
    assert game.current_leg.camel_states["blue"].track_pos == 2
    assert game.current_leg.camel_states["green"].track_pos == 3
    assert game.current_leg.camel_states["green"].stack_pos == 0  # Green at bottom
    assert game.current_leg.camel_states["purple"].track_pos == 3
    assert game.current_leg.camel_states["purple"].stack_pos == 1  # Purple on top of green
    assert game.current_leg.camel_states["black"].track_pos == 16
    assert game.current_leg.camel_states["black"].stack_pos == 0  # Black at the bottom
    assert game.current_leg.camel_states["white"].track_pos == 16
    assert game.current_leg.camel_states["white"].stack_pos == 1  # White on top of black
