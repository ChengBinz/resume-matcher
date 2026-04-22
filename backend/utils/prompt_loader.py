from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """加载指定名称的提示词文件内容。

    Args:
        name: 提示词文件名（不含扩展名），如 'system'、'user'

    Returns:
        提示词文本内容
    """
    prompt_path = PROMPTS_DIR / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def render_prompt(name: str, **kwargs) -> str:
    """加载并渲染带变量的提示词模板。

    Args:
        name: 提示词文件名（不含扩展名）
        **kwargs: 模板变量键值对

    Returns:
        渲染后的提示词文本
    """
    template = load_prompt(name)
    return template.format(**kwargs)
