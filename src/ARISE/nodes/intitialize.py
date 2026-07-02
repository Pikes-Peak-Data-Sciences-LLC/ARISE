from ARISE.agents.generic_agent import GenericAgent


def create_agents(num_agents: int) -> list[GenericAgent]:
    agents = []
    for i in range(num_agents):
        agents.append(GenericAgent(agent_id=f"Agent {i}"))
    return agents
