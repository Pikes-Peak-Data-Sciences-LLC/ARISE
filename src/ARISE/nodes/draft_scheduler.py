from ARISE.agents.generic_agent import GenericAgent


def select_next_drafter(agents: list[GenericAgent]) -> GenericAgent | None:
    """
    Pick the next agent eligible to draft.

    Prefer agents with no dependencies, then agents whose dependency peers
    already have outputs. Return None when every agent has drafted.
    """
    raise NotImplementedError
