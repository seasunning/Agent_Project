import json
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = "https://api.deepseek.com/chat/completions"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "deepseek_test_outputs")
TIMEOUT = 120

CASES = [
    {"case_id": "chat_extra_body", "label": "deepseek-chat + extra_body.thinking", "model": "deepseek-chat", "mode": "extra_body"},
    {"case_id": "chat_top_level", "label": "deepseek-chat + 顶层 thinking", "model": "deepseek-chat", "mode": "top_level"},
    {"case_id": "reasoner_model", "label": "deepseek-reasoner", "model": "deepseek-reasoner", "mode": "model_only"},
]


def now_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def write_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def write_text(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)
    return path


def headers():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def payload(case, messages, stream):
    data = {"model": case["model"], "messages": messages, "stream": stream, "temperature": 0.2}
    if case["mode"] == "extra_body":
        data["extra_body"] = {"thinking": {"type": "enabled"}}
    elif case["mode"] == "top_level":
        data["thinking"] = {"type": "enabled"}
    return data


def walk_paths(value, prefix, paths):
    if isinstance(value, dict):
        for k, v in value.items():
            p = f"{prefix}.{k}" if prefix else k
            paths.add(p)
            walk_paths(v, p, paths)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            p = f"{prefix}[{i}]"
            paths.add(p)
            walk_paths(v, p, paths)


def normalize_non_stream(body):
    choice = ((body.get("choices") or [{}])[0])
    msg = choice.get("message") or {}
    usage = body.get("usage") or {}
    reasoning = msg.get("reasoning_content")
    return {
        "id": body.get("id"),
        "object": body.get("object"),
        "created": body.get("created"),
        "model": body.get("model"),
        "system_fingerprint": body.get("system_fingerprint"),
        "finish_reason": choice.get("finish_reason"),
        "message_role": msg.get("role"),
        "message_content": msg.get("content"),
        "message_reasoning_content": reasoning,
        "has_reasoning_content": bool(reasoning),
        "usage": usage,
        "usage_fields_present": sorted(list(usage.keys())),
    }


def call_non_stream(case):
    req = payload(case, [
        {"role": "system", "content": "你是接口兼容性联调测试模型。"},
        {"role": "user", "content": "请先思考，再输出 JSON，主题是学生成绩管理系统，字段为 summary、modules、risks。"},
    ], False)
    started = time.time()
    resp = requests.post(BASE_URL, headers=headers(), json=req, timeout=TIMEOUT)
    elapsed = time.time() - started
    item = {"request": req, "status_code": resp.status_code, "headers": dict(resp.headers), "elapsed_seconds": elapsed}
    try:
        body = resp.json()
        item["response_json"] = body
        item["normalized"] = normalize_non_stream(body)
    except Exception as exc:
        item["response_text"] = resp.text
        item["parse_error"] = repr(exc)
    return item


def parse_stream(resp):
    lines = []
    chunks = []
    paths = set()
    reasoning = ""
    content = ""
    finish_reason = None
    usage = None
    parse_error = None
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        lines.append(line)
        if not line.startswith("data: "):
            continue
        text = line[6:].strip()
        if text == "[DONE]":
            chunks.append({"done": True})
            continue
        try:
            chunk = json.loads(text)
        except Exception as exc:
            chunks.append({"unparsed": text})
            if parse_error is None:
                parse_error = repr(exc)
            continue
        chunks.append(chunk)
        walk_paths(chunk, "", paths)
        choice = ((chunk.get("choices") or [{}])[0])
        delta = choice.get("delta") or {}
        if delta.get("reasoning_content"):
            reasoning += delta["reasoning_content"]
        if delta.get("content"):
            content += delta["content"]
        if choice.get("finish_reason") is not None:
            finish_reason = choice.get("finish_reason")
        if chunk.get("usage") is not None:
            usage = chunk.get("usage")
    return {
        "raw_event_lines": lines,
        "raw_chunks": chunks,
        "collected_field_paths": sorted(paths),
        "merged_reasoning_content": reasoning,
        "merged_content": content,
        "has_reasoning_content": bool(reasoning),
        "finish_reason": finish_reason,
        "usage": usage,
        "parse_error": parse_error,
    }


