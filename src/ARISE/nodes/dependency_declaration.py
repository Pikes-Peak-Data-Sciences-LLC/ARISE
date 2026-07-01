from ARISE.agents.generic_agent import GenericAgent


def run_dependency_declaration(agents: list[GenericAgent], input_text: str) -> None:
    """Each agent declares peer dependencies directly."""
    for agent in agents:
        peers = [peer for peer in agents if peer is not agent]
        agent.declare_dependencies(peers, input_text)
