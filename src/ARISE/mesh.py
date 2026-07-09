from __future__ import annotations

import logging

from ARISE.agents.generic_agent import GenericAgent
from ARISE.agents.prompts import nudge_prompt, rework_prompt, system_prompt
from ARISE.config import MAX_STEPS, REWORK_PASSES
from ARISE.llm.client import BedrockClient
from ARISE.mcp.registry import load_mcp_servers
from ARISE.mcp.manager import MCPManager
from ARISE.models.schema import Message


class ARISEMesh:
    def __init__(self, input_text: str, num_agents: int, max_agents: int) -> None:
        self.input_text = input_text
        self.num_agents = num_agents
        self.max_agents = max_agents
        self.mcp = MCPManager(load_mcp_servers())
        self.mcp.start()
        tools_prompt = self.mcp.tools_prompt()
        self.agents = [
            GenericAgent(
                agent_id=i,
                llm=BedrockClient(system_prompt(i, num_agents, max_agents, input_text, tools_prompt)),
                mcp=self.mcp,
            )
            for i in range(num_agents)
        ]
        self.mailboxes = {agent.agent_id: [] for agent in self.agents}
        self._max_steps = MAX_STEPS
        self.rework_round = 0

    def agents_finished(self) -> bool:
        return all(agent.status == "done" for agent in self.agents)

    def all_agents_have_roles(self) -> bool:
        return all(agent.role != "unassigned" for agent in self.agents)

    def _run_round(self, wake: list[int], steps: int) -> tuple[list[int], int]:
        while (wake or not self.agents_finished()) and steps < self._max_steps:
            if not wake:
                for agent in self.agents:
                    if agent.status == "active":
                        self.mailboxes[agent.agent_id].append(
                            Message(sender_id=-1, recipient_id=agent.agent_id, content=nudge_prompt(self))
                        )
                        wake.append(agent.agent_id)
                        break # nudge only the first active agent

            agent_id = wake.pop(0)
            inbox = self.mailboxes[agent_id]
            self.mailboxes[agent_id] = []

            if not inbox:
                steps += 1
                continue

            outbound, spawn_roles = self.agents[agent_id].take_turn(inbox, self.agents)

            for message in outbound:
                if message.recipient_id < 0 or message.recipient_id >= len(self.agents):
                    logging.error(f"Invalid recipient id: {message.recipient_id}")
                    continue
                self.mailboxes[message.recipient_id].append(message)
                wake.append(message.recipient_id)

            for role in spawn_roles:
                self.spawn_agent(role)

            steps += 1

        return wake, steps

    def _start_rework(self) -> list[int]:
        self.rework_round += 1
        logging.info("Starting rework pass %s of %s", self.rework_round, REWORK_PASSES)
        wake: list[int] = []
        for agent in self.agents:
            agent.status = "active"
            self.mailboxes[agent.agent_id].append(Message(sender_id=-1, recipient_id=agent.agent_id, content=rework_prompt(self, agent.agent_id)))
            wake.append(agent.agent_id)
        return wake

    def run(self) -> list[GenericAgent]:
        try:
            self.mailboxes[0].append(
                Message(sender_id=-1, recipient_id=0, content="Begin by assigning yourself a role.")
            )
            wake = [0]
            steps = 0

            while True:
                wake, steps = self._run_round(wake, steps)

                if not self.agents_finished():
                    break
                if self.rework_round >= REWORK_PASSES:
                    break

                wake = self._start_rework()

            return self.agents
        finally:
            self.mcp.stop()

    def spawn_agent(self, _role: str) -> None:
        if len(self.agents) >= self.max_agents:
            return
        new_id = len(self.agents)
        llm = BedrockClient(
            system_prompt(new_id, new_id + 1, self.max_agents, self.input_text, self.mcp.tools_prompt())
        )
        self.agents.append(GenericAgent(agent_id=new_id, llm=llm, mcp=self.mcp))
        self.mailboxes[new_id] = []
