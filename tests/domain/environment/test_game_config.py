from camelgo.domain.environment.game_config import GameConfig, Color


def test_is_camel_crazy():
    assert GameConfig.is_camel_crazy(Color.WHITE)
    assert GameConfig.is_camel_crazy(Color.BLACK)
    assert not GameConfig.is_camel_crazy(Color.BLUE)
