from typing import Literal

from pydantic import BaseModel

from app.schemas.design import DesignGenerateResponse


class CodegenOptions(BaseModel):
    language: str
    backend_framework: str
    frontend_framework: str
    database: str


class CodeSuggestRequest(BaseModel):
    design: DesignGenerateResponse


class CodeSuggestResponse(BaseModel):
    options: CodegenOptions
    reasoning: str | None = None
    raw_model_output: str = ''


class CodeSuggestStreamEvent(BaseModel):
    type: Literal['status', 'content', 'result', 'error', 'done']
    content: str = ''
    result: CodeSuggestResponse | None = None


class CodeFile(BaseModel):
    path: str
    language: str
    description: str
    content: str


class CodeGenerateRequest(BaseModel):
    design: DesignGenerateResponse
    options: CodegenOptions
    mode: Literal['fast', 'deep'] = 'fast'


class CodeGenerateResponse(BaseModel):
    project_summary: str
    tech_stack: list[str]
    file_tree: str
    files: list[CodeFile]
    startup_steps: list[str]
    raw_model_output: str
    reasoning_content: str | None = None
    mode: Literal['fast', 'deep'] = 'fast'


class CodeStreamEvent(BaseModel):
    type: Literal['status', 'reasoning', 'content', 'result', 'error', 'done']
    content: str = ''
    mode: Literal['fast', 'deep'] | None = None
    result: CodeGenerateResponse | None = None


class CodePreviewRequest(BaseModel):
    design: DesignGenerateResponse
    options: CodegenOptions
    mode: Literal['fast', 'deep'] = 'fast'


class CodePersistRequest(BaseModel):
    result: CodeGenerateResponse
    options: CodegenOptions | None = None
    project_name: str = ''
    save_strategy: Literal['save_as_new'] = 'save_as_new'


class CodePersistResponse(BaseModel):
    project_name: str
    output_path: str
    written_files: list[str]
    startup_script: str | None = None
    archive_name: str | None = None
