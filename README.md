## Agentic Planner

(!) Work in progress (!)


##Structure:

Begin by creating N agents. Starting at agent 0, have them assign themselves a role, and pass a message on to agent 1. Repeat until agent N. 

Agents will then go around refining their roles in the case of overlaps or gaps. They may also create new agents if there are too few agents. 

Agent N will then pass a message to the best starting Agent. This agent will create output or pass a message to another agent, this continues recursively until all agents have completed their task. 


###TODOs:

-Implement stronger JSON parsing. Constrained decoding and/or ways to handle incorrect JSON outputs

-Prevent looping. Often, agents can get stuck in endless role refinement loops. 

-Refactor for efficiency(?). Agents currently see their entire conversation history, which gets expensive. 

-Potentially rethink role refinement step. Not every role needs to be refined, one agent could just identify which roles have overlaps rather than each agent evaluating their role (expensive and potentially unnecessary)

-Implement tool/resource calls. Currently, agents have no way to search for information.

-Clean up prompts