"""Miroフローチャートのレイアウト計算"""

from dataclasses import dataclass


# レイアウト定数
X_START = 200
Y_START = 200
X_SPACING = 350
Y_SPACING = 150
PHASE_GAP = 300
MAX_PER_ROW = 4
PHASE_HEADER_WIDTH = 900
PHASE_HEADER_HEIGHT = 50

# 図形サイズ
SHAPE_SIZES = {
    "start": (180, 60),
    "end": (180, 60),
    "process": (250, 80),
    "decision": (200, 120),
}

# 色設定
SHAPE_COLORS = {
    "start": "#E8F5E9",      # 薄緑
    "end": "#E8F5E9",        # 薄緑
    "process": "#E3F2FD",    # 薄青
    "decision": "#FFF3E0",   # 薄橙
}

# Miro図形タイプ
SHAPE_TYPES = {
    "start": "round_rectangle",
    "end": "round_rectangle",
    "process": "rectangle",
    "decision": "rhombus",
}


@dataclass
class ShapePosition:
    """図形の位置情報"""
    step_id: str
    x: float
    y: float
    width: float
    height: float
    shape_type: str
    fill_color: str
    label: str
    role: str
    deadline: str


@dataclass
class PhaseHeader:
    """フェーズヘッダーの位置情報"""
    name: str
    x: float
    y: float
    width: float
    height: float


def calculate_layout(flowchart_data: dict) -> tuple[list[PhaseHeader], list[ShapePosition]]:
    """フローチャートデータからレイアウトを計算する

    Args:
        flowchart_data: JSONパースされたフローチャート構造

    Returns:
        (フェーズヘッダーリスト, 図形位置リスト)
    """
    headers: list[PhaseHeader] = []
    positions: list[ShapePosition] = []
    current_y = Y_START

    for phase in flowchart_data.get("phases", []):
        # フェーズヘッダー
        header = PhaseHeader(
            name=phase["name"],
            x=X_START + PHASE_HEADER_WIDTH / 2,
            y=current_y,
            width=PHASE_HEADER_WIDTH,
            height=PHASE_HEADER_HEIGHT,
        )
        headers.append(header)
        current_y += PHASE_HEADER_HEIGHT + 50

        # 各ステップの配置
        steps = phase.get("steps", [])
        col = 0
        row_start_y = current_y

        for step in steps:
            step_type = step.get("type", "process")
            width, height = SHAPE_SIZES.get(step_type, (250, 80))

            x = X_START + col * X_SPACING + width / 2
            y = current_y + height / 2

            pos = ShapePosition(
                step_id=step["id"],
                x=x,
                y=y,
                width=width,
                height=height,
                shape_type=SHAPE_TYPES.get(step_type, "rectangle"),
                fill_color=SHAPE_COLORS.get(step_type, "#E3F2FD"),
                label=step.get("label", ""),
                role=step.get("role", ""),
                deadline=step.get("deadline", ""),
            )
            positions.append(pos)

            col += 1
            if col >= MAX_PER_ROW:
                col = 0
                current_y += Y_SPACING

        # 最後の行の高さを反映
        if col > 0:
            current_y += Y_SPACING

        # フェーズ間のギャップ
        current_y += PHASE_GAP

    return headers, positions
