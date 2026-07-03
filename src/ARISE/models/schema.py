from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, model_validator

from dataclasses import dataclass


@dataclass
class Message:
    sender_id: int
    recipient_id: int
    content: str

    def __repr__(self) -> str:
        return f"\tMessage from Agent {self.sender_id} to Agent {self.recipient_id}: {self.content}\n"

class AgentAction(BaseModel):
    action: Literal["message", "assign_role", "write_output", "create_agent"]
    content: str
    recipient_id: int | None = None

    @model_validator(mode="after")
    def message_requires_recipient(self) -> AgentAction:
        if self.action == "message" and self.recipient_id is None:
            raise ValueError("recipient_id is required when action is 'message'")
        return self

    def __repr__(self) -> str:
        if self.action == "message":
            return f"\tAction {self.action} to Agent {self.recipient_id}: {self.content}\n"
        return f"\tAction {self.action}: {self.content}\n"
    def __str__(self) -> str:
        return self.__repr__()

def parse_actions(data: Any) -> list[AgentAction]:
    if isinstance(data, dict):
        data = data["actions"]
    return [AgentAction.model_validate(item) for item in data]
