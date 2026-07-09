from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Awaitable, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ARISE.mcp.registry import MCPServerConfig

logger = logging.getLogger(__name__)


def _tool_result_text(result) -> str:
    parts: list[str] = []
    for block in result.content:
        text = getattr(block, "text", None)
        parts.append(text if text else str(block))
    if parts:
        return "\n".join(parts)
    return json.dumps(result.model_dump(), default=str)


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


def _format_tool_args(input_schema: dict | None) -> str:
    if not input_schema:
        return "  Args: none"
    properties = input_schema.get("properties") or {}
    if not properties:
        return "  Args: none"
    required = set(input_schema.get("required") or [])
    arg_lines: list[str] = []
    for name, spec in properties.items():
        if not isinstance(spec, dict):
            arg_lines.append(f"  - {name}")
            continue
        arg_type = spec.get("type", "any")
        requirement = "required" if name in required else "optional"
        details = [arg_type, requirement]
        if "default" in spec:
            details.append(f"default={spec['default']!r}")
        description = (spec.get("description") or "").strip()
        line = f"  - {name} ({', '.join(details)})"
        if description:
            line += f": {description}"
        arg_lines.append(line)
    return "\n".join(arg_lines)


def _format_tool_prompt(server_id: str, tool) -> str:
    description = (tool.description or "").strip()
    header = f"- {server_id}/{tool.name}"
    if description:
        header += f": {description}"
    return f"{header}\n{_format_tool_args(getattr(tool, 'inputSchema', None))}"


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
        for server_id in list(self._servers):
            server = self._servers[server_id]
            try:
                tools = self._run(self._list_tools(server))
            except Exception as exc:
                logger.warning("Failed to register MCP server %s: %s", server_id, exc)
                del self._servers[server_id]
                continue
            self._tools[server_id] = tools
            logger.info(
                "Registered MCP server %s with tools: %s",
                server_id,
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
        lines = [
            _format_tool_prompt(server_id, tool)
            for server_id, tools in self._tools.items()
            for tool in tools
        ]
        return "\n".join(lines) if lines else "None."

    def call_tool(self, server_id: str, tool_name: str, arguments: dict) -> str:
        if server_id not in self._servers:
            raise ValueError(f"Unknown MCP server: {server_id}")
        server = self._servers[server_id]
        return self._run(self._call_tool(server, tool_name, arguments))

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    async def _with_session(
        self,
        server: MCPServerConfig,
        fn: Callable[[ClientSession], Awaitable],
    ):
        params = StdioServerParameters(command=server.command, args=server.args)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await fn(session)

    async def _list_tools(self, server: MCPServerConfig):
        async def list_tools(session: ClientSession):
            return (await session.list_tools()).tools

        return await self._with_session(server, list_tools)

    async def _call_tool(self, server: MCPServerConfig, tool_name: str, arguments: dict) -> str:
        async def invoke(session: ClientSession) -> str:
            result = await session.call_tool(tool_name, arguments=arguments)
            return _tool_result_text(result)

        return await self._with_session(server, invoke)
