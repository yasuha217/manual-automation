"""Claude API クライアント - Anthropic SDKの薄いラッパー"""

import anthropic
from src.config import config


def create_client() -> anthropic.Anthropic:
    """Anthropicクライアントを生成"""
    return anthropic.Anthropic(api_key=config.anthropic_api_key)


def call_claude(
    messages: list[dict],
    system: str = "",
    max_tokens: int = 8000,
    model: str | None = None,
) -> str:
    """Claude APIを呼び出しテキストレスポンスを返す

    Args:
        messages: [{"role": "user"|"assistant", "content": "..."}]
        system: システムプロンプト
        max_tokens: 最大トークン数
        model: モデルID（省略時はconfig.claude_model）

    Returns:
        レスポンステキスト
    """
    client = create_client()
    kwargs: dict = {
        "model": model or config.claude_model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    return response.content[0].text


def call_claude_conversation(
    conversation: list[dict],
    system: str = "",
    max_tokens: int = 8000,
) -> tuple[str, list[dict]]:
    """会話を続けながらClaude APIを呼び出す

    Step3→Step4の同一会話を実現するために使用。
    応答を会話履歴に追加して返す。

    Returns:
        (レスポンステキスト, 更新された会話履歴)
    """
    response_text = call_claude(conversation, system=system, max_tokens=max_tokens)
    updated = conversation + [{"role": "assistant", "content": response_text}]
    return response_text, updated
