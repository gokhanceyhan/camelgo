from torch import nn
from tensordict.nn import TensorDictModule
from torchrl.modules import MLP, ProbabilisticActor
from torchrl.modules.distributions import MaskedCategorical

def create_ppo_modules(obs_dim=253, action_dim=48, hidden_dim=128, device="cpu"):
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
    
    # Common backbone (optional, but used in previous script implicitly by structure, 
    # though usually PPO uses separate or shared. Here we define the structure used previously.)
    
    # Note: in previous script, they were separate instances of nn.Sequential containing new MLPs.
    # We will replicate the architecture:
    # Actor: MLP(obs->128, depth=2) -> MLP(128->48, depth=1)
    # Critic: MLP(obs->128, depth=2) -> MLP(128->1, depth=1)
    
    # Actor Network
    actor_common = MLP(in_features=obs_dim, out_features=hidden_dim, depth=2, activation_class=nn.Tanh)
    actor_head = MLP(in_features=hidden_dim, out_features=action_dim, depth=1)
    actor_net = nn.Sequential(actor_common, actor_head)
    
    # Critic Network
    critic_common = MLP(in_features=obs_dim, out_features=hidden_dim, depth=2, activation_class=nn.Tanh)
    value_head = MLP(in_features=hidden_dim, out_features=1, depth=1)
    critic_net = nn.Sequential(critic_common, value_head)
    
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
    
    value_operator = critic_module
    
    return actor, value_operator
