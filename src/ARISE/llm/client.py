"""LLM client initialization."""

from __future__ import annotations

import json
import logging
from typing import Any

import boto3

from ARISE.config import AWS_REGION,BEDROCK_MODEL,MAX_RETRIES,MAX_TOKENS,MEMORY_WINDOW,OUTPUT_CHARACTER_LIMIT,TEMPERATURE,resolve_bedrock_model_id
from ARISE.models.schema import AgentAction, TurnResponse, parse_actions
import re

logger = logging.getLogger(__name__)

MAX_TOKENS_STOP_REASON = "max_tokens"
_TRUNCATION_RETRY_SUFFIX = (
    "\n\nIMPORTANT: Your previous response was truncated because it exceeded the token limit. "
    "Try again with fewer actions in one turn, shorter message content, and a much shorter "
    f"write_output (under {OUTPUT_CHARACTER_LIMIT} characters). Do not repeat the full prior answer."
)


def _set_additional_properties_false(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            node["additionalProperties"] = False
        for value in node.values():
            _set_additional_properties_false(value)
    elif isinstance(node, list):
        for item in node:
            _set_additional_properties_false(item)


def _bedrock_json_schema() -> str:
    schema = TurnResponse.model_json_schema()
    _set_additional_properties_false(schema)
    return json.dumps(schema)


class BedrockClient:
    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        self.model = resolve_bedrock_model_id(BEDROCK_MODEL, AWS_REGION)
        self.history: list[dict[str, Any]] = []
        self.memory_window = MEMORY_WINDOW
        self.region = AWS_REGION
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS
        self.max_retries = MAX_RETRIES
        self._client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    def _converse(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return self._client.converse(
            modelId=self.model,
            system=[{"text": self.system_prompt}],
            messages=messages,
            inferenceConfig={
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
            },
            outputConfig={
                "textFormat": {
                    "type": "json_schema",
                    "structure": {
                        "jsonSchema": {
                            "name": "turn_actions",
                            "description": "Actions for the agent's turn",
                            "schema": _bedrock_json_schema(),
                        }
                    },
                }
            },
        )

    def complete(self, user_message: str) -> str:
        attempt_message = user_message
        max_attempts = self.max_retries + 1

        for attempt in range(max_attempts):
            new_message = {"role": "user", "content": [{"text": attempt_message}]}
            response = self._converse(self.history + [new_message])
            stop_reason = response.get("stopReason", "unknown")
            content = response.get("output", {}).get("message", {}).get("content", [])
            text_parts = [block["text"] for block in content if "text" in block]
            assistant_text = "\n".join(text_parts).strip()

            if stop_reason == MAX_TOKENS_STOP_REASON:
                if attempt < self.max_retries:
                    logger.warning(
                        "Model hit max_tokens on attempt %s/%s; retrying with shorter-output instruction",
                        attempt + 1,
                        max_attempts,
                    )
                    attempt_message = user_message + _TRUNCATION_RETRY_SUFFIX
                    continue
                raise ValueError(
                    f"Model response exceeded max tokens after {max_attempts} attempt(s)"
                )

            if not text_parts:
                raise ValueError(
                    f"Model response did not include text output (stopReason={stop_reason})"
                )

            if len(self.history) > self.memory_window:
                self.history.pop(0)
            self.history.append(new_message)
            self.history.append({"role": "assistant", "content": [{"text": assistant_text}]})
            return assistant_text

        raise ValueError(f"Model response exceeded max tokens after {max_attempts} attempt(s)")

    def parse_turn(self, user_message: str) -> list[AgentAction]:
        agent_answer = self.complete(user_message)
        logger.info("Agent Output: %s", agent_answer)
        try:
            return parse_actions(json.loads(agent_answer))
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Agent answer: {agent_answer}")
            raise e

    def update_system_prompt(self, new_role: str) -> str:
        new_prompt = re.sub(r'<[^>]*>', f"<{new_role}>", self.system_prompt)
        self.system_prompt = new_prompt
