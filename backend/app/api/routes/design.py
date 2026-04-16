import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.design import DesignGenerateRequest
from app.services.design_service import design_service

router = APIRouter(prefix="/design", tags=["design"])


@router.post("/generate")
async def generate_design(request: DesignGenerateRequest):
    return await design_service.generate(request)


@router.post("/generate/stream")
async def generate_design_stream(request: DesignGenerateRequest):
    async def event_generator():
        async for event in design_service.generate_stream(request):
            yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
