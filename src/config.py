"""設定管理 - .env / Streamlit Secrets から各種API設定を読み込む"""

import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの.envを読み込み（ローカル用）
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")


def _get_secret(key: str, default: str = "") -> str:
    """環境変数 → Streamlit Secrets → デフォルト の順で取得"""
    # 1. 環境変数（.env / OS）
    val = os.getenv(key, "")
    if val:
        return val
    # 2. Streamlit Secrets（クラウドデプロイ時）
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


class Config:
    """アプリケーション設定"""

    # Claude API
    anthropic_api_key: str = _get_secret("ANTHROPIC_API_KEY")
    claude_model: str = _get_secret("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # Notion
    notion_secret: str = _get_secret("NOTION_SECRET")
    notion_parent_page_id: str = _get_secret("NOTION_PARENT_PAGE_ID")

    # Miro
    miro_access_token: str = _get_secret("MIRO_ACCESS_TOKEN")
    miro_board_id: str = _get_secret("MIRO_BOARD_ID")

    # パス
    project_root: Path = _project_root
    rules_dir: Path = _project_root / "rules"
    output_dir: Path = _project_root / "output"

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
