"""設定管理 - .env / Streamlit Secrets から各種API設定を読み込む"""

import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの.envを読み込み（ローカル用）
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")


def _get(key: str, default: str = "") -> str:
    """環境変数 → Streamlit Secrets → デフォルト の順で取得"""
    # 1. 環境変数（ローカル .env）
    val = os.getenv(key, "")
    if val:
        return val
    # 2. Streamlit Secrets（クラウド）
    try:
        import streamlit as st
        return str(st.secrets[key])
    except Exception:
        return default


class Config:
    """アプリケーション設定"""

    def __init__(self):
        self.project_root: Path = _project_root
        self.rules_dir: Path = _project_root / "rules"
        self.output_dir: Path = _project_root / "output"
        self.reload()

    def reload(self):
        """APIキーを再読み込みする（Streamlit Secrets対応）"""
        self.anthropic_api_key: str = _get("ANTHROPIC_API_KEY")
        self.claude_model: str = _get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        self.notion_secret: str = _get("NOTION_SECRET")
        self.notion_parent_page_id: str = _get("NOTION_PARENT_PAGE_ID")
        self.miro_access_token: str = _get("MIRO_ACCESS_TOKEN")
        self.miro_board_id: str = _get("MIRO_BOARD_ID")

    def validate(self, require_notion: bool = False, require_miro: bool = False) -> list[str]:
        """設定の妥当性を検証し、不足項目のリストを返す"""
        errors = []
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY が未設定です")
        if require_notion:
            if not self.notion_secret:
                errors.append("NOTION_SECRET が未設定です")
            if not self.notion_parent_page_id:
                errors.append("NOTION_PARENT_PAGE_ID が未設定です")
        if require_miro:
            if not self.miro_access_token:
                errors.append("MIRO_ACCESS_TOKEN が未設定です")
            if not self.miro_board_id:
                errors.append("MIRO_BOARD_ID が未設定です")
        return errors


config = Config()
