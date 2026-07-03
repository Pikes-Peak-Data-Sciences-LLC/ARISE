"""LLM client initialization."""

from __future__ import annotations

import json
import re

import boto3

from ARISE.config import AWS_REGION, BEDROCK_MODEL, resolve_bedrock_model_id
from ARISE.models.schema import AgentAction, parse_actions


def extract_json(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch not in "{[":
            continue
        try:
            _, end = decoder.raw_decode(text, i)
            return text[i:end]
        except json.JSONDecodeError:
            continue
    return text

class BedrockClient:
    def __init__(self, system_prompt: str, model: str = BEDROCK_MODEL, region: str = AWS_REGION, temperature: float = 0.2, max_tokens: int = 2048,) -> None:
        self.system_prompt = system_prompt
        self.model = resolve_bedrock_model_id(model, region)
        self.history: list[dict[str, Any]] = []
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def complete(self, user_message: str) -> str:
        new_message = {"role": "user", "content": [{"text": user_message}]}
        response = self._client.converse(
            modelId=self.model,
            system=[{"text": self.system_prompt}],
            messages= self.history + [new_message],
            inferenceConfig={
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        )
        content = response.get("output", {}).get("message", {}).get("content", [])
        text_parts = [block["text"] for block in content if "text" in block]
        assistant_text = "\n".join(text_parts).strip()
        self.history.append(new_message)
        self.history.append({"role": "assistant", "content": [{"text": assistant_text}]})
        if text_parts:
            return "\n".join(text_parts).strip()

        stop_reason = response.get("stopReason", "unknown")
        raise ValueError(
            f"Model response did not include text output (stopReason={stop_reason})"
        )

    def parse_turn(self, user_message: str) -> list[AgentAction]:
        data = json.loads(extract_json(self.complete(user_message)))
        return parse_actions(data)
