"""Generic peer agent for the ARISE planning pipeline."""

from __future__ import annotations


class GenericAgent:
    def __init__(self, agent_id: str, llm) -> None:
        self.agent_id = agent_id
        self.llm = llm
        self.role: str | None = None
        self.dependencies: list[str] = []
        self.draft: str | None = None
        self.output: str | None = None

    def assign_role(self, peers: list[GenericAgent], input_text: str) -> None:
        """Assign a role to this agent based on peer roles and the plan."""
        raise NotImplementedError

    def refine_role(
        self,
        peers: list[GenericAgent],
        input_text: str,
        max_agents: int,
    ) -> None:
        """Refine this agent's role or propose adding a new peer agent."""
        raise NotImplementedError

    def declare_dependencies(self, peers: list[GenericAgent], input_text: str) -> None:
        """Declare which peer agents this agent depends on."""
        raise NotImplementedError

    def draft_output(self, peers: list[GenericAgent], input_text: str) -> None:
        """Draft output using outputs from dependency peers."""
        raise NotImplementedError

    def refine_output(self, peers: list[GenericAgent], input_text: str) -> None:
        """Refine this agent's draft using peer outputs."""
        raise NotImplementedError
