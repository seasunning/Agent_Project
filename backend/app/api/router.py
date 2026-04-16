from fastapi import APIRouter

from app.api.routes import codegen, design, llm, requirements, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(llm.router)
api_router.include_router(requirements.router)
api_router.include_router(design.router)
api_router.include_router(codegen.router)
