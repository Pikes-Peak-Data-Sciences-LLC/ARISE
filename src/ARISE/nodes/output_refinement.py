from ARISE.agents.generic_agent import GenericAgent


def run_output_refinement(agents: list[GenericAgent], input_text: str) -> None:
    """Each agent refines its own draft by reading peer outputs."""
    for agent in agents:
        peers = [peer for peer in agents if peer is not agent]
        agent.refine_output(peers, input_text)
