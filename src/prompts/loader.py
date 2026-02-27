"""既存プロンプト・ルールファイルの読み込み"""

from pathlib import Path
from src.config import config


def _read_file(path: Path) -> str:
    """ファイルを読み込みテキストを返す"""
    return path.read_text(encoding="utf-8")


def load_creation_guide() -> str:
    """マニュアル作成・更新ガイドを読み込む"""
    return _read_file(config.rules_dir / "creation_guide.md")


def load_template() -> str:
    """企画用マニュアルテンプレートを読み込む"""
    return _read_file(config.rules_dir / "template.md")


def load_check_prompt() -> str:
    """適合性チェックプロンプトを読み込む"""
    return _read_file(config.rules_dir / "check_prompt.md")


def load_improve_prompt() -> str:
    """マニュアル改善提案ジェネレータープロンプトを読み込む"""
    return _read_file(config.rules_dir / "improve_prompt.md")


def load_check_prompt_with_manual(manual_md: str) -> str:
    """適合性チェックプロンプトにマニュアル内容を注入して返す"""
    prompt = load_check_prompt()
    return prompt.replace(
        "（ここにMarkdown形式でダウンロードした内容をコピペ）",
        manual_md,
    )


def load_improve_prompt_with_manual(manual_md: str) -> str:
    """改善提案プロンプトにマニュアル内容を注入して返す"""
    prompt = load_improve_prompt()
    return prompt.replace(
        "（ここにMarkdown形式でダウンロードした内容をコピペ）",
        manual_md,
    )
