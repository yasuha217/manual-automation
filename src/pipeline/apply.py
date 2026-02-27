"""Step 5: 改善提案をマニュアル草稿に適用する"""

import click
from src.utils.claude_client import call_claude
from src.prompts.custom import get_apply_prompt
from src.prompts.loader import load_creation_guide


def run_apply(draft: str, improvement_report: str, verbose: bool = False) -> str:
    """改善提案をすべて草稿に適用して最終版を返す

    Args:
        draft: マニュアル草稿（Step2の出力）
        improvement_report: 改善提案レポート（Step4の出力）

    Returns:
        改善適用済みの最終マニュアル（Markdown）
    """
    if verbose:
        click.echo("  [Step 5] 改善提案を適用中...")

    system = f"""あなたはNotion互換Markdownでマニュアルを完成させる専門家です。

## マニュアル作成・更新ガイド
{load_creation_guide()}"""

    prompt = get_apply_prompt(draft, improvement_report)
    response = call_claude(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=16000,
    )

    if verbose:
        click.echo("  [Step 5] 改善適用完了")
    return response
