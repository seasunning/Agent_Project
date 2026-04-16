import json
from collections.abc import AsyncGenerator

from app.schemas.llm import ChatMessage, LLMInvokeRequest
from app.schemas.requirement import (
    RequirementAnalyzeRequest,
    RequirementAnalyzeResponse,
    RequirementItem,
    RequirementStreamEvent,
)
from app.services.deepseek_service import deepseek_service


class RequirementService:
    async def analyze(self, request: RequirementAnalyzeRequest) -> RequirementAnalyzeResponse:
        llm_request = self._build_llm_request(request)
        result = await deepseek_service.invoke(llm_request)
        return self._build_response(result.content, result.reasoning_content, request.mode)

    async def analyze_stream(self, request: RequirementAnalyzeRequest) -> AsyncGenerator[RequirementStreamEvent, None]:
        llm_request = self._build_llm_request(request, stream=True)
        yield RequirementStreamEvent(
            type="status",
            mode=request.mode,
            content="已提交需求，正在连接模型服务...",
        )
        reasoning_content = ""
        content = ""
        async for event in deepseek_service.stream(llm_request):
            if event.type == "reasoning":
                reasoning_content += event.content
                yield RequirementStreamEvent(type="reasoning", mode=request.mode, content=event.content)
            elif event.type == "content":
                content += event.content
                yield RequirementStreamEvent(type="content", mode=request.mode, content=event.content)
            elif event.type == "meta":
                status_text = "正在进行深度推理..." if request.mode == "deep" else "正在生成结构化结果..."
                yield RequirementStreamEvent(type="status", mode=request.mode, content=status_text)
            elif event.type == "done":
                response = self._build_response(content, reasoning_content or None, request.mode)
                yield RequirementStreamEvent(type="result", mode=request.mode, result=response)
                yield RequirementStreamEvent(type="done", mode=request.mode, content="需求分析完成")

    def _build_llm_request(self, request: RequirementAnalyzeRequest, stream: bool = False) -> LLMInvokeRequest:
        deep_mode = request.mode == "deep"
        return LLMInvokeRequest(
            messages=[
                ChatMessage(role="system", content=self._system_prompt(deep_mode)),
                ChatMessage(role="user", content=self._user_prompt(request.text, deep_mode)),
            ],
            enable_thinking=deep_mode,
            stream=stream,
            temperature=0.2 if deep_mode else 0.1,
        )

    @staticmethod
    def _system_prompt(deep_mode: bool) -> str:
        if deep_mode:
            return (
                "你是资深软件需求分析师。"
                "请将用户需求转换为严格 JSON。"
                "不要输出 markdown，不要输出代码块，不要添加解释。"
            )
        return (
            "你是高效的软件需求整理助手。"
            "请快速提取核心需求并输出严格 JSON。"
            "不要输出 markdown，不要输出代码块，不要添加解释。"
        )

    @staticmethod
    def _user_prompt(text: str, deep_mode: bool) -> str:
        base = (
            "请分析下面的软件需求，并输出 JSON 对象。\n"
            "字段必须严格包含：summary, functional_requirements, non_functional_requirements, "
            "constraints, actors, ambiguities, conflicts, questions_for_user。\n"
            "其中 functional_requirements 是数组，数组元素包含 name, description, priority。\n"
            "priority 仅允许：高 / 中 / 低。\n"
        )
        if deep_mode:
            extra = "请尽量识别潜在模糊点、冲突点、约束条件与待确认问题。\n"
        else:
            extra = "请优先保证响应速度，先提取核心功能、主要角色和关键待确认问题。\n"
        return f"{base}{extra}需求文本如下：\n{text}"

    def _build_response(self, content: str, reasoning_content: str | None, mode: str) -> RequirementAnalyzeResponse:
        parsed = self._parse_json_content(content)
        return RequirementAnalyzeResponse(
            summary=parsed.get("summary") or "需求分析已完成",
            functional_requirements=[
                RequirementItem(
                    name=item.get("name") or "未命名功能",
                    description=item.get("description") or "",
                    priority=item.get("priority"),
                )
                for item in (parsed.get("functional_requirements") or [])
                if isinstance(item, dict)
            ],
            non_functional_requirements=self._string_list(parsed.get("non_functional_requirements")),
            constraints=self._string_list(parsed.get("constraints")),
            actors=self._string_list(parsed.get("actors")),
            ambiguities=self._string_list(parsed.get("ambiguities")),
            conflicts=self._string_list(parsed.get("conflicts")),
            questions_for_user=self._string_list(parsed.get("questions_for_user")),
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
            "summary": "模型返回未完全符合 JSON 规范，已保留原始输出供人工确认。",
            "functional_requirements": [],
            "non_functional_requirements": [],
            "constraints": [],
            "actors": [],
            "ambiguities": [],
            "conflicts": [],
            "questions_for_user": ["请人工检查模型原始输出并补充结构化信息。"],
        }


requirement_service = RequirementService()
