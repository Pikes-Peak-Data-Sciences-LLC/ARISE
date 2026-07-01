"""Peer-to-peer orchestrator for the ARISE multi-agent planning pipeline."""

from __future__ import annotations

from ARISE.agents.generic_agent import GenericAgent
from ARISE.nodes.dependency_declaration import run_dependency_declaration
from ARISE.nodes.draft_agent import run_draft_pass
from ARISE.nodes.draft_scheduler import select_next_drafter
from ARISE.nodes.intitialize import create_agents
from ARISE.nodes.output_refinement import run_output_refinement
from ARISE.nodes.role_assignment import run_role_assignment
from ARISE.nodes.role_refinement import run_role_refinement


class ARISEGraph:
    """
    Orchestrates phase order and agent turn-taking.

    Data lives on each GenericAgent; agents read and write peer objects
    """

    def __init__(
        self,
        agents: list[GenericAgent],
        input_text: str,
        max_agents: int,
    ) -> None:
        self.agents = agents
        self.input_text = input_text
        self.max_agents = max_agents

    def run(self) -> list[GenericAgent]:
        """
        Execute the full peer-to-peer pipeline.

        Flow:
            create agents
              -> role assignment (each agent reads peer roles)
              -> role refinement (agents may change roles or spawn peers)
              -> dependency declaration (agents declare peer dependencies)
              -> draft loop (agents draft using dependency peer outputs)
              -> output refinement (each agent refines using peer outputs)

        Returns the agent roster with each agent's executable output set.
        """
        run_role_assignment(self.agents, self.input_text)
        self.agents = run_role_refinement(
            self.agents, self.input_text, self.max_agents
        )
        run_dependency_declaration(self.agents, self.input_text)

        while select_next_drafter(self.agents) is not None:
            run_draft_pass(self.agents, self.input_text)

        run_output_refinement(self.agents, self.input_text)
        return self.agents


def create_graph(
    input_text: str,
    num_agents: int,
    max_agents: int,
) -> ARISEGraph:
    """Create the peer-to-peer graph with initial agent instances."""
    agents = create_agents(num_agents)
    return ARISEGraph(
        agents=agents,
        input_text=input_text,
        max_agents=max_agents,
    )
