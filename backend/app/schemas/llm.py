from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMInvokeRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = False
    enable_thinking: bool = True
    temperature: float = Field(default=0.2, ge=0, le=2)
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(default=None, ge=1)


class LLMUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    prompt_cache_hit_tokens: Optional[int] = None
    prompt_cache_miss_tokens: Optional[int] = None


class LLMResponse(BaseModel):
    id: Optional[str] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    content: str = ""
    reasoning_content: Optional[str] = None
    usage: Optional[LLMUsage] = None
    raw_response: dict


class LLMStreamEvent(BaseModel):
    type: Literal["reasoning", "content", "meta", "done"]
    id: Optional[str] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    content: str = ""
    usage: Optional[dict] = None
