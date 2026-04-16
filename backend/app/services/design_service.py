import json
from collections.abc import AsyncGenerator

from app.schemas.design import (
    ApiDesign,
    DataEntity,
    DesignGenerateRequest,
    DesignGenerateResponse,
    DesignStreamEvent,
    ModuleDesign,
)
from app.schemas.llm import ChatMessage, LLMInvokeRequest
from app.services.deepseek_service import deepseek_service


class DesignService:
    async def generate(self, request: DesignGenerateRequest) -> DesignGenerateResponse:
        llm_request = self._build_llm_request(request)
        result = await deepseek_service.invoke(llm_request)
        return self._build_response(result.content, result.reasoning_content, request.mode)

    async def generate_stream(self, request: DesignGenerateRequest) -> AsyncGenerator[DesignStreamEvent, None]:
        llm_request = self._build_llm_request(request, stream=True)
        yield DesignStreamEvent(type="status", mode=request.mode, content="已提交设计生成请求，正在连接模型服务...")
        reasoning_content = ""
        content = ""
        async for event in deepseek_service.stream(llm_request):
            if event.type == "reasoning":
                reasoning_content += event.content
                yield DesignStreamEvent(type="reasoning", mode=request.mode, content=event.content)
            elif event.type == "content":
                content += event.content
                yield DesignStreamEvent(type="content", mode=request.mode, content=event.content)
            elif event.type == "meta":
                status_text = "正在进行深度架构推理..." if request.mode == "deep" else "正在快速生成设计草案..."
                yield DesignStreamEvent(type="status", mode=request.mode, content=status_text)
            elif event.type == "done":
                response = self._build_response(content, reasoning_content or None, request.mode)
                yield DesignStreamEvent(type="result", mode=request.mode, result=response)
                yield DesignStreamEvent(type="done", mode=request.mode, content="设计方案生成完成")

    def _build_llm_request(self, request: DesignGenerateRequest, stream: bool = False) -> LLMInvokeRequest:
        deep_mode = request.mode == "deep"
        requirement_json = json.dumps(request.requirement.model_dump(mode="json"), ensure_ascii=False, indent=2)
        return LLMInvokeRequest(
            messages=[
                ChatMessage(role="system", content=self._system_prompt(deep_mode)),
                ChatMessage(role="user", content=self._user_prompt(requirement_json, deep_mode)),
            ],
            enable_thinking=deep_mode,
            stream=stream,
            temperature=0.2 if deep_mode else 0.1,
        )

    @staticmethod
    def _system_prompt(deep_mode: bool) -> str:
        if deep_mode:
            return (
                "你是资深软件架构师。"
                "请根据需求分析结果生成严格 JSON 的设计方案。"
                "不要输出 markdown，不要输出代码块，不要添加解释。"
            )
        return (
            "你是高效的软件架构整理助手。"
            "请快速输出设计草案，并保持严格 JSON。"
            "不要输出 markdown，不要输出代码块，不要添加解释。"
        )

    @staticmethod
    def _user_prompt(requirement_json: str, deep_mode: bool) -> str:
        base = (
            "请基于以下需求分析结果生成设计方案。\n"
            "必须输出 JSON，对象字段严格包含：architecture_style, architecture_rationale, modules, apis, data_entities, mermaid。\n"
            "modules 是数组，每项字段：name, responsibility, inputs, outputs。\n"
            "apis 是数组，每项字段：name, method, path, description。\n"
            "data_entities 是数组，每项字段：name, fields。\n"
            "mermaid 必须输出可直接渲染的 flowchart TD 图。\n"
        )
        extra = (
            "请尽量给出模块职责边界、接口划分依据和较完整的数据实体设计。\n"
            if deep_mode
            else "请优先输出最核心的架构风格、主要模块、关键接口和基础图描述。\n"
        )
        return f"{base}{extra}需求分析结果：\n{requirement_json}"

    def _build_response(self, content: str, reasoning_content: str | None, mode: str) -> DesignGenerateResponse:
        parsed = self._parse_json_content(content)
        return DesignGenerateResponse(
            architecture_style=str(parsed.get("architecture_style") or "分层架构"),
            architecture_rationale=str(parsed.get("architecture_rationale") or "根据当前需求自动生成的初步架构方案。"),
            modules=[
                ModuleDesign(
                    name=item.get("name") or "未命名模块",
                    responsibility=item.get("responsibility") or "",
                    inputs=self._string_list(item.get("inputs")),
                    outputs=self._string_list(item.get("outputs")),
                )
                for item in (parsed.get("modules") or [])
                if isinstance(item, dict)
            ],
            apis=[
                ApiDesign(
                    name=item.get("name") or "未命名接口",
                    method=item.get("method") or "GET",
                    path=item.get("path") or "/pending",
                    description=item.get("description") or "",
                )
                for item in (parsed.get("apis") or [])
                if isinstance(item, dict)
            ],
            data_entities=[
                DataEntity(
                    name=item.get("name") or "未命名实体",
                    fields=self._string_list(item.get("fields")),
                )
                for item in (parsed.get("data_entities") or [])
                if isinstance(item, dict)
            ],
            mermaid=str(parsed.get("mermaid") or self._fallback_mermaid()),
            raw_model_output=content,
            reasoning_content=reasoning_content,
            mode=mode,
        )

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    @staticmethod
    def _parse_json_content(content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {
            "architecture_style": "分层架构",
            "architecture_rationale": "模型返回未完全符合 JSON 规范，已保留原始输出供人工确认。",
            "modules": [],
            "apis": [],
            "data_entities": [],
            "mermaid": DesignService._fallback_mermaid(),
        }

    @staticmethod
    def _fallback_mermaid() -> str:
        return "flowchart TD\n    A[用户需求] --> B[需求分析]\n    B --> C[系统设计]\n    C --> D[代码生成]"


design_service = DesignService()
