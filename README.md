## Agentic Planner

(!) Work in progress (!)

Structure:
Role Selection -begin at agent 1, move to all N agents and have them self assign a role based on current roles. 

Role Refinement -go around, each agent decides if they want to change their role, or add a new agent

Dependency Identification -determine what dependencies, if any, an agent relies on to complete their task

Create draft -beginning at the agent with no dependencies, create a draft. If all agents have dependencies, start at the agent with the fewest and create a preliminary draft. 
Then, move to agents with the previous agent as a dependency if applicable. Cycle until all agents have recieved final input from their dependencies. Agents will see the entire output of their dependencies. 

Refine Draft -go around once, each agent refining only their own draft while looking at all other agent's outputs. 




TODOs:
fill out method stubs in generic agent, nodes, etc.

Prompts are currently hardcoded - change this. 

Implement LLM calls

test on synthetic dataset
    test alternative models, prompts, min/max agent counts, refinement passes
    test comparing zero-shot to ARISE system (potentially)

Rewrite README and additional documentation


Implement tool calls, w/ hardcoded tool definitions in config or elsewhere

Implement iterative prompt refinement + reinforcement


