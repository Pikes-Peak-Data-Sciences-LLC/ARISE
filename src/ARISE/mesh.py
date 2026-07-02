from __future__ import annotations

from ARISE.agents.generic_agent import GenericAgent
from ARISE.agents.prompts import system_prompt
from ARISE.llm.client import BedrockClient
from ARISE.messages import Message


class ARISEMesh:
    def __init__(self, input_text: str, num_agents: int, max_agents: int) -> None:
        self.input_text = input_text
        self.max_agents = max_agents
        self.agents = [
            GenericAgent(
                agent_id=i,
                llm=BedrockClient(system_prompt(i, num_agents, max_agents, input_text)),
            )
            for i in range(num_agents)
        ]
        self.mailboxes = {agent.agent_id: [] for agent in self.agents}
        self._max_steps = 1000

    def run(self) -> list[GenericAgent]:
        self.mailboxes[0].append(Message(sender_id=-1, recipient_id=0, content="Begin role assignment."))
        wake = [0]
        steps = 0

        while wake and not self.is_done() and steps < self._max_steps:
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

    def is_done(self) -> bool:
        return all(agent.phase == "done" for agent in self.agents)
