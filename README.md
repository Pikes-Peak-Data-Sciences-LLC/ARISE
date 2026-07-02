## Agentic Planner

(!) Work in progress (!)


Structure:

Begin by creating N agents. Starting at agent 0, have them assign themselves a role, and pass a message on to agent 1. Repeat until agent N. 

Agent N will then begin role refinement by passing a message to agent 0 to refine roles. This continues as above, and new agents can be created as needed. 

Agent N will then pass a message to the best starting Agent. This agent will create output or pass a message to another agent, this continues recursively until all agents have completed their task. 