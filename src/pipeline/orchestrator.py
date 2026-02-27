"""パイプラインオーケストレーター - 全ステップを統合実行"""

from pathlib import Path
from datetime import datetime
import click

from src.pipeline.analyze import run_analyze, run_merge_analyze
from src.pipeline.draft import run_draft, run_update_draft
from src.pipeline.check import run_check
from src.pipeline.improve import run_improve
from src.pipeline.apply import run_apply


def _save_intermediate(output_dir: Path, filename: str, content: str) -> Path:
    """中間ファイルを保存する"""
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def run_create_pipeline(
    input_path: Path,
    title: str,
    manual_type: str = "business",
    skip_miro: bool = False,
    skip_notion: bool = False,
    output_dir: Path = Path("output"),
    verbose: bool = False,
) -> dict:
    """新規マニュアル作成パイプライン

    Step1(抽出) → Step2(生成) → 出力
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    click.echo(f"新規マニュアル作成を開始: {title}")

    # 入力読み込み
    minutes_text = input_path.read_text(encoding="utf-8")

    # Step 1: 抽出
    structured_data = run_analyze(minutes_text, manual_type, verbose)
    _save_intermediate(output_dir, f"{timestamp}_step1_analysis.json", structured_data)

    # Step 2: マニュアル生成（一発完成版）
    final_manual = run_draft(structured_data, verbose)

    # 最終出力保存
    final_path = output_dir / f"{timestamp}_{title}.md"
    final_path.write_text(final_manual, encoding="utf-8")
    if verbose:
        click.echo(f"  最終マニュアルを保存: {final_path}")

    result = {"output_path": str(final_path), "final_manual": final_manual}

    # Notion出力
    if not skip_notion:
        try:
            from src.integrations.notion_client import create_notion_page
            if verbose:
                click.echo("  [Notion] ページを作成中...")
            notion_url = create_notion_page(title, final_manual)
            result["notion_url"] = notion_url
            if verbose:
                click.echo(f"  [Notion] 作成完了: {notion_url}")
        except Exception as e:
            click.echo(f"  警告: Notion出力に失敗しました: {e}", err=True)

    # Miro出力
    if not skip_miro:
        try:
            from src.integrations.miro_client import create_flowchart_from_manual
            if verbose:
                click.echo("  [Miro] フローチャートを作成中...")
            miro_url = create_flowchart_from_manual(final_manual, verbose)
            result["miro_url"] = miro_url
            if verbose:
                click.echo(f"  [Miro] 作成完了: {miro_url}")
        except Exception as e:
            click.echo(f"  警告: Miro出力に失敗しました: {e}", err=True)

    return result


def run_update_pipeline(
    manual_path: Path,
    input_path: Path | None = None,
    skip_miro: bool = False,
    skip_notion: bool = False,
    notion_page_id: str | None = None,
    output_dir: Path = Path("output"),
    verbose: bool = False,
) -> dict:
    """既存マニュアル更新パイプライン

    議事録あり: Step1(差分分析) → Step2(更新) → チェック → 改善 → 適用 → 出力
    議事録なし: チェック → 改善 → 適用 → 出力
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    click.echo("マニュアル更新を開始")

    existing_manual = manual_path.read_text(encoding="utf-8")

    if input_path:
        # パターンA: 議事録あり
        minutes_text = input_path.read_text(encoding="utf-8")

        # 差分分析
        updates_json = run_merge_analyze(existing_manual, minutes_text, verbose)
        _save_intermediate(output_dir, f"{timestamp}_step1_updates.json", updates_json)

        # 更新草稿
        draft = run_update_draft(existing_manual, updates_json, verbose)
        _save_intermediate(output_dir, f"{timestamp}_step2_draft.md", draft)
    else:
        # パターンB: 議事録なし
        draft = existing_manual

    # チェック → 改善 → 適用（共通）
    check_report = run_check(draft, verbose)
    _save_intermediate(output_dir, f"{timestamp}_check.md", check_report)

    improve_report = run_improve(draft, check_report, verbose)
    _save_intermediate(output_dir, f"{timestamp}_improve.md", improve_report)

    final_manual = run_apply(draft, improve_report, verbose)

    # 最終出力保存
    title = manual_path.stem
    final_path = output_dir / f"{timestamp}_{title}_updated.md"
    final_path.write_text(final_manual, encoding="utf-8")
    if verbose:
        click.echo(f"  更新マニュアルを保存: {final_path}")

    result = {"output_path": str(final_path), "final_manual": final_manual}

    # Notion出力
    if not skip_notion:
        try:
            from src.integrations.notion_client import create_notion_page, update_notion_page
            if verbose:
                click.echo("  [Notion] ページを更新中...")
            if notion_page_id:
                update_notion_page(notion_page_id, final_manual)
                result["notion_url"] = f"https://notion.so/{notion_page_id}"
            else:
                notion_url = create_notion_page(f"{title}（更新版）", final_manual)
                result["notion_url"] = notion_url
            if verbose:
                click.echo("  [Notion] 完了")
        except Exception as e:
            click.echo(f"  警告: Notion出力に失敗しました: {e}", err=True)

    # Miro出力
    if not skip_miro:
        try:
            from src.integrations.miro_client import create_flowchart_from_manual
            if verbose:
                click.echo("  [Miro] フローチャートを作成中...")
            miro_url = create_flowchart_from_manual(final_manual, verbose)
            result["miro_url"] = miro_url
        except Exception as e:
            click.echo(f"  警告: Miro出力に失敗しました: {e}", err=True)

    return result
