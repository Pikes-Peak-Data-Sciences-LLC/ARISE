from __future__ import annotations

import logging

from ARISE.agents.generic_agent import GenericAgent
from ARISE.agents.prompts import new_task_prompt, nudge_prompt, rework_prompt, system_prompt
from ARISE.config import MAX_STEPS, REWORK_PASSES
from ARISE.llm.client import BedrockClient
from ARISE.mcp.manager import MCPManager
from ARISE.mcp.registry import load_mcp_servers
from ARISE.models.schema import Message

logger = logging.getLogger(__name__)


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
        self._pending_wake: list[int] | None = None

    def agents_finished(self) -> bool:
        return all(agent.status == "done" for agent in self.agents)

    def all_agents_have_roles(self) -> bool:
        return all(agent.role is not None for agent in self.agents)

    def _deliver_messages(self, outbound: list[Message], wake: list[int]) -> None:
        for message in outbound:
            if message.recipient_id < 0 or message.recipient_id >= len(self.agents):
                logger.error("Invalid recipient id: %s", message.recipient_id)
                continue
            self.mailboxes[message.recipient_id].append(message)
            wake.append(message.recipient_id)

    def _nudge_next_active_agent(self, wake: list[int]) -> None:
        for agent in self.agents:
            if agent.status == "active":
                self.mailboxes[agent.agent_id].append(
                    Message(sender_id=-1, recipient_id=agent.agent_id, content=nudge_prompt(self))
                )
                wake.append(agent.agent_id)
                break

    def _run_round(self, wake: list[int], steps: int) -> tuple[list[int], int]:
        while (wake or not self.agents_finished()) and steps < self._max_steps:
            if not wake:
                self._nudge_next_active_agent(wake)

            agent_id = wake.pop(0)
            inbox = self.mailboxes[agent_id]
            self.mailboxes[agent_id] = []

            if not inbox:
                steps += 1
                continue

            outbound, spawn_roles = self.agents[agent_id].take_turn(inbox, self.agents)
            self._deliver_messages(outbound, wake)

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
            self.mailboxes[agent.agent_id].append(
                Message(
                    sender_id=-1,
                    recipient_id=agent.agent_id,
                    content=rework_prompt(self, agent.agent_id),
                )
            )
            wake.append(agent.agent_id)
        return wake

    def begin_new_task(self, task: str) -> None:
        """Reset agent status and queue a new task for the existing mesh."""
        logging.info("Starting new task: %s", task)
        self.input_text = task
        self.rework_round = 0
        self.mailboxes = {agent.agent_id: [] for agent in self.agents}
        n = len(self.agents)
        tools_prompt = self.mcp.tools_prompt()
        for agent in self.agents:
            agent.status = "active"
            agent.output = None
            agent.llm.system_prompt = system_prompt(
                agent.agent_id, n, self.max_agents, task, tools_prompt
            )
            if agent.role:
                agent.llm.update_system_prompt(agent.role)
        self.mailboxes[0].append(
            Message(sender_id=-1, recipient_id=0, content=new_task_prompt(task))
        )
        self._pending_wake = [0]

    def run(self) -> list[GenericAgent]:
        if self._pending_wake is not None:
            wake = self._pending_wake
            self._pending_wake = None
        else:
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

    def shutdown(self) -> None:
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
