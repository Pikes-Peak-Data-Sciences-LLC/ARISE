from __future__ import annotations

from typing import Literal

from ARISE.agents.prompts import build_user_prompt
from ARISE.llm.client import BedrockClient
from ARISE.models.schema import Message
import logging


class GenericAgent:
    def __init__(self, agent_id: int, llm: BedrockClient) -> None:
        self.agent_id = agent_id
        self.llm = llm
        self.role: str | None = None
        self.output: str | None = None
        self.phase: Literal["active", "done"] = "active"
        logger = logging.getLogger(__name__)

    def __str__(self) -> str:
        return (
            f"Agent {self.agent_id}: {self.role}, Phase={self.phase}"
        )

    def take_turn(self, inbox: list[Message], agents: list[GenericAgent],) -> tuple[list[Message], list[str]]:
        logging.info(f"Agent {self.agent_id} has received the following messages:")
        [logging.info(message) for message in inbox]
        actions = self.llm.parse_turn(build_user_prompt(inbox, agents, self.agent_id))

        outbound: list[Message] = []
        spawn_roles: list[str] = []

        for action in actions:
            match action.action:
                case "assign_role":
                    logging.info(f"Agent {self.agent_id} assigned role: {action.content}")
                    self.role = action.content
                case "write_output":
                    self.output = action.content
                    self.phase = "done"
                case "message":
                    logging.info(f"Agent {self.agent_id} sent message to Agent {action.recipient_id}: {action.content}")
                    if action.recipient_id != self.agent_id: #reject messages to self
                        outbound.append(Message(self.agent_id, action.recipient_id, action.content))
                case "create_agent":
                    logging.info(f"Agent {self.agent_id} created agent: {action.content}")
                    spawn_roles.append(action.content)
        logging.info(f"Agent {self.agent_id} took turn with actions:")
        [logging.info(action) for action in actions]
        return outbound, spawn_roles
