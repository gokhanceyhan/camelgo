"""Script to run a trained CamelGo agent in a simulation environment and display the game progress."""

import torch

from camelgo.domain.environment.action import ActionInt
from camelgo.domain.environment.game_config import GameConfig
from camelgo.domain.environment.gym_env import CamelGoEnv
from camelgo.domain.training.single_agent_ppo import create_ppo_modules, make_env


def get_action_description(action_idx):
    """Convert action index to human-readable description."""
    action_num = ActionInt(action_idx)
    return action_num.name.replace("_", " ").title()


def load_agent(model_path="models/actor.pt"):
    """
    Reconstructs the agent architecture and loads trained weights.
    Structure must match src/camelgo/training/single_agent_ppo.py
    """
    # 1. Define Network Architecture
    actor, _ = create_ppo_modules(
        obs_dim=CamelGoEnv.OBSERVATION_DIM, 
        action_dim=CamelGoEnv.ACTION_DIM, 
        hidden_dim=128
    )
    
    # 2. Load Weights
    try:
        # Load state dictionary
        state_dict = torch.load(model_path)
        actor.load_state_dict(state_dict)
        print(f"Successfully loaded model from {model_path}")
    except FileNotFoundError:
        print(f"Warning: Model file not found at {model_path}. Using random weights.")
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Using random weights.")
    
    return actor


def main():
    env = make_env()
    actor = load_agent()
    # evaluation mode
    actor.eval()
    
    print("-" * 50)
    print("Starting Game Simulation with Trained Agent")
    print("-" * 50)
    
    # Run rollout
    # max_steps ensures we don't loop forever if something is broken, 
    # but the environment should emit 'done' when the game ends.
    with torch.no_grad():
        rollout_td = env.rollout(policy=actor, max_steps=1000, auto_reset=True)
    
    total_reward = 0
    steps = rollout_td.shape[0]
    
    for i in range(steps):
        step_td = rollout_td[i]
        
        action_idx = step_td["action"].item()
        reward = step_td["next", "reward"].item()
        action_desc = get_action_description(action_idx)
        
        print(f"Step {i+1:3d} | Action Index: {action_idx:2d} | Reward: {reward:6.2f} | {action_desc}")
        
        total_reward += reward
    
    print("-" * 50)
    print(f"Game Over!")
    print(f"Total Steps: {steps}")
    print(f"Total Reward: {total_reward:.2f}")
    print(f"Winner player is {env.game.winner_player()}")
    print("-" * 50)


if __name__ == "__main__":
    main()
