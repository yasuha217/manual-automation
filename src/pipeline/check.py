"""Step 3: 適合性チェック - 既存プロンプトをそのまま使用"""

import click
from src.utils.claude_client import call_claude
from src.prompts.loader import load_check_prompt_with_manual


def run_check(manual_md: str, verbose: bool = False) -> str:
    """マニュアルの適合性チェックを実行する

    既存の適合性チェックプロンプトを使用し、
    末尾のプレースホルダーにマニュアル内容を注入して実行。

    Returns:
        適合性チェックレポート（Markdown）
    """
    if verbose:
        click.echo("  [Step 3] 適合性チェック実行中...")

    prompt_with_manual = load_check_prompt_with_manual(manual_md)

    response = call_claude(
        messages=[{"role": "user", "content": prompt_with_manual}],
        system="あなたはNotionドキュメント作成の専門家です。",
        max_tokens=8000,
    )

    if verbose:
        click.echo("  [Step 3] 適合性チェック完了")
    return response
