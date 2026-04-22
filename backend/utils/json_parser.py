import json
import re


def strip_think_blocks(text: str) -> str:
    """去除 Qwen3 模型 <think>...</think> 思考块"""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text)
    return cleaned.strip()


def extract_json_object(text: str, required_key: str = "overall_score") -> dict | None:
    """从文本中提取第一个包含指定 key 的完整 JSON 对象。

    使用平衡大括号算法逐个尝试候选 JSON 块，
    直到找到能成功解析且包含 required_key 的对象。

    Args:
        text: 包含 JSON 的原始文本（可能含有思考过程等干扰内容）
        required_key: JSON 对象中必须包含的字段名

    Returns:
        解析后的 dict 或 None
    """
    search_start = 0
    while search_start < len(text):
        start = text.find("{", search_start)
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape_next = False

        for i in range(start, len(text)):
            ch = text[i]

            if escape_next:
                escape_next = False
                continue

            if ch == "\\":
                if in_string:
                    escape_next = True
                continue

            if ch == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    json_str = text[start:i + 1]
                    try:
                        obj = json.loads(json_str)
                        if required_key in obj:
                            return obj
                    except json.JSONDecodeError:
                        pass
                    search_start = i + 1
                    break
        else:
            return None

    return None


def extract_question_objects(text: str) -> list[dict]:
    """从部分文本中提取所有完整的面试问题 JSON 对象。

    用于流式输出场景，逐步从累积文本中提取已完成的问题对象。
    每个有效对象必须包含 'id' 和 'question' 字段。
    """
    questions = []
    search_start = 0
    while search_start < len(text):
        start = text.find("{", search_start)
        if start == -1:
            break

        depth = 0
        in_string = False
        escape_next = False
        found_end = False

        for i in range(start, len(text)):
            ch = text[i]

            if escape_next:
                escape_next = False
                continue

            if ch == "\\" and in_string:
                escape_next = True
                continue

            if ch == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        obj = json.loads(candidate)
                        if isinstance(obj, dict) and "id" in obj and "question" in obj:
                            questions.append(obj)
                            search_start = i + 1
                        else:
                            search_start = start + 1
                    except json.JSONDecodeError:
                        search_start = start + 1
                    found_end = True
                    break

        if not found_end:
            search_start = start + 1

    return questions
