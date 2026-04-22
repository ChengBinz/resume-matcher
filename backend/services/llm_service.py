from openai import AsyncOpenAI
from config import settings
from utils.prompt_loader import load_prompt, render_prompt
from utils.json_parser import strip_think_blocks, extract_json_object, extract_question_objects

client = AsyncOpenAI(
    base_url=settings.VLLM_BASE_URL,
    api_key=settings.VLLM_API_KEY,
)


def _extract_content(response) -> str:
    """从 LLM 响应中提取文本内容。

    兼容不同 API 网关对 thinking 模式的处理差异：
    - 标准模式：content 包含全部输出
    - thinking 模式（vLLM/Ollama）：content 包含 <think>...</think> + 正文
    - thinking 模式（OneAPI 等转发网关）：思考在 reasoning_content，正文在 content
    - 某些情况下 content 为 None，需要从 reasoning_content 中提取
    """
    message = response.choices[0].message
    parts = []

    # 尝试获取 reasoning_content（部分网关将 thinking 输出放在此字段）
    reasoning = getattr(message, "reasoning_content", None)
    if reasoning:
        parts.append(reasoning)

    # 获取 content 主体
    if message.content:
        parts.append(message.content)

    if not parts:
        raise ValueError("LLM 返回内容为空：content 和 reasoning_content 均为 None")

    combined = "\n".join(parts)
    return strip_think_blocks(combined)


async def _call_llm(messages: list[dict], temperature: float = 0.3, max_tokens: int | None = None) -> str:
    """统一的 LLM 调用入口，返回清洗后的文本"""
    response = await client.chat.completions.create(
        model=settings.VLLM_MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
    )
    return _extract_content(response)


async def evaluate_resume(resume_text: str, jd_text: str) -> dict:
    """调用 LLM 评估简历与 JD 的匹配度"""
    system_prompt = load_prompt("system")
    user_prompt = render_prompt("user", jd=jd_text, resume=resume_text)

    content = await _call_llm(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    result = extract_json_object(content)
    if result is None:
        raise ValueError(f"LLM 返回内容无法解析为JSON: {content[:500]}")
    return result


async def generate_interview_questions(resume_text: str, jd_text: str) -> dict:
    """根据简历内容生成面试问题"""
    user_prompt = render_prompt("interview_questions", jd=jd_text, resume=resume_text)

    content = await _call_llm(
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=settings.LLM_MAX_TOKENS * 2,
    )

    result = extract_json_object(content, required_key="questions")
    if result is None:
        raise ValueError(f"LLM 返回内容无法解析为JSON: {content[:500]}")
    return result


async def stream_interview_questions(resume_text: str, jd_text: str):
    """流式生成面试问题，逐个 yield 完成的问题对象"""
    user_prompt = render_prompt("interview_questions", jd=jd_text, resume=resume_text)

    stream = await client.chat.completions.create(
        model=settings.VLLM_MODEL_NAME,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.5,
        max_tokens=settings.LLM_MAX_TOKENS * 2,
        stream=True,
    )

    accumulated = ""
    yielded_count = 0

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None) or ""
        reasoning = getattr(delta, "reasoning_content", None) or ""
        accumulated += reasoning + content

        cleaned = strip_think_blocks(accumulated)
        # 如果存在未关闭的 <think> 块，跳过解析
        if "<think>" in cleaned:
            continue

        questions = extract_question_objects(cleaned)
        while yielded_count < len(questions):
            yield questions[yielded_count]
            yielded_count += 1
