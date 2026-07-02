from __future__ import annotations

from ARISE.messages import Message


def system_prompt(agent_id: int, num_agents: int, max_agents: int, task: str) -> str:
    last_agent_id = num_agents - 1
    return f"""You are agent {agent_id} in a mesh of {num_agents} agents (IDs 0 through {last_agent_id}).
Your goal is to complete this task:

{task}


Task Execution will proceed in the following order:
1. Role assignment — Agent 0 assigns themselves a role and prompts agent 1 to do the same. Pass along information about your own role and the known roles of other agents in messages. 
Continue in order until agent {last_agent_id} assigns themselves a role, then agent {last_agent_id} messages agent 0 to begin role refinement. 

2. Role refinement — Agent 0 refines only their own role, then messages agent 1. Continue in order until agent {last_agent_id} refines only their own role, then agent {last_agent_id} messages the best agent to start output. 
During this phase, agents may optionally spawn new agents where there are gaps in the roles. Do not create an additional agent unless absolutely necessary. 

3. Output — Agents will message relevant agents for information needed to complete their role. Each agent writes their role's deliverable. When finished, use write_output to mark yourself done.

You act only when you receive a message. Each turn you may return multiple actions.

Available actions:
- assign_role — Set your role in content.
- message — Pass the turn to another agent. recipient_id must be a valid agent ID. Content should say what the recipient should do next.
- create_agent — Propose a new agent when a responsibility is unowned. Team limit: {max_agents} agents ({num_agents} active now).
- write_output — Submit your final deliverable in content and mark yourself done.

Respond with valid JSON only. No markdown fences or extra text.

Response format (JSON array):
[
  {{"action": "assign_role", "content": "the role assignment"}},
  {{"action": "message", "recipient_id": 1, "content": "your message"}},
  {{"action": "create_agent", "content": "suggested new agent role"}},
  {{"action": "write_output", "content": "your final output"}}
]

Example actions:
[
  {{"action": "assign_role", "content": "Hotel Coordinator"}},
  {{"action": "message", "recipient_id": 1, "content": "Please provide information about cities on the itinerary for the trip."}},
  {{"action": "create_agent", "content": "Flight Coordinator"}},
  {{"action": "write_output", "content": "Three Hotels Bookings: A two day stay in Kyoto at a hotel near the train station, a three day stay in Tokyo in a pod hotel, and a two day stay in Osaka at a traditional ryokan."}}
]

"""


def build_user_prompt(inbox: list[Message], agents: list, agent_id: int) -> str:
    inbox_lines = []
    for message in inbox:
        sender = "system" if message.sender_id == -1 else f"Agent {message.sender_id}"
        inbox_lines.append(f"- {sender}: {message.content}")
    inbox_text = "\n".join(inbox_lines) if inbox_lines else "None."
    mesh_lines = []
    for agent in agents:
        label = "you" if agent.agent_id == agent_id else f"Agent {agent.agent_id}"
        mesh_lines.append(
            f"- {label}: role={agent.role or 'unassigned'}, "
            f"output={agent.output or 'none'}, phase={agent.phase}"
        )

    return f"""Messages you received this turn:
{inbox_text}

Current mesh:
{"\n".join(mesh_lines)}
"""
