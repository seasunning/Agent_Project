import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.schemas.codegen import CodeGenerateRequest, CodePersistRequest, CodePreviewRequest, CodeSuggestRequest
from app.services.codegen_service import codegen_service

router = APIRouter(prefix='/codegen', tags=['codegen'])


@router.post('/suggest')
async def suggest_options(request: CodeSuggestRequest):
    return await codegen_service.suggest_options(request.design)


@router.post('/suggest/stream')
async def suggest_options_stream(request: CodeSuggestRequest):
    async def event_generator():
        async for event in codegen_service.suggest_options_stream(request.design):
            yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')


@router.post('/generate')
async def generate_code(request: CodeGenerateRequest):
    return await codegen_service.generate(request)


@router.post('/preview')
async def preview_code(request: CodePreviewRequest):
    return await codegen_service.preview(request)


@router.post('/persist')
async def persist_code_project(request: CodePersistRequest):
    return codegen_service.ensure_project_persisted(request.result, request.project_name, request.options)


@router.get('/archive/{archive_name}')
async def download_archive(archive_name: str):
    archive_path = codegen_service.output_root / archive_name
    if not archive_path.exists() or archive_path.suffix.lower() != '.zip':
        raise HTTPException(status_code=404, detail='压缩包不存在')
    return FileResponse(path=archive_path, filename=archive_name, media_type='application/zip')


@router.post('/generate/stream')
async def generate_code_stream(request: CodeGenerateRequest):
    async def event_generator():
        async for event in codegen_service.generate_stream(request):
            yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')
