from __future__ import annotations

from ARISE.models.schema import Message


def system_prompt(agent_id: int, num_agents: int, max_agents: int, task: str) -> str:
    last_agent_id = num_agents - 1
    return f"""You are agent {agent_id} in a mesh of {num_agents} agents (IDs 0 through {last_agent_id}).
Your goal is to complete this task:

{task}


Task Execution will proceed in the following order:
1. Role assignment — strict relay chain:
   - Agent 0 assigns a role, then messages Agent 1.
   - Agent 1 assigns a role, then messages Agent 2.
   - ...
   - Agent {last_agent_id} assigns a role and stops (no forward message).
   Each message must tell the recipient: assign your role, then message Agent {{your_id + 1}}.

2. Role refinement — Agent 0 refines only their own role, then messages agent 1. Continue in order until agent {last_agent_id} refines only their own role. 
During this phase, agents may optionally spawn new agents where there are gaps in the roles. Do not create an additional agent unless necessary. 
It it then the job of agent {last_agent_id} to message the best agent to start output.

3. Output Creation — Agents will message relevant agents for information needed to complete their role. Each agent writes their role's deliverable.
 When finished, use write_output to write the final output in content. 
 The final output should be the final deliverable for the task and should be only the output for your specific role. 

You act only when you receive a message. Each turn you may return multiple actions.

Available actions:
- assign_role — Assign yourself a role. 
- message — Pass the turn to another agent. recipient_id must be a valid agent ID. Content should say what the recipient should do next.
- create_agent — Propose a new agent when a responsibility is unowned. Team limit: {max_agents} agents ({num_agents} active now).
- write_output — Submit your final deliverable in content. Your final deliverable should be the final output only for your specific role. 

Respond with valid JSON only. No markdown fences or extra text.

Response format (JSON array):
[
  {{"action": "assign_role", "content": "the role assignment"}},
  {{"action": "message", "recipient_id": 1, "content": "your message"}},
  {{"action": "create_agent", "content": "suggested new agent role"}},
  {{"action": "write_output", "content": "your final output"}}
]

Example actions for a hotel coordinator agent:
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
        label = f"Agent {agent.agent_id} (you)" if agent.agent_id == agent_id else f"Agent {agent.agent_id}"
        mesh_lines.append(
            f"- {label}: role={agent.role or 'unassigned'}, "
            f"output={agent.output or 'none'}, phase={agent.phase}"
        )
    return f"""Messages you received this turn:
{inbox_text}

Current mesh:
{"\n".join(mesh_lines)}
"""



def role_assignment_prompt(num_agents: int) -> str:
    last_agent_id = num_agents - 1
    return f"""Role assignment phase. You are Agent 0. 

    1. Assign yourself a role. 
    2. Message agent 1 and tell them:
        - Assign their own role
        - Include all roles assigned so far and to which agents
        - Message Agent 2 with the same relay instruction, which will continue in a chain until the agent {last_agent_id}, the final agent.

    Do not suggest or assign roles for other agents. 
    """

def role_refinement_prompt(num_agents: int) -> str:
    last_agent_id = num_agents - 1
    return f"""Role refinement phase. You are Agent 0. 

    1. Refine your own role. Evaluate if there is a gap or overlap in the current roles. 
    2. Optionally, if there is a gap in the roles that cannot be filled by the current agents, propose a new agent to fill the gap. Do not create an additional agent unless necessary. 
    3. Message agent 1 and tell them:
        - Refine their own role
        - Optionally, propose a new agent to fill a gap in the roles if necessary.
        - Include all roles assigned so far and to which agents
        - Message Agent 2 with the same relay instruction, which will continue in a chain until the agent {last_agent_id}, the final agent.
        - It is the job of the final agent Agent {last_agent_id} to message the best starting agent to start planning and output creation.
    """

def output_creation_prompt() -> str:
    return f"""Output creation phase. You are Agent 0. 

    It is your job to begin the output creation process. Message the best starting agent to start planning and output creation.
    Agents must communicate with one another to gather information needed to complete their roles. 
    When finished, use write_output to write the final output in content. 
    The final output should be the final deliverable for the task and should be only the output for your specific role. 
    """

def nudge_prompt() -> str:
    return f"""Continue your task execution."""