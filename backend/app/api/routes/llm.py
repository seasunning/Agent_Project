import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.llm import LLMInvokeRequest
from app.services.deepseek_service import deepseek_service

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/invoke")
async def invoke_llm(request: LLMInvokeRequest):
    return await deepseek_service.invoke(request)


@router.post("/stream")
async def stream_llm(request: LLMInvokeRequest):
    async def event_generator():
        async for event in deepseek_service.stream(request):
            yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
