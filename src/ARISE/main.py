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
    args = parser.parse_args(argv)

    if args.num_agents < 1:
        parser.error("--num-agents must be at least 1.")
    if args.max_agents < args.num_agents:
        parser.error("--max-agents must be >= --num-agents.")

    return args


def _log_agents(agents) -> None:
    logging.info("=" * 100)
    logging.info("Final Agents:")
    for agent in agents:
        logging.info(f"{agent}")
    for agent in agents:
        logging.info(f"Agent {agent.agent_id} output: {agent.output}")

def clear_log() -> None:
    with open('action_log.jsonl', 'w') as file:
        file.write('')


def main(argv: list[str] | None = None) -> int:
    mesh = None
    try:
        args = parse_args(argv)
        logging.basicConfig(filename='arise.log', level=logging.INFO)
        logging.info(f"="* 100)
        logging.info(f"Starting ARISE")
        logging.info(f"="* 100)
        logging.info(f"Input text: {args.input_text}")
        mesh = ARISEMesh(args.input_text, args.num_agents, args.max_agents)
        clear_log()
        
        while True:
            final_agents = mesh.run()
            _log_agents(final_agents)

            try:
                new_task = input("\nEnter a new task (empty to quit): ").strip()
            except EOFError:
                break
            if not new_task:
                break

            logging.info("=" * 100)
            logging.info("New task: %s", new_task)
            mesh.begin_new_task(new_task)

        return 0
    except ValueError as exc:
        logging.error(f"error: {exc}")
        return 2
    except Exception as exc:
        logging.error(f"error: {exc}")
        return 1
    finally:
        if mesh is not None:
            mesh.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
