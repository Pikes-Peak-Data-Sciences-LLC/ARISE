# ARISE

A multi-agent planner built around a mesh of peers rather than a single orchestrator. Agents assign their own roles, refine them over time, and communicate peer-to-peer. No agent has privileged control over another, and each agent only sees messages sent from other agents.

The aim of this project is to see agents continually update their roles to respond to changing task conditions and changes made by other agents. 

## How it works

1. **Start** with `N` agents (default 3). Agent 0 begins by assigning itself a role, then prompts others without roles to do the same.
2. **Role refinement.** Agents will refine their own role and message other agents to refine theirs. They can create or delete agents if required.
3. **Planning.** Once agents are satisfied with role coverage, they can begin messaging other agents and calling tools. Once finished, they will write their output and mark themselves done. 
4. **Rework** (optional). After everyone is done, the mesh can run a configured number of rework passes so agents can critique roles and revise outputs.
5. **New task.** When a run finishes, you can enter another task (or a refinement). Existing agents keep their roles unless they choose to update them.

Turns are queue-based. If the queue is empty while some agents remain active, the system sends a "nudge" to the first active agent.

The strength (and weakness) of this design is that almost everything is agent-driven. Aside from some hardcoded limits and rework prompts, there is little hard intervention in role assignment, output quality and format, and what agents can message each other. 

## Agent actions

An agent may take multiple actions in one turn:

| Action | Description |
|--------|-------------|
| `assign_role` | Assign or update its own role |
| `message` | Send a message to another agent |
| `create_agent` | Propose a new agent when a responsibility is unowned |
| `delete_agent` | Remove an agent *(not currently implemented)* |
| `query_output` | Fetch another agent's output if that agent is `done` |
| `write_output` | Submit a final deliverable and mark itself `done` |
| `call_tool` | Call an MCP tool (e.g. weather, hotels) |

### What an agent sees each turn

- Its own conversation history (truncated by `MEMORY_WINDOW`)
- IDs, roles, and statuses of other agents
- Messages in its inbox (including tool results and self-replies)

Agents do **not** see peer-to-peer messages between other agents, or outputs they have not queried.

## Usage

```bash
python run.py "Plan a 3 day trip to San Francisco"
```

Options:

```bash
python run.py "your task" --num-agents 3 --max-agents 10
```

When a run completes, you will be prompted for another task (empty input to quit).

### Logs

| File | Contents |
|------|----------|
| `arise.log` | Full plaintext event log |
| `action_log.jsonl` | JSON record of agent actions |


## Configuration

Tunable defaults live in `src/ARISE/config.py`:

| Setting | |
|---------|---------|
| `DEFAULT_AGENTS` / `MAX_AGENTS` | Initial and maximum mesh size |
| `MEMORY_WINDOW` | Prior turns kept in each agent's LLM history |
| `REWORK_PASSES` | Rework cycles after all agents are finished |
| `MAX_STEPS` | Hard cap on turn steps |
| `OUTPUT_CHARACTER_LIMIT` | Max length for `write_output` |

## Project layout

```
src/ARISE/
  main.py                 CLI entry point
  mesh.py                 Agent mesh, mailboxes, turn-taking, spawn
  config.py               Settings and env loading
  agents/
    generic_agent.py      Agent class and action resolution
    prompts.py            System, turn, nudge, and rework prompts
  llm/
    client.py             LLM client, history, memory, JSON schema validation
  models/
    schema.py             Pydantic action schemas and Message type
  mcp/
    manager.py            MCP tool registration and calls
    registry.py           Loads mcp_server.yaml
    servers/              Tool server locations
  visualization/
    visualize.py          Optional role evolution visualization
```

## Future work

- Force `write_output` near `MAX_STEPS`
- Improve nudge behavior (nudges can sometimes occur when mail is in queue)
- Per-turn action limits (e.g. one `write_output`, no duplicate messages to the same peer)
- Tool-call budgeting / oversight (currently no limits on how often tools can be called and when)
- Improve agent spawning behavior (agents are reluctant to cede responsibility or create new agents)
- Add Hard Role-similarity checks (e.g. embeddings) to flag overlaps without relying only on the LLM
- Better error handling for rate limits, context-window overflow, and max-token truncation
- GUI for observing mesh behavior live
