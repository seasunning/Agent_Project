import json
from collections.abc import AsyncGenerator

import httpx

from app.core.config import settings
from app.schemas.llm import LLMInvokeRequest, LLMResponse, LLMStreamEvent, LLMUsage


class DeepSeekService:
    def __init__(self) -> None:
        self.base_url = settings.deepseek_base_url
        self.api_key = settings.deepseek_api_key.get_secret_value()
        self.timeout = settings.deepseek_timeout
        self.default_model = settings.deepseek_model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, request: LLMInvokeRequest) -> dict:
        payload = {
            "model": request.model or self.default_model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": request.stream,
            "temperature": request.temperature,
        }
        if request.enable_thinking:
            payload["thinking"] = {"type": "enabled"}
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        return payload

    @staticmethod
    def _usage_from_raw(raw_usage: dict | None) -> LLMUsage | None:
        if not raw_usage:
            return None
        return LLMUsage(
            prompt_tokens=raw_usage.get("prompt_tokens"),
            completion_tokens=raw_usage.get("completion_tokens"),
            total_tokens=raw_usage.get("total_tokens"),
            prompt_cache_hit_tokens=raw_usage.get("prompt_cache_hit_tokens"),
            prompt_cache_miss_tokens=raw_usage.get("prompt_cache_miss_tokens"),
        )

    async def invoke(self, request: LLMInvokeRequest) -> LLMResponse:
        payload = self._payload(request)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            raw = response.json()

        choice = ((raw.get("choices") or [{}])[0])
        message = choice.get("message") or {}
        return LLMResponse(
            id=raw.get("id"),
            model=raw.get("model"),
            finish_reason=choice.get("finish_reason"),
            content=message.get("content") or "",
            reasoning_content=message.get("reasoning_content"),
            usage=self._usage_from_raw(raw.get("usage")),
            raw_response=raw,
        )

    async def stream(self, request: LLMInvokeRequest) -> AsyncGenerator[LLMStreamEvent, None]:
        payload = self._payload(request.model_copy(update={"stream": True}))
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self.base_url, headers=self._headers(), json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        yield LLMStreamEvent(type="done")
                        continue
                    chunk = json.loads(data_str)
                    choice = ((chunk.get("choices") or [{}])[0])
                    delta = choice.get("delta") or {}
                    model = chunk.get("model")
                    chunk_id = chunk.get("id")
                    finish_reason = choice.get("finish_reason")

                    if delta.get("reasoning_content"):
                        yield LLMStreamEvent(
                            type="reasoning",
                            id=chunk_id,
                            model=model,
                            finish_reason=finish_reason,
                            content=delta.get("reasoning_content") or "",
                        )
                    if delta.get("content"):
                        yield LLMStreamEvent(
                            type="content",
                            id=chunk_id,
                            model=model,
                            finish_reason=finish_reason,
                            content=delta.get("content") or "",
                        )
                    if finish_reason or chunk.get("usage"):
                        yield LLMStreamEvent(
                            type="meta",
                            id=chunk_id,
                            model=model,
                            finish_reason=finish_reason,
                            usage=chunk.get("usage"),
                        )


deepseek_service = DeepSeekService()
