from __future__ import annotations

from typing import Literal

from ARISE.agents.prompts import build_user_prompt
from ARISE.llm.client import BedrockClient
from ARISE.messages import Message


class GenericAgent:
    def __init__(self, agent_id: int, llm: BedrockClient) -> None:
        self.agent_id = agent_id
        self.llm = llm
        self.role: str | None = None
        self.output: str | None = None
        self.phase: Literal["active", "done"] = "active"

    def __str__(self) -> str:
        return (
            f"Agent {self.agent_id}: {self.role}, "
            f"Output={self.output}, Phase={self.phase}"
        )

    def take_turn(self, inbox: list[Message], agents: list[GenericAgent],) -> tuple[list[Message], list[str]]:
        print(f"Agent {self.agent_id} taking turn with messages {inbox}")
        actions = self.llm.parse_turn(build_user_prompt(inbox, agents, self.agent_id))

        outbound: list[Message] = []
        spawn_roles: list[str] = []

        for action in actions:
            match action.action:
                case "assign_role":
                    self.role = action.content
                case "write_output":
                    self.output = action.content
                    self.phase = "done"
                case "message":
                    outbound.append(
                        Message(self.agent_id, action.recipient_id, action.content)
                    )
                case "create_agent":
                    spawn_roles.append(action.content)
        print(f"Agent {self.agent_id} taking turn with actions {outbound}")
        return outbound, spawn_roles
