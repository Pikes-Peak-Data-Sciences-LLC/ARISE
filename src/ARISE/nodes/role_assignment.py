from ARISE.agents.generic_agent import GenericAgent


def run_role_assignment(agents: list[GenericAgent], input_text: str) -> None:
    for agent in agents:
        peers = [peer for peer in agents if peer is not agent]
        agent.assign_role(peers, input_text)
