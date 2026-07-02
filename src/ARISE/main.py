"""CLI entry point for ARISE."""

from __future__ import annotations

import argparse
import sys

from ARISE.config import DEFAULT_AGENTS, MAX_AGENTS
from ARISE.graph import create_graph


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the ARISE multi-agent planner.",
    )
    parser.add_argument(
        "input_text",
        help="The plan to execute.",
    )
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
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.num_agents < 1:
        raise ValueError("--num-agents must be at least 1.")
    if args.max_agents < args.num_agents:
        raise ValueError("--max-agents must be >= --num-agents.")


def run(args: argparse.Namespace) -> None:
    graph = create_graph(
        input_text=args.input_text,
        num_agents=args.num_agents,
        max_agents=args.max_agents,
    )
    # For now, return the agents and print
    final_agents = graph.run()
    [print("Final Agent", agent, '\n') for agent in final_agents]


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        validate_args(args)
        run(args)
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