def call_stream(case):
    messages = [{"role": "user", "content": "9.11 和 9.8 哪个更大？请先思考再简要回答。"}]
    req1 = payload(case, messages, True)
    started = time.time()
    resp1 = requests.post(BASE_URL, headers=headers(), json=req1, timeout=TIMEOUT, stream=True)
    turn1 = {"request": req1, "status_code": resp1.status_code, "headers": dict(resp1.headers), "elapsed_seconds": time.time() - started}
    if resp1.status_code >= 400:
        turn1["response_text"] = resp1.text
        return {"turn_1": turn1, "turn_2": {"skipped": True, "reason": "turn_1_failed"}}
    turn1.update(parse_stream(resp1))
    messages.append({"role": "assistant", "content": turn1.get("merged_content", "")})
    messages.append({"role": "user", "content": "单词 strawberry 中有几个字母 R？请继续先思考再回答。"})
    req2 = payload(case, messages, True)
    started = time.time()
    resp2 = requests.post(BASE_URL, headers=headers(), json=req2, timeout=TIMEOUT, stream=True)
    turn2 = {"request": req2, "status_code": resp2.status_code, "headers": dict(resp2.headers), "elapsed_seconds": time.time() - started}
    if resp2.status_code >= 400:
        turn2["response_text"] = resp2.text
    else:
        turn2.update(parse_stream(resp2))
    return {"turn_1": turn1, "turn_2": turn2}


def summarize(case, non_stream, stream):
    ns = non_stream.get("normalized") or {}
    t1 = stream.get("turn_1") or {}
    t2 = stream.get("turn_2") or {}
    return {
        "case_id": case["case_id"],
        "label": case["label"],
        "non_stream": {
            "status_code": non_stream.get("status_code"),
            "model": ns.get("model"),
            "finish_reason": ns.get("finish_reason"),
            "has_reasoning_content": ns.get("has_reasoning_content"),
            "reasoning_length": len(ns.get("message_reasoning_content") or ""),
            "content_length": len(ns.get("message_content") or ""),
            "usage_fields_present": ns.get("usage_fields_present"),
        },
        "stream_turn_1": {
            "status_code": t1.get("status_code"),
            "has_reasoning_content": t1.get("has_reasoning_content"),
            "reasoning_length": len(t1.get("merged_reasoning_content") or ""),
            "content_length": len(t1.get("merged_content") or ""),
            "finish_reason": t1.get("finish_reason"),
            "has_reasoning_field_path": "choices[0].delta.reasoning_content" in (t1.get("collected_field_paths") or []),
        },
        "stream_turn_2": {
            "status_code": t2.get("status_code"),
            "has_reasoning_content": t2.get("has_reasoning_content"),
            "reasoning_length": len(t2.get("merged_reasoning_content") or ""),
            "content_length": len(t2.get("merged_content") or ""),
            "finish_reason": t2.get("finish_reason"),
            "has_reasoning_field_path": "choices[0].delta.reasoning_content" in (t2.get("collected_field_paths") or []),
        },
    }


def build_notes(rows):
    parts = [
        "DeepSeek 三种接入方式兼容性测试说明",
        "================================",
        "",
        "测试目标：比较三种接法是否返回 reasoning_content。",
        "",
        "结果摘要：",
    ]
    for row in rows:
        parts.extend([
            f"- {row['label']}",
            f"  - 非流式 reasoning_content: {row['non_stream']['has_reasoning_content']}，长度={row['non_stream']['reasoning_length']}",
            f"  - 流式 Turn1 reasoning_content: {row['stream_turn_1']['has_reasoning_content']}，长度={row['stream_turn_1']['reasoning_length']}，字段路径存在={row['stream_turn_1']['has_reasoning_field_path']}",
            f"  - 流式 Turn2 reasoning_content: {row['stream_turn_2']['has_reasoning_content']}，长度={row['stream_turn_2']['reasoning_length']}，字段路径存在={row['stream_turn_2']['has_reasoning_field_path']}",
            "",
        ])
    parts.extend([
        "对接建议：",
        "1. 后端统一保留 content、reasoning_content、finish_reason、usage、model、id。",
        "2. reasoning_content 必须作为可选字段处理。",
        "3. 前端先保证 content 流式渲染，再决定是否展示 reasoning 通道。",
    ])
    return "\n".join(parts)


def main():
    ensure_output_dir()
    stamp = now_str()
    full = {"timestamp": stamp, "base_url": BASE_URL, "cases": {}}
    rows = []
    for case in CASES:
        print(f"开始测试：{case['label']}")
        non_stream = call_non_stream(case)
        stream = call_stream(case)
        full["cases"][case["case_id"]] = {"case": case, "non_stream": non_stream, "stream": stream}
        rows.append(summarize(case, non_stream, stream))
    summary = {"timestamp": stamp, "results": rows}
    files = {
        "compat_full": write_json(f"{stamp}_compat_full.json", full),
        "compat_summary": write_json(f"{stamp}_compat_summary.json", summary),
        "compat_notes": write_text(f"{stamp}_compat_notes.txt", build_notes(rows)),
    }
    print("兼容性测试完成，输出文件如下：")
    for name, path in files.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
