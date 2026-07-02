"""Pydantic schemas for structured LLM responses."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, model_validator


class AgentAction(BaseModel):
    action: Literal["message", "assign_role", "write_output", "create_agent"]
    content: str
    recipient_id: int | None = None

    @model_validator(mode="after")
    def message_requires_recipient(self) -> AgentAction:
        if self.action == "message" and self.recipient_id is None:
            raise ValueError("recipient_id is required when action is 'message'")
        return self


def parse_actions(data: Any) -> list[AgentAction]:
    if isinstance(data, dict):
        data = data["actions"]
    return [AgentAction.model_validate(item) for item in data]
