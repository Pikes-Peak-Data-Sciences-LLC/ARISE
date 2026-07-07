from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from ARISE.config import MCP_SERVERS_PATH

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


@dataclass(frozen=True)
class MCPServerConfig:
    id: str
    command: str
    args: list[str]
    env: dict[str, str] | None = None
    description: str = ""


def _resolve_env(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), "")

    return _ENV_PATTERN.sub(replace, value)


def _resolve_command(command: str) -> str:
    if command == "python":
        return sys.executable
    return command


def load_mcp_servers(path: Path | None = None) -> list[MCPServerConfig]:
    config_path = path or MCP_SERVERS_PATH
    if not config_path.exists():
        return []

    raw = yaml.safe_load(config_path.read_text()) or {}
    servers: list[MCPServerConfig] = []

    for server_id, entry in (raw.get("servers") or {}).items():
        if not entry or not entry.get("enabled", True):
            continue

        env = entry.get("env")
        resolved_env = None
        if env:
            resolved_env = {key: _resolve_env(str(val)) for key, val in env.items()}

        servers.append(
            MCPServerConfig(
                id=server_id,
                command=_resolve_command(str(entry["command"])),
                args=[str(arg) for arg in entry.get("args", [])],
                env=resolved_env,
                description=str(entry.get("description", "")),
            )
        )

    return servers
