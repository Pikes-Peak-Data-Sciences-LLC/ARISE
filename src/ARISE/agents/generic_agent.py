from __future__ import annotations

import logging
import json
from typing import Literal

from ARISE.agents.prompts import build_user_prompt
from ARISE.config import OUTPUT_CHARACTER_LIMIT
from ARISE.llm.client import BedrockClient
from ARISE.mcp.manager import MCPManager, parse_tool_call
from ARISE.models.schema import Message

logger = logging.getLogger(__name__)


class GenericAgent:
    def __init__(self, agent_id: int, llm: BedrockClient, mcp: MCPManager | None = None) -> None:
        self.agent_id = agent_id
        self.llm = llm
        self.mcp = mcp
        self.role: str | None = None
        self.output: str | None = None
        self.status: Literal["active", "done"] = "active"

    def __str__(self) -> str:
        return f"Agent {self.agent_id}: {self.role}, Status={self.status}"

    def take_turn(self, inbox: list[Message], agents: list[GenericAgent],) -> tuple[list[Message], list[str]]:
        logging.info(f"Agent {self.agent_id} ({self.role}) has received the following messages:")
        [logging.info(message) for message in inbox]
        actions = self.llm.parse_turn(build_user_prompt(inbox, agents,self.agent_id))
        self.write_to_json(actions)

        outbound: list[Message] = []
        spawn_roles: list[str] = []
        for action in actions:
            match action.action:
                case "assign_role":
                    logging.info(f"Agent {self.agent_id} assigned role: {action.content}")
                    self.role = action.content.split(":")[0].strip()
                    self.llm.update_system_prompt(action.content)

                case "write_output":
                    if len(action.content) > OUTPUT_CHARACTER_LIMIT:
                        logging.error(f"Agent {self.agent_id} ({self.role}) wrote output: {action.content} is too long. It must be less than {OUTPUT_CHARACTER_LIMIT} characters.")
                        outbound.append(Message(self.agent_id, self.agent_id, f"Output error: Previous output is {len(action.content)} characters, which exceeds the character limit of {OUTPUT_CHARACTER_LIMIT}. Please trim your output or split your responsibilities into multiple agents."))
                    else:
                        logging.info(f"Agent {self.agent_id} ({self.role}) wrote output: {action.content}")
                        self.output = action.content
                        self.status = "done"

                case "message":
                    logging.info(f"Agent {self.agent_id} ({self.role}) sent message to Agent {action.recipient_id}: {action.content}")
                    if action.recipient_id != self.agent_id: #reject messages to self
                        outbound.append(Message(self.agent_id, action.recipient_id, action.content))

                case "create_agent":
                    logging.info(f"Agent {self.agent_id} ({self.role}) created agent: {action.content}")
                    spawn_roles.append(action.content)

                case "delete_agent":
                    logging.info(f"Agent {self.agent_id} ({self.role}) deleted agent: {action.content}")
                    # TODO

                case "query_output":
                    logging.info(f"Agent {self.agent_id} ({self.role}) queried output from Agent {action.recipient_id}")
                    requested_agent = None
                    for agent in agents:
                        if agent.agent_id == action.recipient_id:
                            requested_agent = agent
                            requested_output = agent.output
                            break
                    if requested_agent is None:
                        logging.error(f"Agent {self.agent_id} ({self.role}) requested output from Agent {action.recipient_id}, but they do not exist.")
                    elif requested_agent.status == "done":
                        outbound.append(Message(self.agent_id, self.agent_id, f"Requested output from Agent {action.recipient_id}: {requested_output}"))
                    else:
                        logging.info(f"Agent {self.agent_id} ({self.role}) requested output from Agent {action.recipient_id}, but they are not done.")

                case "call_tool":
                    if self.mcp is None:
                        logger.error("Agent %s called a tool, but MCP is not configured", self.agent_id)
                        outbound.append(self._self_message("Tool error: MCP is not configured."))
                        continue
                    try:
                        server_id, tool_name, arguments = parse_tool_call(action.content)
                        logger.info("Agent %s called tool %s/%s with args %s", self.agent_id, server_id,tool_name,arguments,)
                        result = self.mcp.call_tool(server_id, tool_name, arguments)
                        outbound.append(
                            Message(
                                self.agent_id,
                                self.agent_id,
                                f"Tool result ({server_id}/{tool_name}): {result}",
                            )
                        )
                    except Exception as exc:
                        logging.error("Agent %s tool call failed: %s", self.agent_id, exc)
                        outbound.append(
                            Message(self.agent_id, self.agent_id, f"Tool error ({action.content}): {exc}")
                        )

        return outbound, spawn_roles
    
    def write_to_json(self, lines: dict):
        with open('action_log.jsonl', mode='a') as file:
            for line in lines:
                file.write(json.dumps({"agent_id": self.agent_id, "agent_role": self.role,"action": line.action, "recipient_id": line.recipient_id, "content": line.content}) + "\n")
