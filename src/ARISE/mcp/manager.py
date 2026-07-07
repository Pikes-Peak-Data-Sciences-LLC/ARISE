from __future__ import annotations

import asyncio
import json
import logging
import threading

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ARISE.mcp.registry import MCPServerConfig

logger = logging.getLogger(__name__)


def _format_arg(name: str, schema: dict, required: set[str]) -> str:
    type_name = schema.get("type", "any")
    if "anyOf" in schema:
        type_name = " | ".join(
            option.get("type", "any") for option in schema["anyOf"] if isinstance(option, dict)
        )
    parts = [f"{name} ({type_name}"]
    if name in required:
        parts.append(", required")
    else:
        parts.append(", optional")
    if "default" in schema:
        parts.append(f", default: {schema['default']}")
    if "minimum" in schema:
        parts.append(f", min: {schema['minimum']}")
    if "maximum" in schema:
        parts.append(f", max: {schema['maximum']}")
    description = schema.get("description")
    if description:
        parts.append(f", {description}")
    parts.append(")")
    return "".join(parts)


def _format_input_schema(input_schema: dict) -> str:
    properties = input_schema.get("properties") or {}
    if not properties:
        return "args: none"
    required = set(input_schema.get("required") or [])
    arg_lines = [
        _format_arg(name, prop, required)
        for name, prop in properties.items()
        if isinstance(prop, dict)
    ]
    return "args: " + "; ".join(arg_lines)


class MCPManager:
    def __init__(self, servers: list[MCPServerConfig]) -> None:
        self._servers = {server.id: server for server in servers}
        self._tools: dict[str, list] = {}
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._started = False

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def start(self) -> None:
        if not self._servers or self._started:
            return
        self._thread.start()
        for server in self._servers.values():
            tools = self._run(self._list_tools(server))
            self._tools[server.id] = tools
            logger.info(
                "Registered MCP server %s with tools: %s",
                server.id,
                [tool.name for tool in tools],
            )
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._tools.clear()
        self._started = False

    def tools_prompt(self) -> str:
        lines: list[str] = []
        for server_id, tools in self._tools.items():
            for tool in tools:
                description = (tool.description or "").strip()
                args = _format_input_schema(tool.inputSchema)
                lines.append(f"- {server_id}/{tool.name}: {description}")
                lines.append(f"  {args}")
        return "\n".join(lines) if lines else "None."

    def call_tool(self, server_id: str, tool_name: str, arguments: dict) -> str:
        if server_id not in self._servers:
            raise ValueError(f"Unknown MCP server: {server_id}")
        return self._run(self._call_tool(self._servers[server_id], tool_name, arguments))

    def _run(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    async def _with_session(self, server: MCPServerConfig, fn):
        params = StdioServerParameters(
            command=server.command,
            args=server.args,
            env=server.env,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await fn(session)

    async def _list_tools(self, server: MCPServerConfig):
        async def list_tools(session: ClientSession):
            response = await session.list_tools()
            return response.tools

        return await self._with_session(server, list_tools)

    async def _call_tool(self, server: MCPServerConfig, tool_name: str, arguments: dict) -> str:
        async def invoke(session: ClientSession) -> str:
            result = await session.call_tool(tool_name, arguments=arguments)
            parts: list[str] = []
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
                else:
                    parts.append(str(block))
            if parts:
                return "\n".join(parts)
            return json.dumps(result.model_dump(), default=str)

        return await self._with_session(server, invoke)


def parse_tool_call(content: str) -> tuple[str, str, dict]:
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("call_tool content must be a JSON object")
    server = data.get("server")
    tool = data.get("tool")
    if not server or not tool:
        raise ValueError("call_tool content must include server and tool")
    args = data.get("args") or data.get("arguments") or {}
    if not isinstance(args, dict):
        raise ValueError("call_tool args must be a JSON object")
    return str(server), str(tool), args
