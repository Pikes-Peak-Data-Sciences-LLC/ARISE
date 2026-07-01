from ARISE.agents.generic_agent import GenericAgent
from ARISE.nodes.draft_scheduler import select_next_drafter


def run_draft_pass(agents: list[GenericAgent], input_text: str) -> None:
    """Have the next eligible agent draft using peer outputs."""
    agent = select_next_drafter(agents)
    if agent is None:
        return
    peers = [peer for peer in agents if peer is not agent]
    agent.draft_output(peers, input_text)
