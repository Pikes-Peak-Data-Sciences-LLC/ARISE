from __future__ import annotations


class GenericAgent:
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.role: str | None = None
        self.dependencies: list[str] = []
        self.draft: str | None = None
        self.output: str | None = None
    
    def __str__(self) -> str:
        return f"Agent {self.agent_id}: {self.role}, Dependencies={self.dependencies}, Draft={self.draft}, Output={self.output}"

    def __repr__(self) -> str:
        return f"Agent {self.agent_id}: {self.role}"

    def get_ratio_satisfied(self) -> float:
        total_dependencies = len(self.dependencies)
        satisfied_dependencies = 0
        if total_dependencies == 0:
            return 1
        for dependency in self.dependencies:
            if dependency.draft is not None:
                satisfied_dependencies += 1
        return satisfied_dependencies / total_dependencies

    def assign_role(self, peers: list[GenericAgent], input_text: str) -> None:
        self.role = "Planner" #TODO: Implement role assignment

    def refine_role(self, peers: list[GenericAgent], input_text: str, max_agents: int) -> None:
        self.role = "Improved Planner" #TODO: Implement role refinement

    def declare_dependencies(self, peers: list[GenericAgent], input_text: str) -> None:
        # for now, just get a random number of dependencies 
        # TODO: Implement dependency declaration
        import random
        num_dependencies = random.randint(0, len(peers))
        self.dependencies = random.sample(peers, k=num_dependencies)

    def temp_draft_output(self) -> str:
        self.draft = "this is a temporary draft since I do not have the required information"

    def draft_output(self, peers: list[GenericAgent], input_text: str) -> None:
        self.draft = "this is a draft" #TODO: Implement draft output

    def refine_output(self, peers: list[GenericAgent], input_text: str) -> None:
        self.output = "this is the final output" #TODO: Implement output refinement
