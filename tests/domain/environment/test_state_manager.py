import pytest

from camelgo.domain.environment.state_manager import StateManager

@pytest.fixture
def players():
    return ["Alice", "Bob"]

@pytest.fixture
def dices_at_game_start():
    return [("red", 1), ("blue", 2), ("green", 3), ("purple", 3), ("black", 1), ("white", 1)]

def test_start_game(players, dices_at_game_start):
    manager = StateManager()
    manager.start_game(players=players, dices_rolled=dices_at_game_start)
    assert manager.game_state() is not None
    assert manager.game_state().players[0].name == "Alice"
    assert manager.game_state().players[1].name == "Bob"
    assert len(manager.game_state().current_leg.camel_states) == 6
    assert manager.game_state().current_leg.camel_states["red"].track_pos == 1
    assert manager.game_state().current_leg.camel_states["blue"].track_pos == 2
    assert manager.game_state().current_leg.camel_states["green"].track_pos == 3
    assert manager.game_state().current_leg.camel_states["green"].stack_pos == 0  # Green at bottom
    assert manager.game_state().current_leg.camel_states["purple"].track_pos == 3
    assert manager.game_state().current_leg.camel_states["purple"].stack_pos == 1  # Purple on top of green
    assert manager.game_state().current_leg.camel_states["black"].track_pos == 16
    assert manager.game_state().current_leg.camel_states["black"].stack_pos == 0  # Black at the bottom
    assert manager.game_state().current_leg.camel_states["white"].track_pos == 16
    assert manager.game_state().current_leg.camel_states["white"].stack_pos == 1  # White on top of black
