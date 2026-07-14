from __future__ import annotations

from ARISE.config import REWORK_PASSES, OUTPUT_CHARACTER_LIMIT
from ARISE.models.schema import Message
from typing import List

def system_prompt(agent_id: int, num_agents: int, max_agents: int, task: str, tools: str = "None.") -> str:
    last_agent_id = num_agents - 1
    prompt =f"""You are agent {agent_id} in a mesh of {num_agents} agents (IDs 0 through {last_agent_id}).

    You have the role of <Unassigned>.
Your goal is to complete this task:

{task}


You will first begin by assigning yourself a role. This role should be useful for completing the task, not overly broad, nor too narrow, and should not overlap with other roles. 
If you see an agent without a role, message them prompting them to assign themselves a role. You may NOT assign or suggest roles to other agents.
You may only prompt one agent for role assignment at a time. 

Once all agents have roles, you should message agents and direct them to refine or change their role if a role is too broad, narrow, or overlaps with another role. 
Ex. 'Hotel and Budget Coordinator' is too broad, and should be split into two separate roles. 'Tokyo Hotel Coordinator' and 'Kyoto Hotel Coordinator' are too narrow, and should be combined into one role unless the task requires separate coordination for each city.
'Iternary Coordinator' and 'Travel Planner' overlap too much, and one agent should be directed to change their role. 
If there is a gap in the roles, you should propose a new agent to fill the gap and suggest their role. If a current agent taking on too many responsibilities, you should propose a new agent and message the current agent to redefine their role. 
If there are too many agents for the task, you should delete an agent. 

If all roles are clear, not overlapping, and not too broad, you may message agents in order to complete the task. You may message multiple agents in one turn.
You are encouraged to critique the work of other agents, as well as ask agents to refine their role throughout the process. 
When finished, use write_output to write the final output in content. Content must be less than {OUTPUT_CHARACTER_LIMIT} characters, if it is longer, it should be trimmed or the agent's responsibilities should be split into multiple agents.
Your final output should be the final concise deliverable for the task and should be only the output for your specific role, and should not include information that will be provided by other agents or extraneous information. 
Your final ouput can be a tool call, if this is the case, call the tool and submit a summary of the tool call in write output.


You act only when you receive a message. Each turn you may return multiple actions.

Available actions (every action must include content and recipient_id; use recipient_id -1 when not messaging or querying):
- assign_role — Assign yourself a role. Set recipient_id to -1. Content will be only the role title. 
- message — Pass the turn to another agent. recipient_id must be a valid agent ID. Content should be the message to the recipient.
- create_agent — Propose a new agent when a responsibility is unowned. Set recipient_id to -1. Team limit: {max_agents} agents ({num_agents} active now).
- delete_agent — Remove an agent from the team. Set recipient_id to the agent ID to delete.
- query_output — If an agent's status is "done", query their output. recipient_id must be the target agent ID. Set content to "".
- write_output — Submit your final deliverable in content. Set recipient_id to -1. Content must be less than {OUTPUT_CHARACTER_LIMIT} characters.
- call_tool — Call an MCP tool. Set recipient_id to -1. Content must be a JSON string with server, tool, and args.

Tools available (server/tool_name):
{tools}

Response format (JSON array):
{{'actions': [
  {{"action": "assign_role", "recipient_id": -1, "content": "Role Title: a short description of the role"}},
  {{"action": "message", "recipient_id": INTEGER, "content": "your message"}},
  {{"action": "create_agent", "recipient_id": -1, "content": "Role Title: a short description of the role"}},
  {{"action": "delete_agent", "recipient_id": INTEGER, "content": ""}},
  {{"action": "query_output", "recipient_id": INTEGER, "content": ""}},
  {{"action": "call_tool", "recipient_id": -1, "content": "{{"server": "server", "tool": "tool_name", "args": {{"arg1": "value1"}}}}"}},
  {{"action": "write_output", "recipient_id": -1, "content": "your final output"}}
]}}

Example actions for a weather agent communicating with iternerary agent with ID 1:
{{'actions': [
  {{"action": "assign_role", "recipient_id": -1, "content": "Weather Agent: responsible for providing weather information for the itinerary"}},
  {{"action": "message", "recipient_id": 1, "content": "Please assign yourself a role"}},
  {{"action": "message", "recipient_id": 1, "content": "Please provide information about cities on the itinerary for the trip."}},
  {{"action": "create_agent", "recipient_id": -1, "content": "Flight Coordinator: responsible for booking flights for the itinerary"}},
  {{"action": "query_output", "recipient_id": 1, "content": ""}},
  {{"action": "call_tool", "recipient_id": -1, "content": "{{"server": "weather", "tool": "get_weather_forecast", "args": {{"city": "Osaka", "days": 1}}}}"}},
  {{"action": "write_output", "recipient_id": -1, "content": "Weather Forecast for June 15th-19th: June 15th in Osaka: 25°C, sunny with a chance of rain. \nJune 16th in Kyoto: 22°C, cloudy with a chance of rain..."}}
]}}

"""
    return prompt


def get_mesh_state(agents: List[GenericAgent], agent_id: int) -> str:
    mesh_lines = []
    for agent in agents:
        label = f"Agent {agent.agent_id} (you)" if agent.agent_id == agent_id else f"Agent {agent.agent_id}"
        mesh_lines.append(
            f"- {label}: role={agent.role or 'unassigned'}, status={agent.status}"
        )
    return "\n".join(mesh_lines)


def build_user_prompt(inbox: list[Message], agents: List[GenericAgent], agent_id: int) -> str:
    inbox_lines = []
    for message in inbox:
        sender = "system" if message.sender_id == -1 else f"Agent {message.sender_id}"
        inbox_lines.append(f"- {sender}: {message.content}")
    inbox_text = "\n".join(inbox_lines) if inbox_lines else "None."
    
    return f"""Messages you received this turn:
{inbox_text}

Current mesh:
{get_mesh_state(agents, agent_id)}
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

def rework_prompt(mesh, agent_id: int) -> str:
    output_lines = [
        f"- Agent {agent.agent_id} ({agent.role}): {agent.output}"
        for agent in mesh.agents
    ]
    return f"""Rework round {mesh.rework_round} of {REWORK_PASSES}.

Original task:
{mesh.input_text}

Team outputs from the previous round:
{'\n'.join(output_lines)}

----------------------------------------------------------------------------------------------------

Current mesh:
{get_mesh_state(mesh.agents, agent_id)}

Your primary objective is to evaluate the team's roles against their work and determine if an agent's role:
- is too narrow
- is too broad
- overlaps with another agent's role
- is not aligned with the task
- emcompasses more than one responsibility

The goal is to identify improvements in roles in order to improve the team's cooperation and output.

Outputs should be concise, useful, factual, and meet all of the requirement of the task.

If your role should change, use assign_role with an updated title. If an agent's role should be changed, message them to change their role. 
If additional agents are required, you should create an agent. If there are extraneous agents, you should delete them. 

Then rework your deliverable by messaging agents, calling tools, or writing output.

"""
def final_turn_prompt() -> str:
    return f"""
    This is your final turn. You must write your final output. You may not take any other actions. 
    """


def new_task_prompt(task: str) -> str:
    return f"""
    You have been give a new task:
    {task}

    Update the roles of the agents to reflect the new task and begin work on this new task.
    """
