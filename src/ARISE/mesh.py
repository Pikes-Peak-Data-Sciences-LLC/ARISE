from __future__ import annotations

from ARISE.agents.generic_agent import GenericAgent
from ARISE.agents.prompts import *
from ARISE.llm.client import BedrockClient
from ARISE.models.schema import Message


class ARISEMesh:
    def __init__(self, input_text: str, num_agents: int, max_agents: int) -> None:
        self.input_text = input_text
        self.num_agents = num_agents
        self.max_agents = max_agents
        self.agents = [GenericAgent(agent_id=i, llm=BedrockClient(system_prompt(i, num_agents, max_agents, input_text))) for i in range(num_agents)]
        self.mailboxes = {agent.agent_id: [] for agent in self.agents}
        self._max_steps = 1000
        self.started_role_refinement = False
        self.started_output = False

    def agents_finished(self) -> bool:
        return all(agent.phase == "done" for agent in self.agents)

    def all_agents_have_roles(self) -> bool:
        return all(agent.role is not None for agent in self.agents)

    def run(self) -> list[GenericAgent]:
        self.mailboxes[0].append(Message(sender_id=-1, recipient_id=0, content=role_assignment_prompt(self.num_agents)))
        wake = [0]
        steps = 0

        while (wake or not self.agents_finished()) and steps < self._max_steps:
            if not self.started_role_refinement and self.all_agents_have_roles():
                self.mailboxes[0].append(Message(sender_id=-1, recipient_id=0, content=role_refinement_prompt(self.num_agents)))
                self.started_role_refinement = True
                wake.append(0)

            # begin output creation
            if not self.started_output and self.all_agents_have_roles() and self.started_role_refinement:
                self.mailboxes[0].append(Message(sender_id=-1, recipient_id=0, content=output_creation_prompt()))
                self.started_output = True
                wake.append(0)

            # if agents need a nudge
            if not wake:
                for agent in self.agents:
                    if agent.phase == "active":
                        self.mailboxes[agent.agent_id].append(Message(sender_id=-1, recipient_id=agent.agent_id, content=nudge_prompt()))
                        wake.append(agent.agent_id)
                        break

            agent_id = wake.pop(0)
            inbox = self.mailboxes[agent_id]
            self.mailboxes[agent_id] = []

            if not inbox:
                steps += 1
                continue

            outbound, spawn_roles = self.agents[agent_id].take_turn(inbox, self.agents)

            for message in outbound:
                self.mailboxes[message.recipient_id].append(message)
                wake.append(message.recipient_id)

            for role in spawn_roles:
                self.spawn_agent(role)

            steps += 1

        return self.agents

    def spawn_agent(self, _role: str) -> None:
        if len(self.agents) >= self.max_agents:
            return
        new_id = len(self.agents)
        llm = BedrockClient(
            system_prompt(new_id, new_id + 1, self.max_agents, self.input_text)
        )
        self.agents.append(GenericAgent(agent_id=new_id, llm=llm))
        self.mailboxes[new_id] = []
