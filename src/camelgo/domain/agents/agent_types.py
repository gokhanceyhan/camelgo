"""Enumeration of different types of agents in the CamelGo domain."""

from enum import Enum

from src.camelgo.domain.agents.random_player import RandomPlayerAgent


class AgentType(Enum):
    """Enumeration of different types of agents in the CamelGo domain."""
    RANDOM_PLAYER = "RANDOM_PLAYER"
    EXPECTED_VALUE_MAX = "EXPECTED_VALUE_MAX"
    PPO = "PPO"


class AgentFactory:
    """Factory class to create agents based on AgentType."""

    @staticmethod
    def create_agent(agent_type: AgentType, **kwargs):
        """Create an agent based on the specified AgentType.

        Args:
            agent_type (AgentType): The type of agent to create.
            **kwargs: Additional parameters for agent creation.

        Returns:
            An instance of the specified agent type.
        """
        if agent_type == AgentType.RANDOM_PLAYER:
            return RandomPlayerAgent(**kwargs)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")