"""Prompt templates for ARISE peer-to-peer planning agents."""

from __future__ import annotations

from typing import Any


def _format_peer_roles(peers: list[dict[str, Any]]) -> str:
    if not peers:
        return "None assigned yet."
    lines = []
    for peer in peers:
        role = peer.get("role") or "unassigned"
        lines.append(f"- {peer.get('agent_id', 'unknown')}: {role}")
    return "\n".join(lines)


def _format_peer_outputs(peers: list[dict[str, Any]]) -> str:
    if not peers:
        return "No peer outputs available yet."
    lines = []
    for peer in peers:
        role = peer.get("role") or "unassigned"
        output = peer.get("output") or peer.get("draft") or "No output yet."
        lines.append(f"- {peer.get('agent_id', 'unknown')} ({role}):\n  {output}")
    return "\n".join(lines)


def role_selection_prompt(
    task: str,
    agent_id: str,
    peer_roles: list[dict[str, Any]],
) -> str:
    """Prompt an agent to self-assign a unique, task-relevant role."""
    return f"""You are agent {agent_id} in a collaborative planning team.

Your job is to choose ONE specialized role that helps complete the task below.
Review the roles already taken by other agents and pick a role that:
- Is clearly distinct from existing roles (no overlap or duplication)
- Is narrow enough to produce actionable output, but broad enough to be useful
- Directly contributes to completing the task

Task:
{task}

Roles already assigned to other agents:
{_format_peer_roles(peer_roles)}

Respond with valid JSON only. Do not include markdown fences, commentary, or text outside the JSON object.

Response schema:
{{
  "role": "short descriptive role name",
  "responsibilities": "1-2 sentences describing what this role will deliver",
  "reasoning": "why this role fills a needed gap for the task"
}}
"""


def role_refinement_prompt(
    task: str,
    agent_id: str,
    current_role: str | None,
    peer_roles: list[dict[str, Any]],
    current_agent_count: int,
    max_agents: int,
) -> str:
    """Prompt an agent to keep, change, or propose adding a new peer agent."""
    can_add_agent = current_agent_count < max_agents
    add_agent_guidance = (
        "If you identify a clear gap that no existing or proposed role covers, "
        f"you may propose creating one additional agent ({current_agent_count}/{max_agents} agents active)."
        if can_add_agent
        else "Do not propose creating new agents; the team is at its maximum size."
    )

    return f"""You are agent {agent_id} in a collaborative planning team.

Review your current role and the roles held by other agents. Decide whether to:
1. Keep your current role as-is
2. Refine your current role (rename or adjust scope)
3. Propose creating a new agent to cover an unmet need

Task:
{task}

Your current role: {current_role or "unassigned"}

Other agents and their roles:
{_format_peer_roles(peer_roles)}

Guidelines:
- Prefer keeping or refining your role over proposing a new agent
- Only propose a new agent when a necessary responsibility is completely unowned
- New roles must not overlap with existing roles
- {add_agent_guidance}

Respond with valid JSON only. Do not include markdown fences, commentary, or text outside the JSON object.

If keeping or refining your role, respond with:
{{
  "action": "keep" | "refine",
  "role": "final role name",
  "responsibilities": "1-2 sentences describing what this role will deliver",
  "reasoning": "why this role is appropriate"
}}

If proposing a new agent, respond with:
{{
  "action": "create_agent",
  "role": "proposed role name for the new agent",
  "responsibilities": "1-2 sentences describing what the new agent would deliver",
  "reasoning": "why this gap cannot be covered by existing agents"
}}
"""


def dependency_identification_prompt(
    task: str,
    agent_id: str,
    current_role: str,
    peer_roles: list[dict[str, Any]],
) -> str:
    """Prompt an agent to declare which peer agents it depends on."""
    return f"""You are agent {agent_id} with the role: {current_role}

Identify which other agents you depend on to produce your output.
A dependency means you need that agent's output (or key decisions from it)
before you can produce a complete, accurate result.

Task:
{task}

Other agents:
{_format_peer_roles(peer_roles)}

Guidelines:
- Only declare dependencies you genuinely need; avoid unnecessary coupling
- Do not depend on yourself
- If you can produce your output independently, return an empty list
- Reference dependencies by agent_id

Respond with valid JSON only. Do not include markdown fences, commentary, or text outside the JSON object.

Response schema:
{{
  "dependencies": ["agent_id_1", "agent_id_2"],
  "reasoning": "why each dependency is required for your role"
}}"""


def draft_output_prompt(
    task: str,
    agent_id: str,
    current_role: str,
    dependency_outputs: list[dict[str, Any]],
    peer_roles: list[dict[str, Any]],
) -> str:
    """Prompt an agent to produce executable instructions for its role."""
    return f"""You are agent {agent_id} with the role: {current_role}

Produce the instructions your role is responsible for executing.
Write the actual deliverable content directly—do not summarize, recap,
or describe what you would do. Output the work product itself.

Task:
{task}

Outputs from agents you depend on:
{_format_peer_outputs(dependency_outputs)}

All other agents (for context only):
{_format_peer_roles(peer_roles)}

Guidelines:
- Execute only what your role owns
- Be specific and actionable (dates, locations, options, constraints, etc.)
- Do not redo or duplicate work owned by other roles
- Do not include meta-commentary, change logs, or overview sections
- If a dependency is missing, proceed with explicit placeholders inline

Respond with valid JSON only. Do not include markdown fences, commentary, or text outside the JSON object.

Response schema:
{{
  "draft": "the direct executable output for your role"
}}
"""


def refine_output_prompt(
    task: str,
    agent_id: str,
    current_role: str,
    current_draft: str,
    peer_outputs: list[dict[str, Any]],
) -> str:
    """Prompt an agent to refine its executable instructions using peer outputs."""
    return f"""You are agent {agent_id} with the role: {current_role}

Refine your instructions using the latest outputs from other agents.
Return the updated executable output directly—do not summarize, recap,
or describe the changes you made.

Task:
{task}

Your current draft:
{current_draft}

Outputs from other agents:
{_format_peer_outputs(peer_outputs)}

Guidelines:
- Stay within your role; do not absorb responsibilities from other agents
- Resolve contradictions with peer outputs where possible
- Do not include meta-commentary, change logs, or overview sections
- Output only the final executable content for your role

Respond with valid JSON only. Do not include markdown fences, commentary, or text outside the JSON object.

Response schema:
{{
  "output": "the direct executable output for your role"
}}
"""
