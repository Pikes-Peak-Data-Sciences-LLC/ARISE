# Agentic Planner

## Broad Structure:

Begin by creating N agents. Starting at agent 0, have them assign themselves a role, and pass a message on to any agent without a role. Agents will prompt for roles until all agents have assigned *themselves* a role. Agents have the option to prompt another agent to refine their role, or to spawn or delete agents if required. 

Once agents are happy with roles, they can begin creating their output. They will message relevant agents until they have completed a plan, which is when they will mark themselves done. When all agents have marked themselves done, the program will cease. 

## Detailed Structure:

Agents have 5 potential actions they can do during their turn, and they may take more than one action in a single turn. 
- Assign Role: assigns themselves a role

- Message: Write a message to another agent

- Create Agent: When a gap exists, spawn an additional agent

- Query Output: If another agent has marked themselves "done", retrieve their output 

- Write Output: Write the final deliverable and mark themselves "done". 


During a turn, the only information an agent will see is: 

- Their past prompts/responses

- The ids, roles, and statuses of other agents

- Any messages that are in their "inbox" from other agents


Critically, agents will NOT see the outputs from other agents (unless requested) or messages between other agents. 


## File Guide:

Important files and what they do

agents/generic_agent.py 
    -holds the agent class and logic for action resolution

agents/prompts.py 
    -prompt creation (system prompt, nudge prompt and formatting for turn prompt)

llm/client.py 
    -llm calling logic, including saving history and json validation

models/schema.py 
    -holds all pydantic schema and dataclasses

config.py 
    -all settings (model name, parameters...)

mesh.py 
    -contains all agent objects, runs messaging and turn taking behavior

visualization 
    -optional visualization script



### Future Work & TODOs:

-Give agents the ability to delete other agents (currently stub)

-Improve nudges. Agents can sometimes recieve a nudge message when important messages are in queue.

-Increase safeguards. ie. agents should not be able to write output twice in one turn, or message the same agent twice in one turn.

-Max steps safeguard. Right before max steps, agents should be forced to make output. 

-Increase safeguards for tool calling. Agents can call tools multiple times without oversight. 

-Improve agent creation. Agents are reluctant to create other agents or cede responsibilities. 

-Implement role suggestion in new agent creation. Currently, role suggestion does nothing. 

-Change mesh into a builder pattern for improved passing of args

-Non-llm check for role differentiation? Potentially embed and check embeddings of roles for similarity

-Add context window error handling. Currently, this is just prevented with limited memory

-Add rate limit error handling

-Make a GUI to better observe agent behavior