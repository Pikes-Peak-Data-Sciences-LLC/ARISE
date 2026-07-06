"""LLM client initialization."""

from __future__ import annotations

import json
import logging
from typing import Any

import boto3

from ARISE.config import AWS_REGION, BEDROCK_MODEL, MAX_TOKENS, TEMPERATURE, resolve_bedrock_model_id
from ARISE.models.schema import AgentAction, TurnResponse, parse_actions

logger = logging.getLogger(__name__)


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
        self.region = AWS_REGION
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS
        self._client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    def complete(self, user_message: str) -> str:
        new_message = {"role": "user", "content": [{"text": user_message}]}
        response = self._client.converse(
            modelId=self.model,
            system=[{"text": self.system_prompt}],
            messages=self.history + [new_message],
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
        content = response.get("output", {}).get("message", {}).get("content", [])
        text_parts = [block["text"] for block in content if "text" in block]
        assistant_text = "\n".join(text_parts).strip()
        self.history.append(new_message)
        self.history.append({"role": "assistant", "content": [{"text": assistant_text}]})
        if text_parts:
            return assistant_text

        stop_reason = response.get("stopReason", "unknown")
        raise ValueError(
            f"Model response did not include text output (stopReason={stop_reason})"
        )

    def parse_turn(self, user_message: str) -> list[AgentAction]:
        agent_answer = self.complete(user_message)
        logger.info("Agent Output: %s", agent_answer)
        try:
            return parse_actions(json.loads(agent_answer))
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Agent answer: {agent_answer}")
            raise e
