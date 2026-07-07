from __future__ import annotations

from ARISE.models.schema import Message


def system_prompt(agent_id: int, num_agents: int, max_agents: int, task: str, tools: str = "None.",) -> str:
    last_agent_id = num_agents - 1
    return f"""You are agent {agent_id} in a mesh of {num_agents} agents (IDs 0 through {last_agent_id}).
Your goal is to complete this task:

{task}


You will first begin by assigning yourself a role. This role should be useful for completing the task, not overly broad, nor too narrow, and should not overlap with other roles. 
If you see an agent without a role, message then prompting them to assign themselves a role. You may NOT assign or suggest roles to other agents.
You may only prompt one agent for role assignment at a time. 

Once all agents have roles, you may message agents to ask refine their role if a role is too broad, narrow, or overlaps with another role. 
If there is a gap in the roles, you may propose a new agent to fill the gap and suggest their role. Do not create an additional agent unless necessary. 

Once all roles are satisfactory, you may message agents for information needed to complete your role. You may message multiple agents in one turn.
When finished, use write_output to write the final output in content. Your final output should be the final deliverable for the task and should be only the output for your specific role, and should not include information that will be provided by other agents. 


You act only when you receive a message. Each turn you may return multiple actions.

Available actions (every action must include content and recipient_id; use recipient_id -1 when not messaging or querying):
- assign_role — Assign yourself a role. Set recipient_id to -1. Content will be only the role title. 
- message — Pass the turn to another agent. recipient_id must be a valid agent ID. content must say what the recipient should do next.
- create_agent — Propose a new agent when a responsibility is unowned. Set recipient_id to -1. Team limit: {max_agents} agents ({num_agents} active now).
- query_output — If an agent's status is "done", query their output. recipient_id must be the target agent ID. Set content to "".
- write_output — Submit your final deliverable in content. Set recipient_id to -1.
- call_tool — Call an MCP tool. Set recipient_id to -1. Content must be a JSON string with server, tool, and args keys.

Tools available (server/tool_name):
{tools}

Response format (JSON array):
{{'actions': [
  {{"action": "assign_role", "recipient_id": -1, "content": "the role title"}},
  {{"action": "message", "recipient_id": INTEGER, "content": "your message"}},
  {{"action": "create_agent", "recipient_id": -1, "content": "suggested new agent role"}},
  {{"action": "query_output", "recipient_id": INTEGER, "content": ""}},
  {{"action": "call_tool", "recipient_id": -1, "content": "{{"server": "server", "tool": "tool_name", "args": {{"arg1": "value1"}}}}"}},
  {{"action": "write_output", "recipient_id": -1, "content": "your final output"}}
]}}

Example actions for a hotel coordinator agent communicating with iternerary agent with ID 1:
{{'actions': [
  {{"action": "assign_role", "recipient_id": -1, "content": "Hotel Coordinator"}},
  {{"action": "message", "recipient_id": 1, "content": "Please assign yourself a role"}},
  {{"action": "message", "recipient_id": 1, "content": "Please provide information about cities on the itinerary for the trip."}},
  {{"action": "create_agent", "recipient_id": -1, "content": "Flight Coordinator"}},
  {{"action": "query_output", "recipient_id": 1, "content": ""}},
  {{"action": "call_tool", "recipient_id": -1, "content": "{{"server": "weather", "tool": "get_weather_forecast", "args": {{"city": "Osaka", "days": 5}}}}"}},
  {{"action": "write_output", "recipient_id": -1, "content": "Three Hotels Bookings: A two day stay in Kyoto at a hotel near the train station, a three day stay in Tokyo in a pod hotel, and a two day stay in Osaka at a traditional ryokan."}}
]}}

"""


def build_user_prompt(inbox: list[Message], agents: list, agent_id: int) -> str:
    inbox_lines = []
    for message in inbox:
        sender = "system" if message.sender_id == -1 else f"Agent {message.sender_id}"
        inbox_lines.append(f"- {sender}: {message.content}")
    inbox_text = "\n".join(inbox_lines) if inbox_lines else "None."
    mesh_lines = []
    for agent in agents:
        label = f"Agent {agent.agent_id} (you)" if agent.agent_id == agent_id else f"Agent {agent.agent_id}"
        mesh_lines.append(
            f"- {label}: role={agent.role or 'unassigned'}, status={agent.status}"
        )
    return f"""Messages you received this turn:
{inbox_text}

Current mesh:
{"\n".join(mesh_lines)}
"""


def nudge_prompt(mesh) -> str:
    if not mesh.all_agents_have_roles():
        return """
        It is currently your turn. If you do not have a role, assign yourself a role. If you see an agent without a role, message them to assign themselves a role.
        """
    return """
        It is currently your turn. Evaluate if all agents have satisfactory roles. If not, prompt agents for role refinement. 
        If all agents have satisfactory roles, begin planning the required output for your task by messaging relevant agents, calling tools, or writing your output. 
        """
