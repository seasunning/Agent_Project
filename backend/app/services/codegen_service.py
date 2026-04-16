import json
import re
import shutil
from collections.abc import AsyncGenerator
from pathlib import Path

from app.schemas.codegen import (
    CodeFile,
    CodeGenerateRequest,
    CodeGenerateResponse,
    CodePersistResponse,
    CodePreviewRequest,
    CodeStreamEvent,
    CodeSuggestResponse,
    CodeSuggestStreamEvent,
    CodegenOptions,
)
from app.schemas.llm import ChatMessage, LLMInvokeRequest
from app.services.deepseek_service import deepseek_service


class CodegenService:
    def __init__(self):
        self.output_root = Path.cwd() / 'generated_projects'

    async def suggest_options(self, design) -> CodeSuggestResponse:
        request = self._build_suggest_request(design, stream=False)
        result = await deepseek_service.invoke(request)
        return self._build_suggest_response(result.content, result.reasoning_content)

    async def suggest_options_stream(self, design) -> AsyncGenerator[CodeSuggestStreamEvent, None]:
        yield CodeSuggestStreamEvent(type='status', content='正在连接模型，开始智能选型...')
        request = self._build_suggest_request(design, stream=True)
        content = ''
        reasoning = ''
        async for event in deepseek_service.stream(request):
            if event.type == 'reasoning':
                reasoning += event.content
                yield CodeSuggestStreamEvent(type='content', content=event.content)
            elif event.type == 'content':
                content += event.content
                yield CodeSuggestStreamEvent(type='content', content=event.content)
            elif event.type == 'meta':
                yield CodeSuggestStreamEvent(type='status', content='模型正在整理技术选型建议...')
            elif event.type == 'done':
                response = self._build_suggest_response(content, reasoning or None)
                yield CodeSuggestStreamEvent(type='result', result=response)
                yield CodeSuggestStreamEvent(type='done', content='智能选型完成')

    async def generate(self, request: CodeGenerateRequest) -> CodeGenerateResponse:
        plan, reasoning_parts, raw_parts = await self._generate_plan(request)
        files, file_reasoning, file_raw = await self._generate_files(request, plan)
        reasoning_parts.extend(file_reasoning)
        raw_parts.extend(file_raw)
        return self._build_response(plan, files, '\n'.join(raw_parts), '\n'.join(filter(None, reasoning_parts)) or None, request.mode)

    async def preview(self, request: CodePreviewRequest) -> CodeGenerateResponse:
        plan = self._build_preview_plan(request)
        files = [
            CodeFile(
                path=path,
                language=self._infer_language(path),
                description='测试预览文件',
                content=self._placeholder_content(path),
            )
            for path in plan['file_paths']
        ]
        return self._build_response(plan, files, raw_output='本次为测试预览结果，未调用完整代码生成。', reasoning_content=None, mode=request.mode)

    async def generate_stream(self, request: CodeGenerateRequest) -> AsyncGenerator[CodeStreamEvent, None]:
        yield CodeStreamEvent(type='status', mode=request.mode, content='第一步：正在规划项目文件树与启动步骤...')
        plan, reasoning_parts, raw_parts = await self._generate_plan_streaming(request)
        tech_stack = self._string_list(plan.get('tech_stack')) or self._fallback_tech_stack(request.options)
        plan['tech_stack'] = tech_stack
        file_paths = self._string_list(plan.get('file_paths'))
        yield CodeStreamEvent(type='content', mode=request.mode, content=f'\n[文件树规划完成]\n{self._build_tree(file_paths)}\n')
        yield CodeStreamEvent(type='status', mode=request.mode, content=f'第二步：开始逐个生成 {len(file_paths)} 个关键文件...')
        files: list[CodeFile] = []
        file_reasoning, file_raw = [], []
        for index, path in enumerate(file_paths, start=1):
            yield CodeStreamEvent(type='status', mode=request.mode, content=f'正在生成关键文件 {index}/{len(file_paths)} - {path}')
            file = await self._generate_single_file_streaming(request, plan, path)
            files.append(file['file'])
            if file['reasoning']:
                file_reasoning.append(file['reasoning'])
                yield CodeStreamEvent(type='reasoning', mode=request.mode, content=file['reasoning'])
            file_raw.append(file['raw'])
            yield CodeStreamEvent(type='content', mode=request.mode, content=f'\n[已完成] {path}\n{file["preview"]}\n')

        reasoning_parts.extend(file_reasoning)
        raw_parts.extend(file_raw)
        response = self._build_response(plan, files, '\n'.join(raw_parts), '\n'.join(filter(None, reasoning_parts)) or None, request.mode)
        yield CodeStreamEvent(type='result', mode=request.mode, result=response)
        yield CodeStreamEvent(type='done', mode=request.mode, content='代码原型两阶段流式生成完成')

    def persist_project(self, result: CodeGenerateResponse, project_name: str = '', options: CodegenOptions | None = None) -> CodePersistResponse:
        base_name = self._resolve_project_name(project_name, result.project_summary)
        output_dir = self._resolve_unique_project_dir(base_name)
        output_dir.mkdir(parents=True, exist_ok=True)
        written_files: list[str] = []

        for file in result.files:
            relative_path = Path(file.path.replace('\\', '/'))
            target_path = output_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(file.content, encoding='utf-8')
            written_files.append(relative_path.as_posix())

        startup_script = self._write_startup_script(output_dir, result.startup_steps)
        skeleton_files = self._write_project_skeleton(output_dir, output_dir.name, result, options)
        written_files.extend(skeleton_files)
        archive_name = self._create_archive(output_dir)
        return CodePersistResponse(
            project_name=output_dir.name,
            output_path=str(output_dir),
            written_files=written_files,
            startup_script=startup_script,
            archive_name=archive_name,
        )

    async def _generate_plan(self, request: CodeGenerateRequest):
        llm_request = self._build_plan_request(request, stream=False)
        result = await deepseek_service.invoke(llm_request)
        plan = self._normalize_plan(self._parse_json_content(result.content), request.options)
        return plan, [result.reasoning_content or ''], [f'=== 文件树规划 ===\n{result.content}']

    def ensure_project_persisted(self, result: CodeGenerateResponse, project_name: str = '', options: CodegenOptions | None = None) -> CodePersistResponse:
        resolved_name = self._resolve_project_name(project_name, result.project_summary)
        existing_dir = self.output_root / resolved_name
        existing_archive = self.output_root / f'{resolved_name}.zip'
        if existing_dir.exists() and existing_archive.exists():
            return CodePersistResponse(
                project_name=resolved_name,
                output_path=str(existing_dir),
                written_files=self._list_existing_files(existing_dir),
                startup_script='STARTUP_STEPS.txt' if (existing_dir / 'STARTUP_STEPS.txt').exists() else None,
                archive_name=existing_archive.name,
            )
        return self.persist_project(result, project_name, options)

    async def _generate_plan_streaming(self, request: CodeGenerateRequest):
        llm_request = self._build_plan_request(request, stream=True)
        reasoning = ''
        content = ''
        async for event in deepseek_service.stream(llm_request):
            if event.type == 'reasoning':
                reasoning += event.content
            elif event.type == 'content':
                content += event.content
        plan = self._normalize_plan(self._parse_json_content(content), request.options)
        return plan, [reasoning], [f'=== 文件树规划 ===\n{content}']

    async def _generate_files(self, request: CodeGenerateRequest, plan: dict):
        files = []
        reasoning_parts = []
        raw_parts = []
        for path in self._string_list(plan.get('file_paths')):
            generated = await self._generate_single_file(request, plan, path)
            files.append(generated['file'])
            reasoning_parts.append(generated['reasoning'])
            raw_parts.append(generated['raw'])
        return files, reasoning_parts, raw_parts

    async def _generate_single_file(self, request: CodeGenerateRequest, plan: dict, path: str):
        llm_request = self._build_file_request(request, plan, path, stream=False)
        result = await deepseek_service.invoke(llm_request)
        return self._build_file_payload(path, result.content, result.reasoning_content or '')

    async def _generate_single_file_streaming(self, request: CodeGenerateRequest, plan: dict, path: str):
        llm_request = self._build_file_request(request, plan, path, stream=True)
        reasoning = ''
        content = ''
        async for event in deepseek_service.stream(llm_request):
            if event.type == 'reasoning':
                reasoning += event.content
            elif event.type == 'content':
                content += event.content
        return self._build_file_payload(path, content, reasoning)

    def _build_file_payload(self, path: str, raw_content: str, reasoning: str):
        parsed = self._parse_json_content(raw_content)
        code_file = CodeFile(
            path=str(parsed.get('path') or path),
            language=str(parsed.get('language') or self._infer_language(path)),
            description=str(parsed.get('description') or '关键实现文件'),
            content=str(parsed.get('content') or ''),
        )
        return {
            'file': code_file,
            'reasoning': reasoning,
            'raw': f'=== 文件 {path} ===\n{raw_content}',
            'preview': self._preview_code(code_file.content),
        }

    def _build_suggest_request(self, design, stream: bool) -> LLMInvokeRequest:
        design_json = json.dumps(design.model_dump(mode='json'), ensure_ascii=False, indent=2)
        return LLMInvokeRequest(
            messages=[
                ChatMessage(role='system', content='你是资深技术架构师，请基于设计方案输出严格 JSON 技术选型。不要输出 markdown。'),
                ChatMessage(role='user', content=self._suggest_prompt(design_json)),
            ],
            enable_thinking=True,
            temperature=0.1,
            max_tokens=2000,
            stream=stream,
        )

    def _build_plan_request(self, request: CodeGenerateRequest, stream: bool) -> LLMInvokeRequest:
        design_json = json.dumps(request.design.model_dump(mode='json'), ensure_ascii=False, indent=2)
        options_json = json.dumps(request.options.model_dump(mode='json'), ensure_ascii=False, indent=2)
        return LLMInvokeRequest(
            messages=[
                ChatMessage(role='system', content='你是资深全栈工程师，请先规划代码原型的文件树与启动步骤。输出严格 JSON，不要 markdown。'),
                ChatMessage(role='user', content=self._plan_prompt(design_json, options_json)),
            ],
            enable_thinking=request.mode == 'deep',
            temperature=0.1,
            max_tokens=4000,
            stream=stream,
        )

    def _build_file_request(self, request: CodeGenerateRequest, plan: dict, path: str, stream: bool) -> LLMInvokeRequest:
        design_json = json.dumps(request.design.model_dump(mode='json'), ensure_ascii=False, indent=2)
        options_json = json.dumps(request.options.model_dump(mode='json'), ensure_ascii=False, indent=2)
        plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
        return LLMInvokeRequest(
            messages=[
                ChatMessage(role='system', content='你是资深全栈工程师，请只生成单个文件的严格 JSON 结果。不要 markdown。'),
                ChatMessage(role='user', content=self._file_prompt(design_json, options_json, plan_json, path)),
            ],
            enable_thinking=request.mode == 'deep',
            temperature=0.1,
            max_tokens=5000,
            stream=stream,
        )

    @staticmethod
    def _suggest_prompt(design_json: str) -> str:
        return (
            '请基于以下设计方案，为代码原型生成推荐技术选型。\n'
            '必须输出严格 JSON，对象字段仅包含 language, backend_framework, frontend_framework, database。\n'
            '数据库可为 MySQL / SQLite / PostgreSQL / 不需要，也可以是其他自定义数据库。\n'
            f'设计方案如下：\n{design_json}'
        )

    @staticmethod
    def _plan_prompt(design_json: str, options_json: str) -> str:
        return (
            '请基于以下设计方案和技术选型，先输出代码原型规划。\n'
            '必须输出严格 JSON，对象字段仅包含：project_summary, tech_stack, file_paths, startup_steps。\n'
            'tech_stack 必须给出非空字符串数组。\n'
            'file_paths 为字符串数组，只保留 4 到 8 个最关键文件路径。\n'
            'startup_steps 为不带编号前缀的字符串数组。\n'
            'file_paths 要体现清晰的前后端目录结构。\n'
            f'技术选型如下：\n{options_json}\n\n设计方案如下：\n{design_json}'
        )

    @staticmethod
    def _file_prompt(design_json: str, options_json: str, plan_json: str, path: str) -> str:
        return (
            '请基于以下设计方案、技术选型与文件规划，仅生成一个关键文件。\n'
            '必须输出严格 JSON，对象字段仅包含：path, language, description, content。\n'
            'content 必须是该文件完整文本。\n'
            f'目标文件路径：{path}\n\n技术选型如下：\n{options_json}\n\n文件规划如下：\n{plan_json}\n\n设计方案如下：\n{design_json}'
        )

    def _build_suggest_response(self, content: str, reasoning: str | None) -> CodeSuggestResponse:
        parsed = self._parse_json_content(content)
        options = CodegenOptions(
            language=str(parsed.get('language') or 'Python'),
            backend_framework=str(parsed.get('backend_framework') or 'FastAPI'),
            frontend_framework=str(parsed.get('frontend_framework') or 'Vue 3'),
            database=str(parsed.get('database') or 'MySQL'),
        )
        return CodeSuggestResponse(options=options, reasoning=reasoning, raw_model_output=content)

    def _normalize_plan(self, plan: dict, options: CodegenOptions) -> dict:
        file_paths = self._limit_file_paths(self._string_list(plan.get('file_paths')))
        startup_steps = self._normalize_steps(self._string_list(plan.get('startup_steps')))
        tech_stack = self._string_list(plan.get('tech_stack')) or self._fallback_tech_stack(options)
        if not startup_steps:
            startup_steps = ['安装依赖', '启动后端服务', '启动前端服务', '访问应用首页']
        return {
            'project_summary': str(plan.get('project_summary') or '已根据设计方案生成代码原型。'),
            'tech_stack': tech_stack,
            'file_paths': file_paths,
            'startup_steps': startup_steps,
        }

    def _build_response(self, plan: dict, files: list[CodeFile], raw_output: str, reasoning_content: str | None, mode: str) -> CodeGenerateResponse:
        return CodeGenerateResponse(
            project_summary=str(plan.get('project_summary') or '已根据设计方案生成代码原型。'),
            tech_stack=self._string_list(plan.get('tech_stack')) or self._fallback_tech_stack_from_plan(plan),
            file_tree=self._build_tree(self._string_list(plan.get('file_paths'))),
            files=files,
            startup_steps=self._normalize_steps(self._string_list(plan.get('startup_steps'))),
            raw_model_output=raw_output,
            reasoning_content=reasoning_content,
            mode=mode,
        )

    def _build_preview_plan(self, request: CodePreviewRequest) -> dict:
        design = request.design
        module_paths = []
        for module in design.modules[:6]:
            safe_name = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]+', '_', module.name).strip('_') or 'module'
            module_paths.append(f'backend/{safe_name}.py')
        file_paths = module_paths or ['backend/app.py', 'frontend/src/App.vue']
        architecture = design.architecture_style.strip() or '设计方案'
        return {
            'project_summary': f'{architecture}（测试预览）',
            'tech_stack': self._fallback_tech_stack(request.options),
            'file_paths': file_paths,
            'startup_steps': ['这是测试预览，不生成完整工程', '如需完整代码请使用正式生成'],
        }

    @staticmethod
    def _placeholder_content(path: str) -> str:
        name = Path(path).stem or 'module'
        suffix = Path(path).suffix.lower()
        if suffix == '.py':
            return f'# {name} 功能\n'
        if suffix in {'.js', '.ts'}:
            return f'// {name} 功能\n'
        if suffix == '.vue':
            return f'<!-- {name} 功能 -->\n'
        return f'# {name} 功能\n'

    @staticmethod
    def _list_existing_files(output_dir: Path) -> list[str]:
        return [str(path.relative_to(output_dir)).replace('\\', '/') for path in output_dir.rglob('*') if path.is_file()]

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _limit_file_paths(paths: list[str]) -> list[str]:
        deduped = []
        seen = set()
        for path in paths:
            normalized = path.replace('\\', '/').strip('./ ')
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped[:8]

    @staticmethod
    def _normalize_steps(steps: list[str]) -> list[str]:
        normalized = []
        seen = set()
        for step in steps:
            cleaned = re.sub(r'^\s*\d+([\.)、\-:：]\d+)*[\.)、\-:：]*\s*', '', step).strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        return normalized

    @staticmethod
    def _parse_json_content(content: str) -> dict:
        text = content.strip()
        if text.startswith('```'):
            text = text.replace('```json', '').replace('```', '').strip()
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            repaired = CodegenService._extract_json_object(text)
            if repaired:
                try:
                    data = json.loads(repaired)
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    pass
        return {}

    @staticmethod
    def _extract_json_object(text: str) -> str | None:
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start:end + 1]

    @staticmethod
    def _infer_language(path: str) -> str:
        suffix = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
        return {
            'py': 'Python',
            'java': 'Java',
            'cs': 'C#',
            'cpp': 'C++',
            'vue': 'Vue',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'json': 'JSON',
            'md': 'Markdown',
        }.get(suffix, 'text')

    @staticmethod
    def _preview_code(content: str) -> str:
        lines = content.splitlines()
        preview = '\n'.join(lines[:10]).strip()
        return preview or '(空文件内容)'

    @staticmethod
    def _fallback_tech_stack(options: CodegenOptions) -> list[str]:
        return [item for item in [options.language, options.backend_framework, options.frontend_framework, options.database] if item]

    @staticmethod
    def _fallback_tech_stack_from_plan(plan: dict) -> list[str]:
        value = plan.get('tech_stack')
        if isinstance(value, list) and value:
            return [str(item) for item in value]
        return []

    @staticmethod
    def _build_tree(paths: list[str]) -> str:
        tree: dict[str, dict] = {}
        for path in paths:
            node = tree
            parts = [part for part in path.split('/') if part]
            for part in parts:
                node = node.setdefault(part, {})

        lines: list[str] = []

        def walk(node: dict[str, dict], prefix: str = ''):
            items = list(node.items())
            for index, (name, child) in enumerate(items):
                is_last = index == len(items) - 1
                branch = '└── ' if is_last else '├── '
                lines.append(f'{prefix}{branch}{name}')
                if child:
                    walk(child, prefix + ('    ' if is_last else '│   '))

        walk(tree)
        return '\n'.join(lines) if lines else '暂无文件树'

    def _resolve_project_name(self, custom_name: str, summary: str) -> str:
        if custom_name.strip():
            return custom_name.strip()
        matched = re.search(r'([^，。；：\n]+系统)', summary)
        if matched:
            return matched.group(1).strip()
        trimmed = re.split(r'[，。；：\n]', summary.strip())[0].strip()
        return trimmed[:40] or 'generated-project'

    def _resolve_unique_project_dir(self, base_name: str) -> Path:
        candidate = self.output_root / base_name
        if not candidate.exists():
            return candidate
        index = 1
        while True:
            next_candidate = self.output_root / f'{base_name}({index})'
            if not next_candidate.exists():
                return next_candidate
            index += 1

    def _write_project_skeleton(self, output_dir: Path, project_name: str, result: CodeGenerateResponse, options: CodegenOptions | None) -> list[str]:
        written: list[str] = []
        readme_path = output_dir / 'README.md'
        tech_stack = '\n'.join(f'- {item}' for item in result.tech_stack) or '- 待补充'
        startup = '\n'.join(f'{index + 1}. {step}' for index, step in enumerate(result.startup_steps)) or '1. 暂无'
        readme_path.write_text(
            f'# {project_name}\n\n## 项目摘要\n{result.project_summary}\n\n## 技术栈\n{tech_stack}\n\n## 启动步骤\n{startup}\n',
            encoding='utf-8',
        )
        written.append('README.md')

        env_path = output_dir / '.env.example'
        env_path.write_text('APP_ENV=development\nAPI_BASE_URL=http://127.0.0.1:8000\n', encoding='utf-8')
        written.append('.env.example')

        if options:
            backend_framework = options.backend_framework.lower()
            frontend_framework = options.frontend_framework.lower()
            language = options.language.lower()
            if 'python' in language:
                req_path = output_dir / 'requirements.txt'
                req_path.write_text('fastapi\nuvicorn[standard]\n', encoding='utf-8')
                written.append('requirements.txt')
            if any(item in frontend_framework for item in ['vue', 'react', 'angular']):
                pkg_path = output_dir / 'package.json'
                pkg_path.write_text(
                    json.dumps(
                        {
                            'name': project_name,
                            'private': True,
                            'version': '0.1.0',
                            'scripts': {'dev': 'vite', 'build': 'vite build'},
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding='utf-8',
                )
                written.append('package.json')
        return written

    @staticmethod
    def _write_startup_script(output_dir: Path, startup_steps: list[str]) -> str | None:
        if not startup_steps:
            return None
        script_path = output_dir / 'STARTUP_STEPS.txt'
        lines = [f'{index + 1}. {step}' for index, step in enumerate(startup_steps)]
        script_path.write_text('\n'.join(lines), encoding='utf-8')
        return script_path.name

    @staticmethod
    def _create_archive(output_dir: Path) -> str | None:
        archive_base = output_dir.parent / output_dir.name
        archive_path = shutil.make_archive(str(archive_base), 'zip', root_dir=output_dir)
        return Path(archive_path).name


codegen_service = CodegenService()
