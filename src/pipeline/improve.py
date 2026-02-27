"""Step 4: 改善提案 - 既存プロンプトをそのまま使用

重要: Step3（適合性チェック）と同一会話で実行する。
改善提案プロンプトは「前のメッセージにあるP1のチェック結果を参照」と指定しているため。
"""

import click
from src.utils.claude_client import call_claude
from src.prompts.loader import (
    load_improve_prompt_with_manual,
    load_creation_guide,
    load_template,
)


def run_improve(
    manual_md: str,
    check_result: str,
    verbose: bool = False,
) -> str:
    """改善提案レポートを生成する

    Step3のチェック結果を「前のメッセージ」として同一会話で実行。

    Args:
        manual_md: マニュアルMarkdown
        check_result: Step3の適合性チェック結果

    Returns:
        改善提案レポート（Markdown）
    """
    if verbose:
        click.echo("  [Step 4] 改善提案を生成中...")

    system = f"""あなたはNotion互換Markdownレンダラーです。以下のルールに厳密に従って、レポート本文のみを返してください。

## 参照資料: マニュアル作成・更新ガイド
{load_creation_guide()}

## 参照資料: マニュアルテンプレート
{load_template()}"""

    improve_prompt = load_improve_prompt_with_manual(manual_md)

    # Step3の結果を「前のメッセージ」として会話を構築
    messages = [
        {"role": "user", "content": "以下がマニュアル適合性チェック結果です。"},
        {"role": "assistant", "content": check_result},
        {"role": "user", "content": improve_prompt},
    ]

    response = call_claude(
        messages=messages,
        system=system,
        max_tokens=12000,
    )

    if verbose:
        click.echo("  [Step 4] 改善提案完了")
    return response
