import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = "https://api.deepseek.com/chat/completions"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "deepseek_test_outputs")
TIMEOUT = 120


def now_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def write_json(filename: str, data: Any) -> str:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def write_text(filename: str, data: str) -> str:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)
    return path


def build_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def build_payload(messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
    return {
        "model": "deepseek-chat",
        "messages": messages,
        "stream": stream,
        "temperature": 0.2,
        "extra_body": {
            "thinking": {"type": "enabled"}
        },
    }


def call_non_stream() -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": "你是一个用于接口联调测试的模型。请先进行思考，再用 JSON 返回一个简短结果。"},
        {
            "role": "user",
            "content": (
                "请分析以下需求并返回简短 JSON："
                "用户需要一个图书管理系统，支持图书录入、借阅、归还、库存查询。"
                "请输出字段：summary, modules, risks。"
            ),
        },
    ]

    payload = build_payload(messages, stream=False)
    started = time.time()
    response = requests.post(BASE_URL, headers=build_headers(), json=payload, timeout=TIMEOUT)
    elapsed = time.time() - started
    response.raise_for_status()

    data = response.json()
    return {
        "request": payload,
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "elapsed_seconds": elapsed,
        "response_json": data,
        "normalized": normalize_non_stream(data),
    }


def normalize_non_stream(data: Dict[str, Any]) -> Dict[str, Any]:
    choice0 = ((data.get("choices") or [{}])[0])
    message = choice0.get("message") or {}
    usage = data.get("usage") or {}
    return {
        "id": data.get("id"),
        "object": data.get("object"),
        "created": data.get("created"),
        "model": data.get("model"),
        "system_fingerprint": data.get("system_fingerprint"),
        "choice_index": choice0.get("index"),
        "finish_reason": choice0.get("finish_reason"),
        "message_role": message.get("role"),
        "message_content": message.get("content"),
        "message_reasoning_content": message.get("reasoning_content"),
        "usage": usage,
        "usage_fields_present": sorted(list(usage.keys())),
    }


def call_stream() -> Dict[str, Any]:
    messages = [{"role": "user", "content": "9.11 和 9.8 哪个更大？请先思考再简要回答。"}]
    payload = build_payload(messages, stream=True)

    raw_chunks: List[Dict[str, Any]] = []
    text_lines: List[str] = []
    reasoning_content = ""
    content = ""
    field_paths = set()

    started = time.time()
    with requests.post(BASE_URL, headers=build_headers(), json=payload, timeout=TIMEOUT, stream=True) as response:
        elapsed = time.time() - started
        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            text_lines.append(line)
            if not line.startswith("data: "):
                continue

            data_str = line[6:].strip()
            if data_str == "[DONE]":
                raw_chunks.append({"done": True})
                continue

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                raw_chunks.append({"unparsed": data_str})
                continue

            raw_chunks.append(chunk)
            collect_paths(chunk, prefix="", paths=field_paths)

            choices = chunk.get("choices") or []
            if not choices:
                continue

            delta = (choices[0].get("delta") or {})
            reasoning_piece = delta.get("reasoning_content")
            content_piece = delta.get("content")

            if reasoning_piece:
                reasoning_content += reasoning_piece
            if content_piece:
                content += content_piece

    turn_1_assistant = content

    messages.append({"role": "assistant", "content": turn_1_assistant})
    messages.append({"role": "user", "content": "单词 strawberry 中有几个字母 R？请继续先思考再回答。"})

    payload_turn_2 = build_payload(messages, stream=True)
    raw_chunks_turn_2: List[Dict[str, Any]] = []
    text_lines_turn_2: List[str] = []
    reasoning_content_turn_2 = ""
    content_turn_2 = ""
    field_paths_turn_2 = set()

    started_turn_2 = time.time()
    with requests.post(BASE_URL, headers=build_headers(), json=payload_turn_2, timeout=TIMEOUT, stream=True) as response:
        elapsed_turn_2 = time.time() - started_turn_2
        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            text_lines_turn_2.append(line)
            if not line.startswith("data: "):
                continue

            data_str = line[6:].strip()
            if data_str == "[DONE]":
                raw_chunks_turn_2.append({"done": True})
                continue

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                raw_chunks_turn_2.append({"unparsed": data_str})
                continue

            raw_chunks_turn_2.append(chunk)
            collect_paths(chunk, prefix="", paths=field_paths_turn_2)

            choices = chunk.get("choices") or []
            if not choices:
                continue

            delta = (choices[0].get("delta") or {})
            reasoning_piece = delta.get("reasoning_content")
            content_piece = delta.get("content")

            if reasoning_piece:
                reasoning_content_turn_2 += reasoning_piece
            if content_piece:
                content_turn_2 += content_piece

    return {
        "turn_1": {
            "request": payload,
            "elapsed_seconds": elapsed,
            "raw_event_lines": text_lines,
            "raw_chunks": raw_chunks,
            "collected_field_paths": sorted(field_paths),
            "merged_reasoning_content": reasoning_content,
            "merged_content": content,
        },
        "turn_2": {
            "request": payload_turn_2,
            "elapsed_seconds": elapsed_turn_2,
            "raw_event_lines": text_lines_turn_2,
            "raw_chunks": raw_chunks_turn_2,
            "collected_field_paths": sorted(field_paths_turn_2),
            "merged_reasoning_content": reasoning_content_turn_2,
            "merged_content": content_turn_2,
        },
    }


