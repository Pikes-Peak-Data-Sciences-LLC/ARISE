from __future__ import annotations

import logging

from ARISE.agents.generic_agent import GenericAgent
from ARISE.agents.prompts import new_task_prompt, nudge_prompt, rework_prompt
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
                llm=BedrockClient(
                    agent_id=i,
                    num_agents=num_agents,
                    max_agents=max_agents,
                    task=input_text,
                    tools=tools_prompt,
                ),
                mcp=self.mcp,
            )
            for i in range(num_agents)
        ]
        self.mailboxes = {agent.agent_id: [] for agent in self.agents}
        self._max_steps = MAX_STEPS
        self.rework_round = 0
        self._pending_wake: list[int] | None = None

    def _refresh_mesh_size(self) -> None:
        n = len(self.agents)
        self.num_agents = n
        for agent in self.agents:
            agent.llm.set_num_agents(n)

    def _get_agent(self, agent_id: int) -> GenericAgent | None:
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None

    def agents_finished(self) -> bool:
        return all(agent.status == "done" for agent in self.agents)

    def all_agents_have_roles(self) -> bool:
        return all(agent.role is not None for agent in self.agents)

    def _deliver_messages(self, outbound: list[Message], wake: list[int]) -> None:
        for message in outbound:
            if message.recipient_id not in self.mailboxes:
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
            agent = self._get_agent(agent_id)
            if agent is None or agent_id not in self.mailboxes:
                steps += 1
                continue

            inbox = self.mailboxes[agent_id]
            self.mailboxes[agent_id] = []

            if not inbox:
                steps += 1
                continue

            outbound, agent_changes = agent.take_turn(inbox, self.agents)
            self._deliver_messages(outbound, wake)

            for change in agent_changes:
                if change.action == "create_agent":
                    self.spawn_agent(change.content)
                elif change.action == "delete_agent":
                    self.delete_agent(change.recipient_id, wake)

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
        tools_prompt = self.mcp.tools_prompt()
        n = len(self.agents)
        for agent in self.agents:
            agent.status = "active"
            agent.output = None
            agent.llm.set_task(task)
            agent.llm.set_tools(tools_prompt)
            agent.llm.set_num_agents(n)
        starter_id = self.agents[0].agent_id
        self.mailboxes[starter_id].append(
            Message(sender_id=-1, recipient_id=starter_id, content=new_task_prompt(task))
        )
        self._pending_wake = [starter_id]

    def run(self) -> list[GenericAgent]:
        if self._pending_wake is not None:
            wake = self._pending_wake
            self._pending_wake = None
        else:
            starter_id = self.agents[0].agent_id
            self.mailboxes[starter_id].append(
                Message(
                    sender_id=-1,
                    recipient_id=starter_id,
                    content="Begin by assigning yourself a role.",
                )
            )
            wake = [starter_id]
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
        new_id = max((agent.agent_id for agent in self.agents), default=-1) + 1
        llm = BedrockClient(
            agent_id=new_id,
            num_agents=len(self.agents) + 1,
            max_agents=self.max_agents,
            task=self.input_text,
            tools=self.mcp.tools_prompt(),
        )
        self.agents.append(GenericAgent(agent_id=new_id, llm=llm, mcp=self.mcp))
        self.mailboxes[new_id] = []
        self._refresh_mesh_size()

    def delete_agent(self, agent_id: int, wake: list[int] | None = None) -> None:
        agent = self._get_agent(agent_id)
        if agent is None:
            logger.error("Cannot delete invalid agent id: %s", agent_id)
            return
        if len(self.agents) <= 1:
            logger.error("Cannot delete the last remaining agent")
            return

        self.agents.remove(agent)
        self.mailboxes.pop(agent_id, None)
        if wake is not None:
            wake[:] = [wid for wid in wake if wid != agent_id]
        if self._pending_wake is not None:
            self._pending_wake = [wid for wid in self._pending_wake if wid != agent_id]

        logging.info("Deleted agent %s (%s)", agent_id, agent.role)
        self._refresh_mesh_size()
