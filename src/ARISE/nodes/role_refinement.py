from ARISE.agents.generic_agent import GenericAgent


def run_role_refinement(
    agents: list[GenericAgent],
    input_text: str,
    max_agents: int,
) -> list[GenericAgent]:
    """Each agent refines its role or proposes a new peer; returns updated roster."""
    raise NotImplementedError
