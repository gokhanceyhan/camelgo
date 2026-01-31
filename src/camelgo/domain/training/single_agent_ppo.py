"""Single-Agent PPO training script for CamelGo using TorchRL."""

from tensordict.nn import TensorDictModule
import torch
from torchrl.envs import GymWrapper, ParallelEnv
from torchrl.envs.libs.gym import default_info_dict_reader
from torchrl.collectors import SyncDataCollector
from torchrl.data import ReplayBuffer, LazyMemmapStorage
from torchrl.modules import MLP, ProbabilisticActor
from torchrl.modules.distributions import MaskedCategorical
from torchrl.objectives import ClipPPOLoss
from torchrl.objectives.value import GAE

from camelgo.domain.environment.gym_env import CamelGoEnv


def make_env():
    env = CamelGoEnv()
    # Converts to TorchRL Env
    # Important: Use categorical action encoding for discrete actions
    # Otherwise, TorchRL may misinterpret the action space
    env = GymWrapper(env, categorical_action_encoding=True)
    env.set_info_dict_reader(default_info_dict_reader(["mask"]))
    return env


def create_ppo_modules(
        obs_dim=CamelGoEnv.OBSERVATION_DIM, 
        action_dim=CamelGoEnv.ACTION_DIM, 
        hidden_dim=128, 
        device="cpu"
    ):
    """
    Creates the Actor and Value modules for PPO.
    
    Args:
        obs_dim (int): Observation space dimension.
        action_dim (int): Action space dimension.
        hidden_dim (int): Hidden layer dimension.
        device (str or torch.device): Device to put modules on.
        
    Returns:
        actor (ProbabilisticActor): The actor module.
        value_operator (TensorDictModule): The critic module.
    """
    
    # Actor Network
    actor_net = MLP(
        in_features=obs_dim,
        out_features=action_dim,
        num_cells=[hidden_dim, hidden_dim],
        activation_class=torch.nn.Tanh,
    )
    
    # Critic Network
    critic_net = MLP(
        in_features=obs_dim,
        out_features=1,
        num_cells=[hidden_dim, hidden_dim],
        activation_class=torch.nn.Tanh,
    )
    
    # Move to device
    actor_net.to(device)
    critic_net.to(device)

    # Wrap in TensorDictModules
    actor_module = TensorDictModule(
        actor_net, in_keys=["observation"], out_keys=["logits"]
    )
    
    critic_module = TensorDictModule(
        critic_net, in_keys=["observation"], out_keys=["state_value"]
    )
    
    # Actor requires distribution
    actor = ProbabilisticActor(
        module=actor_module,
        in_keys=["logits", "mask"],
        out_keys=["action"],
        distribution_class=MaskedCategorical,
        return_log_prob=True,
    )
    
    return actor, critic_module


def train(
    total_frames=50_000,
    frames_per_batch=1_000,
    num_epochs=10,
    lr=3e-4,
    device="cpu", # or "cuda"
    num_workers=1
):
    device = torch.device(device)
    
    # 1. Define Environment
    # Use ParallelEnv if >1 worker, else normal
    if num_workers > 1:
        create_env_fn = make_env
        env = ParallelEnv(num_workers, create_env_fn)
    else:
        env = make_env()
        
    # 2. Define Network
    actor, value_operator = create_ppo_modules(
        obs_dim=CamelGoEnv.OBSERVATION_DIM, 
        action_dim=CamelGoEnv.ACTION_DIM, 
        hidden_dim=128, 
        device=device
    )

    # 3. Collector
    collector = SyncDataCollector(
        env,
        actor,
        frames_per_batch=frames_per_batch,
        total_frames=total_frames,
        split_trajs=False,
        device=device,
    )

    # 4. Loss
    advantage_module = GAE(
        gamma=0.99, lmbda=0.95, value_network=value_operator, average_gae=True
    )
    
    loss_module = ClipPPOLoss(
        actor_network=actor,
        critic_network=value_operator,
        clip_epsilon=0.2,
        entropy_bonus=True,
        entropy_coeff=0.01,
        critic_coeff=1.0,
        loss_critic_type="smooth_l1",
    )

    # 5. Optimizer
    optim = torch.optim.Adam(loss_module.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optim, total_frames // frames_per_batch, 0.0
    )

    # 6. Replay Buffer
    replay_buffer = ReplayBuffer(
        storage=LazyMemmapStorage(frames_per_batch),
        batch_size=frames_per_batch // num_epochs,
    )

    # 7. Loop
    print(f"Starting training on {device}...")
    logs = {"reward": [], "step_count": []}
    
    for i, tensordict_data in enumerate(collector):
        # Calc Advantage
        with torch.no_grad():
            advantage_module(tensordict_data)
            
        # Data to buffer
        data_view = tensordict_data.reshape(-1)
        replay_buffer.extend(data_view)

        # Train Loop (Epochs)
        for _ in range(num_epochs):
             for _ in range(frames_per_batch // (frames_per_batch // num_epochs)):
                subdata = replay_buffer.sample()
                loss_vals = loss_module(subdata.to(device))
                
                loss_value = (
                    loss_vals["loss_objective"]
                    + loss_vals["loss_critic"]
                    + loss_vals["loss_entropy"]
                )
                
                optim.zero_grad()
                loss_value.backward()
                torch.nn.utils.clip_grad_norm_(loss_module.parameters(), 1.0)
                optim.step()
                 
        scheduler.step()
        
        # Logging
        avg_reward = tensordict_data["next", "reward"].mean().item()
        print(f"Batch {i}: Avg Reward = {avg_reward:.4f}")
        logs["reward"].append(avg_reward)
        
    print("Training Complete.")
    
    # Save Model
    import os
    os.makedirs("models", exist_ok=True)
    torch.save(actor.state_dict(), "models/actor.pt")
    torch.save(value_operator.state_dict(), "models/critic.pt")
    print("Models saved to models/")


def run_cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--frames", type=int, default=10_000)
    args = parser.parse_args()
    
    train(
        total_frames=args.frames,
        device=args.device,
        num_workers=args.workers
    )


if __name__ == "__main__":
    run_cli()
