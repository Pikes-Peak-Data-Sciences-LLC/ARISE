from ARISE.agents.generic_agent import GenericAgent

def run_draft_pass(agents: list[GenericAgent], input_text: str) -> None:
    unsatisfied_agents = agents.copy()
    while len(unsatisfied_agents) > 0:
        agent, status = select_next_drafter(unsatisfied_agents)
        peers = [peer for peer in agents if peer is not agent]
        agent.draft_output(peers, input_text)
        if status == "satisfied":
            unsatisfied_agents.remove(agent)

def select_next_drafter(agents: list[GenericAgent]) -> GenericAgent | None:
    ''' 
        If an agent has no dependencies, return that agent. 
        Otherwise, return the agent with all dependencies satisfied
        If no agent has all dependencies satisfied, return the agent with the highest ratio of dependencies satisfied
        and specify that their output is incomplete
    '''
    # Check if any agent has no dependencies
    for agent in agents:
        if len(agent.dependencies) == 0:
            return agent, "satisfied" #TODO: "satisfied" is hard coded, change

    # Check if any agent has all dependencies satisfied
    for agent in agents:
        if agent.get_ratio_satisfied() == 1:
            return agent, "satisfied" #TODO: "satisfied" is hard coded, change

    # If no agent has all dependencies satisfied, return the agent with the highest ratio of dependencies satisfied
    return max(agents, key=lambda x: x.get_ratio_satisfied()), "incomplete" #TODO: "incomplete" is hard coded, change