def collect_paths(value: Any, prefix: str, paths: set) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            paths.add(child_prefix)
            collect_paths(child, child_prefix, paths)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            paths.add(child_prefix)
            collect_paths(child, child_prefix, paths)


def build_field_notes(non_stream: Dict[str, Any], stream: Dict[str, Any]) -> str:
    return (
        "DeepSeek 接口测试字段记录\n"
        "========================\n\n"
        "一、非流式返回中建议前端重点关注字段\n"
        "- id: 请求唯一标识\n"
        "- object: 返回对象类型\n"
        "- created: 时间戳\n"
        "- model: 实际模型名\n"
        "- choices[0].index: 选择序号\n"
        "- choices[0].finish_reason: 停止原因\n"
        "- choices[0].message.role: 消息角色\n"
        "- choices[0].message.content: 最终回答\n"
        "- choices[0].message.reasoning_content: 思考内容（若返回）\n"
        "- usage.*: token 消耗统计\n\n"
        "二、流式返回中建议前端重点关注字段\n"
        "- 每个 SSE 事件以 data: 开头\n"
        "- [DONE] 表示流结束\n"
        "- chunk.id / chunk.model / chunk.created: 基础元数据\n"
        "- chunk.choices[0].delta.reasoning_content: 思考流增量\n"
        "- chunk.choices[0].delta.content: 最终回答流增量\n"
        "- chunk.choices[0].finish_reason: 当前 chunk 或最后结束原因\n\n"
        "三、当前测试观测结果摘要\n"
        f"- 非流式 model: {non_stream.get('normalized', {}).get('model')}\n"
        f"- 非流式 usage 字段: {non_stream.get('normalized', {}).get('usage_fields_present')}\n"
        f"- 流式 Turn1 字段路径数: {len(stream.get('turn_1', {}).get('collected_field_paths', []))}\n"
        f"- 流式 Turn2 字段路径数: {len(stream.get('turn_2', {}).get('collected_field_paths', []))}\n\n"
        "四、前后端对接建议\n"
        "- 后端统一将 DeepSeek 原始返回保存一份，避免字段遗漏。\n"
        "- 流式模式下，前端至少需要区分 reasoning_content 与 content 两条渲染通道。\n"
        "- 对 finish_reason、usage、id 建议完整透传，方便日志追踪与计费统计。\n"
        "- 如果前端不展示思考内容，也建议后端保留 reasoning_content 以便调试。\n"
    )


def main() -> None:
    ensure_output_dir()
    stamp = now_str()

    print("开始测试 DeepSeek 非流式接口...")
    non_stream_result = call_non_stream()
    print("开始测试 DeepSeek 流式接口...")
    stream_result = call_stream()

    summary = {
        "timestamp": stamp,
        "non_stream_normalized": non_stream_result.get("normalized"),
        "stream_turn_1_preview": {
            "reasoning_length": len(stream_result["turn_1"].get("merged_reasoning_content", "")),
            "content_length": len(stream_result["turn_1"].get("merged_content", "")),
            "field_paths": stream_result["turn_1"].get("collected_field_paths", []),
        },
        "stream_turn_2_preview": {
            "reasoning_length": len(stream_result["turn_2"].get("merged_reasoning_content", "")),
            "content_length": len(stream_result["turn_2"].get("merged_content", "")),
            "field_paths": stream_result["turn_2"].get("collected_field_paths", []),
        },
    }

    files = {
        "non_stream": write_json(f"{stamp}_non_stream.json", non_stream_result),
        "stream": write_json(f"{stamp}_stream.json", stream_result),
        "summary": write_json(f"{stamp}_summary.json", summary),
        "field_notes": write_text(f"{stamp}_field_notes.txt", build_field_notes(non_stream_result, stream_result)),
    }

    print("测试完成，输出文件如下：")
    for name, path in files.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
