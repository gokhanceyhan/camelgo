"""Single-Agent PPO training script for CamelGo using TorchRL."""

import torch
from torch import nn
from tensordict.nn import TensorDictModule
from torchrl.envs import GymWrapper, TransformedEnv, StepCounter, ParallelEnv, Compose, RenameTransform
from torchrl.envs.libs.gym import default_info_dict_reader
from torchrl.modules import ActorValueOperator, MLP, OneHotCategorical, ProbabilisticActor
from torchrl.modules.distributions import MaskedCategorical
from torchrl.collectors import SyncDataCollector
from torchrl.data import ReplayBuffer, LazyMemmapStorage
from torchrl.objectives import ClipPPOLoss
from torchrl.objectives.value import GAE
from torchrl.record.loggers import get_logger

from camelgo.adapters.sim_env.gym_env import CamelGoEnv


def make_env():
    env = CamelGoEnv()
    env = GymWrapper(env) # Converts to TorchRL Env
    env.set_info_dict_reader(default_info_dict_reader(["action_mask"]))
    env = TransformedEnv(
        env,
        Compose(
            StepCounter(max_steps=100), # Limit leg/game steps to avoid infinite loops
            RenameTransform(in_keys=["action_mask"], out_keys=["mask"]),
        )
    )
    return env


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
    # Observation: 253, Action: 48
    # Shared or separate Actor/Critic? Shared trunk common in PPO.
    
    # Simple MLP
    common_mlp = MLP(in_features=253, out_features=128, depth=2, activation_class=nn.Tanh)
    
    # Actor Head
    actor_head = MLP(in_features=128, out_features=48, depth=1)
    # We need a probabilistic distribution wrapper
    # OneHotCategorical or Categorical. 
    # Use SafeProbabilisticModule or just raw distribution output if manual.
    # TorchRL simplifies this with ActorValueOperator if provided a common module.
    
    # Let's use explicit modules for clarity
    actor_net = nn.Sequential(
        common_mlp,
        actor_head,
        # We need to ensure output maps to distribution parameters (logits)
    )
    
    # Value Head
    value_head = MLP(in_features=128, out_features=1, depth=1)
    critic_net = nn.Sequential(
        common_mlp, # Note: this shares weights in Python logic only if passed identically. 
                    # Actually standard MLP creates new weights. 
                    # To share weights, we need a separate module class.
        value_head
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
    
    # Value operator
    value_operator = critic_module

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
