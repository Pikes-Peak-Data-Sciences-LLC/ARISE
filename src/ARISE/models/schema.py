from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, model_validator


@dataclass
class Message:
    sender_id: int
    recipient_id: int
    content: str

class AgentAction(BaseModel):
    action: Literal["message", "assign_role", "write_output", "create_agent", "query_output", "call_tool", "delete_agent"]
    content: str
    recipient_id: int

    @model_validator(mode="after")
    def validate_fields(self) -> AgentAction:
        if self.action in ("message", "query_output") and self.recipient_id < 0:
            raise ValueError(f"recipient_id must be a valid agent ID for {self.action}")
        if self.action == "message" and not self.content.strip():
            raise ValueError("content is required for message")
        if self.action in ("assign_role", "write_output", "create_agent", "call_tool") and self.recipient_id != -1:
            raise ValueError(f"recipient_id must be -1 for {self.action}")
        if self.action == "call_tool" and not self.content.strip():
            raise ValueError("content is required for call_tool")
        if self.action == "delete_agent" and self.recipient_id < 0:
            raise ValueError("recipient_id must be a valid agent ID for delete_agent")
        return self

class TurnResponse(BaseModel):
    actions: list[AgentAction]


def parse_actions(data: Any) -> list[AgentAction]:
    if isinstance(data, dict):
        data = data["actions"]
    return [AgentAction.model_validate(item) for item in data]
