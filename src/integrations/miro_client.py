"""Miro連携 - 業務フローチャートの作成"""

import json
import re
import time
import click
import requests

from src.config import config
from src.utils.claude_client import call_claude
from src.utils.markdown_parser import extract_section
from src.prompts.custom import get_flowchart_extract_prompt
from src.integrations.miro_layout import calculate_layout


MIRO_API_BASE = "https://api.miro.com/v2"


def _headers() -> dict:
    """Miro API用ヘッダーを返す"""
    return {
        "Authorization": f"Bearer {config.miro_access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _create_shape(board_id: str, data: dict) -> str:
    """Miroボードに図形を作成してIDを返す"""
    url = f"{MIRO_API_BASE}/boards/{board_id}/shapes"
    resp = requests.post(url, headers=_headers(), json=data)
    resp.raise_for_status()
    time.sleep(0.1)  # レート制限対策
    return resp.json()["id"]


def _create_connector(board_id: str, data: dict) -> str:
    """Miroボードにコネクタを作成してIDを返す"""
    url = f"{MIRO_API_BASE}/boards/{board_id}/connectors"
    resp = requests.post(url, headers=_headers(), json=data)
    resp.raise_for_status()
    time.sleep(0.1)
    return resp.json()["id"]


def _extract_flowchart_json(manual_md: str, verbose: bool = False) -> dict:
    """マニュアルから業務フローのJSON構造を抽出する"""
    # セクション【3】全体像を抽出
    overview = extract_section(manual_md, "全体像")
    if not overview:
        # フォールバック: Mermaid図があればそれを使用
        overview = extract_section(manual_md, "フロー")
    if not overview:
        overview = manual_md  # 見つからなければ全体から抽出

    if verbose:
        click.echo("  [Miro] フローチャート構造を抽出中...")

    prompt = get_flowchart_extract_prompt(overview)
    response = call_claude(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
    )

    # JSONブロックを抽出
    json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    # JSONブロックがなければレスポンス全体をパース
    return json.loads(response)


def _build_shape_content(label: str, role: str, deadline: str) -> str:
    """図形内のHTMLコンテンツを構築する"""
    parts = [f"<p><strong>{label}</strong></p>"]
    if role:
        parts.append(f"<p>{role}</p>")
    if deadline:
        parts.append(f"<p><em>{deadline}</em></p>")
    return "".join(parts)


def create_flowchart_from_json(flowchart_json: str) -> str:
    """抽出済みのJSON文字列からMiroにフローチャートを描画する

    Args:
        flowchart_json: フローチャート構造のJSON文字列

    Returns:
        MiroボードのURL
    """
    flowchart_data = json.loads(flowchart_json)
    return _draw_flowchart(flowchart_data)


def create_flowchart_from_manual(manual_md: str, verbose: bool = False) -> str:
    """マニュアルからMiroにフローチャートを作成する

    Args:
        manual_md: マニュアルのMarkdown全文
        verbose: 詳細ログ

    Returns:
        MiroボードのURL
    """
    # フローチャート構造を抽出
    flowchart_data = _extract_flowchart_json(manual_md, verbose)
    return _draw_flowchart(flowchart_data, verbose)


def _draw_flowchart(flowchart_data: dict, verbose: bool = False) -> str:
    """フローチャートデータからMiroに描画する（内部共通処理）"""
    board_id = config.miro_board_id

    if verbose:
        title = flowchart_data.get("title", "業務フロー")
        phase_count = len(flowchart_data.get("phases", []))
        click.echo(f"  [Miro] フロー: {title}（{phase_count}フェーズ）")

    # レイアウト計算
    headers, positions = calculate_layout(flowchart_data)

    # 図形ID → Miro IDのマッピング
    miro_ids: dict[str, str] = {}

    # タイトル作成
    title = flowchart_data.get("title", "業務フロー")
    _create_shape(board_id, {
        "data": {
            "content": f"<p><strong>{title}</strong></p>",
            "shape": "rectangle",
        },
        "style": {
            "fillColor": "#1A1A2E",
            "fontFamily": "arial",
            "fontSize": "24",
            "textAlign": "center",
            "textAlignVertical": "middle",
            "color": "#FFFFFF",
        },
        "position": {"x": headers[0].x if headers else 550, "y": 100},
        "geometry": {"width": 600, "height": 60},
    })

    if verbose:
        click.echo("  [Miro] フェーズヘッダーを作成中...")

    # フェーズヘッダー作成
    for header in headers:
        _create_shape(board_id, {
            "data": {
                "content": f"<p><strong>{header.name}</strong></p>",
                "shape": "rectangle",
            },
            "style": {
                "fillColor": "#F3E5F5",
                "fontFamily": "arial",
                "fontSize": "18",
                "textAlign": "center",
                "textAlignVertical": "middle",
            },
            "position": {"x": header.x, "y": header.y},
            "geometry": {"width": header.width, "height": header.height},
        })

    if verbose:
        click.echo(f"  [Miro] {len(positions)}個の図形を作成中...")

    # 各ステップの図形を作成
    for pos in positions:
        content = _build_shape_content(pos.label, pos.role, pos.deadline)
        shape_id = _create_shape(board_id, {
            "data": {
                "content": content,
                "shape": pos.shape_type,
            },
            "style": {
                "fillColor": pos.fill_color,
                "fontFamily": "arial",
                "fontSize": "14",
                "textAlign": "center",
                "textAlignVertical": "middle",
            },
            "position": {"x": pos.x, "y": pos.y},
            "geometry": {"width": pos.width, "height": pos.height},
        })
        miro_ids[pos.step_id] = shape_id

    if verbose:
        click.echo("  [Miro] コネクタを作成中...")

    # コネクタ作成
    for phase in flowchart_data.get("phases", []):
        for conn in phase.get("connections", []):
            from_id = miro_ids.get(conn["from"])
            to_id = miro_ids.get(conn["to"])
            if not from_id or not to_id:
                continue

            connector_data: dict = {
                "startItem": {"id": from_id, "snapTo": "auto"},
                "endItem": {"id": to_id, "snapTo": "auto"},
                "shape": "elbowed",
                "style": {
                    "strokeColor": "#424242",
                    "strokeWidth": "2.0",
                    "endStrokeCap": "stealth",
                },
            }

            label = conn.get("label", "")
            if label:
                connector_data["captions"] = [{"content": label}]

            _create_connector(board_id, connector_data)

    board_url = f"https://miro.com/app/board/{board_id}/"
    if verbose:
        click.echo(f"  [Miro] フローチャート作成完了")
    return board_url
