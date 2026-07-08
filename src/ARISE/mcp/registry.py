from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from ARISE.config import MCP_SERVERS_PATH


@dataclass(frozen=True)
class MCPServerConfig:
    id: str
    command: str
    args: list[str]


def load_mcp_servers(path: Path | None = None) -> list[MCPServerConfig]:
    config_path = path or MCP_SERVERS_PATH
    if not config_path.exists():
        return []

    raw = yaml.safe_load(config_path.read_text()) or {}
    servers: list[MCPServerConfig] = []

    for server_id, entry in (raw.get("servers") or {}).items():
        if not entry or not entry.get("enabled", True):
            continue
        command = str(entry["command"])
        if command == "python":
            command = sys.executable
        servers.append(
            MCPServerConfig(
                id=server_id,
                command=command,
                args=[str(arg) for arg in entry.get("args", [])],
            )
        )

    return servers
