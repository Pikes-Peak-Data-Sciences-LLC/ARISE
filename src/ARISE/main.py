"""CLI entry point for ARISE."""

from __future__ import annotations

import argparse
import sys

from ARISE.config import DEFAULT_AGENTS, MAX_AGENTS
from ARISE.mesh import ARISEMesh


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ARISE multi-agent planner.")
    parser.add_argument("input_text", help="The plan to execute.")
    parser.add_argument(
        "--num-agents",
        type=int,
        default=DEFAULT_AGENTS,
        help=f"Initial number of agents (default: {DEFAULT_AGENTS}).",
    )
    parser.add_argument(
        "--max-agents",
        type=int,
        default=MAX_AGENTS,
        help=f"Maximum number of agents allowed (default: {MAX_AGENTS}).",
    )
    args = parser.parse_args(argv)

    if args.num_agents < 1:
        parser.error("--num-agents must be at least 1.")
    if args.max_agents < args.num_agents:
        parser.error("--max-agents must be >= --num-agents.")

    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        mesh = ARISEMesh(args.input_text, args.num_agents, args.max_agents)
        final_agents = mesh.run()
        print('='*50, "Final Output", '='*50)
        for agent in final_agents:
            print(agent, end="\n\n")
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
