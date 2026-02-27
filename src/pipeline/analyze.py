"""Step 1: 議事録から業務手順を構造化抽出する"""

import json
import re
import click
from src.utils.claude_client import call_claude
from src.prompts.custom import get_analyze_prompt, get_merge_prompt
from src.prompts.loader import load_creation_guide, load_template


def run_analyze(minutes_text: str, manual_type: str = "business", verbose: bool = False) -> str:
    """議事録から構造化データをJSON文字列として抽出する（新規作成モード）"""
    if verbose:
        click.echo("  [Step 1] 議事録から業務手順を抽出中...")

    system = f"""あなたは業務分析の専門家です。以下のマニュアル作成ガイドを参考に、議事録から情報を抽出してください。

## マニュアル作成・更新ガイド
{load_creation_guide()}

## マニュアルテンプレート
{load_template()}"""

    prompt = get_analyze_prompt(minutes_text, manual_type)
    response = call_claude(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=8000,
    )

    # JSONブロックを抽出
    json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = response

    # JSONとして妥当性チェック
    try:
        json.loads(json_str)
    except json.JSONDecodeError:
        if verbose:
            click.echo("  警告: JSON解析に失敗。レスポンスをそのまま使用します。")
        json_str = response

    if verbose:
        click.echo("  [Step 1] 抽出完了")
    return json_str


def run_merge_analyze(existing_manual: str, minutes_text: str, verbose: bool = False) -> str:
    """既存マニュアルと新議事録から更新箇所を特定する（更新モード）"""
    if verbose:
        click.echo("  [Step 1] 既存マニュアルとの差分を分析中...")

    system = f"""あなたは業務分析の専門家です。

## マニュアル作成・更新ガイド
{load_creation_guide()}"""

    prompt = get_merge_prompt(existing_manual, minutes_text)
    response = call_claude(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=8000,
    )

    json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = response

    if verbose:
        click.echo("  [Step 1] 差分分析完了")
    return json_str
