from typing import Literal

from pydantic import BaseModel, Field


class RequirementAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, description="用户输入的原始需求文本")
    mode: Literal["fast", "deep"] = "fast"


class RequirementItem(BaseModel):
    name: str
    description: str
    priority: str | None = None


class RequirementAnalyzeResponse(BaseModel):
    summary: str
    functional_requirements: list[RequirementItem]
    non_functional_requirements: list[str]
    constraints: list[str]
    actors: list[str]
    ambiguities: list[str]
    conflicts: list[str]
    questions_for_user: list[str]
    raw_model_output: str
    reasoning_content: str | None = None
    mode: Literal["fast", "deep"] = "fast"


class RequirementStreamEvent(BaseModel):
    type: Literal["status", "reasoning", "content", "result", "error", "done"]
    content: str = ""
    mode: Literal["fast", "deep"] | None = None
    result: RequirementAnalyzeResponse | None = None
