"""Miroにフローチャートを描画するスタンドアロンスクリプト

Usage:
    python push_to_miro.py <manual_or_json_file>
    python push_to_miro.py output/final_manual.md
    python push_to_miro.py output/miro_flowchart.json
"""

import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config


def main():
    if len(sys.argv) < 2:
        print("Usage: python push_to_miro.py <file_path>")
        print("  file_path: マニュアル(.md)またはフローチャートJSON(.json)")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"エラー: ファイルが見つかりません: {file_path}")
        sys.exit(1)

    # 設定チェック
    errors = config.validate(require_miro=True)
    if errors:
        print("エラー: .envファイルの設定が不足しています:")
        for e in errors:
            print(f"  - {e}")
        print("\n.envファイルに以下を設定してください:")
        print("  MIRO_ACCESS_TOKEN=your_token")
        print("  MIRO_BOARD_ID=your_board_id")
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    if file_path.suffix == ".json":
        # JSONファイルの場合は直接Miro APIに送信
        from src.integrations.miro_client import create_flowchart_from_manual
        # JSONをマニュアル風に変換してフロー抽出をスキップ
        flowchart_data = json.loads(content)
        from src.integrations.miro_layout import calculate_layout
        from src.integrations.miro_client import (
            _headers, _create_shape, _create_connector, _build_shape_content
        )

        board_id = config.miro_board_id
        headers_list, positions = calculate_layout(flowchart_data)
        miro_ids = {}

        # タイトル
        title = flowchart_data.get("title", "業務フロー")
        print(f"フローチャート作成中: {title}")
        _create_shape(board_id, {
            "data": {"content": f"<p><strong>{title}</strong></p>", "shape": "rectangle"},
            "style": {"fillColor": "#1A1A2E", "fontSize": "24", "textAlign": "center", "color": "#FFFFFF"},
            "position": {"x": headers_list[0].x if headers_list else 550, "y": 100},
            "geometry": {"width": 600, "height": 60},
        })

        # フェーズヘッダー
        for header in headers_list:
            _create_shape(board_id, {
                "data": {"content": f"<p><strong>{header.name}</strong></p>", "shape": "rectangle"},
                "style": {"fillColor": "#F3E5F5", "fontSize": "18", "textAlign": "center"},
                "position": {"x": header.x, "y": header.y},
                "geometry": {"width": header.width, "height": header.height},
            })

        # 図形
        for pos in positions:
            content_html = _build_shape_content(pos.label, pos.role, pos.deadline)
            shape_id = _create_shape(board_id, {
                "data": {"content": content_html, "shape": pos.shape_type},
                "style": {"fillColor": pos.fill_color, "fontSize": "14", "textAlign": "center"},
                "position": {"x": pos.x, "y": pos.y},
                "geometry": {"width": pos.width, "height": pos.height},
            })
            miro_ids[pos.step_id] = shape_id

        # コネクタ
        for phase in flowchart_data.get("phases", []):
            for conn in phase.get("connections", []):
                from_id = miro_ids.get(conn["from"])
                to_id = miro_ids.get(conn["to"])
                if not from_id or not to_id:
                    continue
                connector_data = {
                    "startItem": {"id": from_id, "snapTo": "auto"},
                    "endItem": {"id": to_id, "snapTo": "auto"},
                    "shape": "elbowed",
                    "style": {"strokeColor": "#424242", "strokeWidth": "2.0", "endStrokeCap": "stealth"},
                }
                label = conn.get("label", "")
                if label:
                    connector_data["captions"] = [{"content": label}]
                _create_connector(board_id, connector_data)

        print(f"完了: https://miro.com/app/board/{board_id}/")

    else:
        # Markdownの場合はフロー抽出から実行
        from src.integrations.miro_client import create_flowchart_from_manual
        url = create_flowchart_from_manual(content, verbose=True)
        print(f"完了: {url}")


if __name__ == "__main__":
    main()
