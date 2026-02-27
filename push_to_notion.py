"""Notionにマニュアルページを作成するスタンドアロンスクリプト

Usage:
    python push_to_notion.py <markdown_file> <title>
    python push_to_notion.py output/final_manual.md "月次セミナー運営マニュアル"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import config


def main():
    if len(sys.argv) < 3:
        print("Usage: python push_to_notion.py <markdown_file> <title>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    title = sys.argv[2]

    if not file_path.exists():
        print(f"エラー: ファイルが見つかりません: {file_path}")
        sys.exit(1)

    errors = config.validate(require_notion=True)
    if errors:
        print("エラー: .envファイルの設定が不足しています:")
        for e in errors:
            print(f"  - {e}")
        print("\n.envファイルに以下を設定してください:")
        print("  NOTION_SECRET=ntn_...")
        print("  NOTION_PARENT_PAGE_ID=your_page_id")
        sys.exit(1)

    markdown_content = file_path.read_text(encoding="utf-8")

    from src.integrations.notion_client import create_notion_page

    print(f"Notionページ作成中: {title}")
    url = create_notion_page(title, markdown_content)
    print(f"完了: {url}")


if __name__ == "__main__":
    main()
