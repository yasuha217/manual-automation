"""Notion連携 - データベースへのページ作成・更新"""

import requests
from src.config import config

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.notion_secret}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_notion_page(title: str, markdown_content: str) -> str:
    """Notionデータベースにマニュアルページを作成する

    Args:
        title: マニュアル名（DBのtitleプロパティ）
        markdown_content: マニュアルのMarkdown内容

    Returns:
        作成されたページのURL
    """
    resp = requests.post(
        f"{API_BASE}/pages",
        headers=_headers(),
        json={
            "parent": {"database_id": config.notion_parent_page_id},
            "properties": {
                "マニュアル名": {
                    "title": [{"text": {"content": title}}]
                },
            },
            "markdown": markdown_content,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["url"]


def update_notion_page(page_id: str, markdown_content: str) -> None:
    """既存のNotionページを更新する

    既存ブロックを削除してからmarkdownで再作成する。

    Args:
        page_id: 更新するNotionページのID
        markdown_content: 新しいマニュアルのMarkdown内容
    """
    # 既存ブロックを取得して削除
    resp = requests.get(
        f"{API_BASE}/blocks/{page_id}/children?page_size=100",
        headers=_headers(),
    )
    resp.raise_for_status()
    for block in resp.json().get("results", []):
        requests.delete(
            f"{API_BASE}/blocks/{block['id']}",
            headers=_headers(),
        )

    # markdownで新しいコンテンツを追加
    resp = requests.patch(
        f"{API_BASE}/blocks/{page_id}/children",
        headers=_headers(),
        json={"markdown": markdown_content},
    )
    resp.raise_for_status()
