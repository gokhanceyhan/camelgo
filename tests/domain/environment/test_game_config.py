from camelgo.domain.environment.game_config import GameConfig


def test_is_camel_crazy():
    assert GameConfig.is_camel_crazy('white')
    assert GameConfig.is_camel_crazy('black')
    assert not GameConfig.is_camel_crazy('blue')
