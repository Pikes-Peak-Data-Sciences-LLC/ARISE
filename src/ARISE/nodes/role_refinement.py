from ARISE.agents.generic_agent import GenericAgent


def run_role_refinement(agents: list[GenericAgent], input_text: str, max_agents: int) -> list[GenericAgent]:
    for agent in agents:
        peers = [peer for peer in agents if peer is not agent]
        agent.refine_role(peers, input_text, max_agents)
    return agents