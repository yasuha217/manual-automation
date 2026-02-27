"""Step 2: 構造化データからマニュアル草稿を生成する"""

import click
from src.utils.claude_client import call_claude
from src.prompts.custom import get_draft_prompt, get_update_draft_prompt
from src.prompts.loader import load_creation_guide, load_template


def run_draft(structured_data: str, verbose: bool = False) -> str:
    """構造化データからマニュアル草稿を生成する（新規作成モード）"""
    if verbose:
        click.echo("  [Step 2] マニュアル草稿を生成中...")

    system = f"""あなたはNotion互換Markdownでマニュアルを作成する専門家です。
以下のガイドラインとテンプレートに厳密に従ってください。

## マニュアル作成・更新ガイド
{load_creation_guide()}

## マニュアルテンプレート
{load_template()}"""

    prompt = get_draft_prompt(structured_data)
    response = call_claude(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=16000,
    )

    if verbose:
        click.echo("  [Step 2] 草稿生成完了")
    return response


def run_update_draft(existing_manual: str, updates_json: str, verbose: bool = False) -> str:
    """既存マニュアルに更新情報を反映する（更新モード）"""
    if verbose:
        click.echo("  [Step 2] マニュアルを更新中...")

    system = f"""あなたはNotion互換Markdownでマニュアルを更新する専門家です。

## マニュアル作成・更新ガイド
{load_creation_guide()}"""

    prompt = get_update_draft_prompt(existing_manual, updates_json)
    response = call_claude(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=16000,
    )

    if verbose:
        click.echo("  [Step 2] 更新完了")
    return response
