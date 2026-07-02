from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Message:
    sender_id: int
    recipient_id: int
    content: str
