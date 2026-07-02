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
    def __init__(self, input_text: str, num_agents: int, max_agents: int) -> None:
        self.num_agents = num_agents
        self.input_text = input_text
        self.max_agents = max_agents
        self.agents = create_agents(num_agents)

    def run(self) -> list[GenericAgent]:
        run_role_assignment(self.agents, self.input_text)
        self.agents = run_role_refinement(
            self.agents, self.input_text, self.max_agents
        )
        run_dependency_declaration(self.agents, self.input_text)

        while select_next_drafter(self.agents) is not None:
            run_draft_pass(self.agents, self.input_text)

        run_output_refinement(self.agents, self.input_text)
        return self.agents


def create_graph(input_text: str, num_agents: int, max_agents: int) -> ARISEGraph:
    return ARISEGraph(input_text=input_text, num_agents=num_agents, max_agents=max_agents)
