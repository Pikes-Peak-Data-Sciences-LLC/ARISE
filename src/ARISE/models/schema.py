from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, model_validator


@dataclass
class Message:
    sender_id: int
    recipient_id: int
    content: str

    def __repr__(self) -> str:
        return f"\tMessage from Agent {self.sender_id} to Agent {self.recipient_id}: {self.content}\n"


class AgentAction(BaseModel):
    action: Literal["message", "assign_role", "write_output", "create_agent", "query_output"]
    content: str
    recipient_id: int

    @model_validator(mode="after")
    def validate_fields(self) -> AgentAction:
        if self.action in ("message", "query_output") and self.recipient_id < 0:
            raise ValueError(f"recipient_id must be a valid agent ID for {self.action}")
        if self.action == "message" and not self.content.strip():
            raise ValueError("content is required for message")
        if self.action in ("assign_role", "write_output", "create_agent") and self.recipient_id != -1:
            raise ValueError(f"recipient_id must be -1 for {self.action}")
        return self

    def __repr__(self) -> str:
        if self.action in ("message", "query_output"):
            return f"\tAction {self.action} to Agent {self.recipient_id}: {self.content}\n"
        return f"\tAction {self.action}: {self.content}\n"

    def __str__(self) -> str:
        return self.__repr__()


class TurnResponse(BaseModel):
    actions: list[AgentAction]


def parse_actions(data: Any) -> list[AgentAction]:
    if isinstance(data, dict):
        data = data["actions"]
    return [AgentAction.model_validate(item) for item in data]
