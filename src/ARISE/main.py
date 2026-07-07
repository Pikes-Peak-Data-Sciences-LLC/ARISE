"""CLI entry point for ARISE."""

from __future__ import annotations

import argparse
import sys
import logging
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
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Log all actions and messages.',
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
        logging.basicConfig(filename='arise.log', level=logging.INFO if args.verbose else logging.INFO) #verbose doesnt do anything right now
        logging.info(f"="* 100)
        logging.info(f"Starting ARISE")
        logging.info(f"="* 100)
        logging.info(f"Input text: {args.input_text}")
        final_agents = mesh.run()

        # log final outputs of agents
        logging.info(f"="* 100)
        logging.info(f"Final Agents:")
        for agent in final_agents:
            logging.info(f"{agent}")
        for agent in final_agents:
            logging.info(f"Agent {agent.agent_id} output: {agent.output}")
        return 0
    except ValueError as exc:
        logging.error(f"error: {exc}")
        return 2
    except Exception as exc:
        logging.error(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
