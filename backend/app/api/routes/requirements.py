import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.requirement import RequirementAnalyzeRequest
from app.services.requirement_service import requirement_service

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("/analyze")
async def analyze_requirement(request: RequirementAnalyzeRequest):
    return await requirement_service.analyze(request)


@router.post("/analyze/stream")
async def analyze_requirement_stream(request: RequirementAnalyzeRequest):
    async def event_generator():
        async for event in requirement_service.analyze_stream(request):
            yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
