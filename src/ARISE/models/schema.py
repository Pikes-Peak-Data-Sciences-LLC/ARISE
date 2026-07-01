"""Pydantic schemas for structured LLM responses."""

from pydantic import BaseModel


class RoleSelection(BaseModel):
    role: str
    responsibilities: str
    reasoning: str


class RoleRefinement(BaseModel):
    action: str
    role: str
    responsibilities: str
    reasoning: str


class DependencyDeclaration(BaseModel):
    dependencies: list[str]
    reasoning: str


class DraftOutput(BaseModel):
    draft: str


class RefineOutput(BaseModel):
    output: str
