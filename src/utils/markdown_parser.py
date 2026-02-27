"""Markdownパーサー - セクション抽出ユーティリティ"""

import re


def extract_section(markdown: str, header_pattern: str) -> str:
    """指定パターンを含む見出しのセクションを抽出する

    Args:
        markdown: Markdownテキスト全体
        header_pattern: 見出しに含まれるパターン（例: "全体像"）

    Returns:
        該当セクションの内容（見出し含む）。見つからなければ空文字。
    """
    lines = markdown.split("\n")
    in_section = False
    section_lines: list[str] = []
    section_level: int | None = None

    for line in lines:
        header_match = re.match(r"^(#{1,6})\s+", line)
        if header_match and header_pattern in line:
            in_section = True
            section_level = len(header_match.group(1))
            section_lines.append(line)
            continue
        if in_section:
            if header_match and len(header_match.group(1)) <= section_level:
                break
            section_lines.append(line)

    return "\n".join(section_lines)


def extract_all_sections(markdown: str) -> dict[str, str]:
    """Markdownからすべてのトップレベルセクションを抽出する

    Returns:
        {見出しテキスト: セクション内容} の辞書
    """
    lines = markdown.split("\n")
    sections: dict[str, str] = {}
    current_header: str | None = None
    current_lines: list[str] = []

    for line in lines:
        header_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if header_match:
            if current_header is not None:
                sections[current_header] = "\n".join(current_lines)
            current_header = header_match.group(2).strip()
            current_lines = [line]
        elif current_header is not None:
            current_lines.append(line)

    if current_header is not None:
        sections[current_header] = "\n".join(current_lines)

    return sections
