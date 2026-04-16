from typing import Literal

from pydantic import BaseModel

from app.schemas.requirement import RequirementAnalyzeResponse


class DesignGenerateRequest(BaseModel):
    requirement: RequirementAnalyzeResponse
    mode: Literal["fast", "deep"] = "fast"


class ModuleDesign(BaseModel):
    name: str
    responsibility: str
    inputs: list[str]
    outputs: list[str]


class ApiDesign(BaseModel):
    name: str
    method: str
    path: str
    description: str


class DataEntity(BaseModel):
    name: str
    fields: list[str]


class DesignGenerateResponse(BaseModel):
    architecture_style: str
    architecture_rationale: str
    modules: list[ModuleDesign]
    apis: list[ApiDesign]
    data_entities: list[DataEntity]
    mermaid: str
    raw_model_output: str
    reasoning_content: str | None = None
    mode: Literal["fast", "deep"] = "deep"


class DesignStreamEvent(BaseModel):
    type: Literal["status", "reasoning", "content", "result", "error", "done"]
    content: str = ""
    mode: Literal["fast", "deep"] | None = None
    result: DesignGenerateResponse | None = None
