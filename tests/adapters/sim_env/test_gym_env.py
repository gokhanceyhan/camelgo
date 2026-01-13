import numpy as np

from camelgo.adapters.sim_env.gym_env import CamelGoEnv
from camelgo.domain.environment.game_config import GameConfig


class TestCamelGoEnv:
    def test_initialization(self):
        env = CamelGoEnv()
        assert env.observation_space.shape == (253,)
        assert env.action_space.n == 48
        # Should be None before reset
        assert env.game is None

    def test_reset(self):
        env = CamelGoEnv()
        obs, info = env.reset()
        
        # Check observation shape and type
        assert isinstance(obs, np.ndarray)
        assert obs.shape == (253,)
        assert obs.dtype == np.float32
        
        # Check if game is initialized
        assert env.game is not None
        assert env.agent_name in env.game.players
        
        # Check if basic info is returned (can be empty dict in simple impl)
        assert isinstance(info, dict)

    def test_step_dice_roll(self):
        # Action 0 is the roll dice
        env = CamelGoEnv()
        env.reset()
        
        # To strictly test step, we might want to ensure it's a valid action context.
        # But roll dice is usually valid unless all dice rolled.
        # As reset() creates a fresh leg, rolling dice should be valid.
        
        obs, reward, terminated, truncated, info = env.step(0)
        
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)
        
        # Rolling dice gives +1 coin reward immediately
        assert reward == 1.0

    def test_action_leg_bet(self):
        # Actions 1-5 are Leg Bets
        env = CamelGoEnv()
        env.reset()
        
        # Action 1: Bet on Blue
        obs, reward, terminated, truncated, info = env.step(1)
        
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        
        # Verify the bet was placed in the game logic
        # We need to access the game state
        agent_bets = env.game.current_leg.player_bets[env.agent_name]
        # 'blue' is the first color if order matches CamelConfig
        # GameConfig.CAMEL_COLORS = ['blue', 'yellow', 'green', 'purple', 'red']
        bet_color = GameConfig.CAMEL_COLORS[0]
        assert bet_color in agent_bets
        # First bet should be value 5
        assert 5 in agent_bets[bet_color]

    def test_random_rollout_snippet(self):
        # Just run a few random steps to ensure no crash
        env = CamelGoEnv()
        env.reset()
        
        for _ in range(100):
            mask = env.get_action_mask().astype(np.int8)
            action = env.action_space.sample(mask=mask)
            obs, reward, terminated, truncated, info = env.step(action)
            # print(f"Action: {action}, Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}")
            if terminated or truncated:
                break
            assert obs.shape == (253,)

