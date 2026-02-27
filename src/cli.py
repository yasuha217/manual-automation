"""CLI エントリポイント - manual-tool コマンド"""

import click
from pathlib import Path


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="詳細ログを表示")
@click.pass_context
def cli(ctx, verbose):
    """マニュアル自動作成 & Miro業務フロー生成ツール"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--input", "-i", "input_file", required=True, type=click.Path(exists=True), help="議事録ファイル (.txt/.md)")
@click.option("--title", "-t", required=True, help="マニュアルタイトル")
@click.option("--type", "manual_type", type=click.Choice(["business", "operation", "hr"]), default="business", help="マニュアル種別")
@click.option("--no-miro", is_flag=True, help="Miroフロー生成をスキップ")
@click.option("--no-notion", is_flag=True, help="Notion出力をスキップ")
@click.option("--output-dir", "-o", default=None, help="出力ディレクトリ")
@click.pass_context
def create(ctx, input_file, title, manual_type, no_miro, no_notion, output_dir):
    """議事録から新規マニュアルを作成する"""
    from src.config import config
    from src.pipeline.orchestrator import run_create_pipeline

    errors = config.validate(
        require_notion=not no_notion,
        require_miro=not no_miro,
    )
    if errors:
        for e in errors:
            click.echo(f"エラー: {e}", err=True)
        raise SystemExit(1)

    out_dir = Path(output_dir) if output_dir else config.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_create_pipeline(
        input_path=Path(input_file),
        title=title,
        manual_type=manual_type,
        skip_miro=no_miro,
        skip_notion=no_notion,
        output_dir=out_dir,
        verbose=ctx.obj["verbose"],
    )
    click.echo(f"\n完了: {result['output_path']}")
    if result.get("notion_url"):
        click.echo(f"Notion: {result['notion_url']}")
    if result.get("miro_url"):
        click.echo(f"Miro: {result['miro_url']}")


@cli.command()
@click.option("--manual", "-m", required=True, type=click.Path(exists=True), help="既存マニュアルファイル")
@click.option("--input", "-i", "input_file", required=True, type=click.Path(exists=True), help="新しい議事録ファイル")
@click.option("--no-miro", is_flag=True, help="Miroフロー生成をスキップ")
@click.option("--no-notion", is_flag=True, help="Notion出力をスキップ")
@click.option("--notion-page-id", default=None, help="更新するNotionページID")
@click.option("--output-dir", "-o", default=None, help="出力ディレクトリ")
@click.pass_context
def update(ctx, manual, input_file, no_miro, no_notion, notion_page_id, output_dir):
    """既存マニュアルを新しい議事録で更新する"""
    from src.config import config
    from src.pipeline.orchestrator import run_update_pipeline

    errors = config.validate(
        require_notion=not no_notion,
        require_miro=not no_miro,
    )
    if errors:
        for e in errors:
            click.echo(f"エラー: {e}", err=True)
        raise SystemExit(1)

    out_dir = Path(output_dir) if output_dir else config.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_update_pipeline(
        manual_path=Path(manual),
        input_path=Path(input_file),
        skip_miro=no_miro,
        skip_notion=no_notion,
        notion_page_id=notion_page_id,
        output_dir=out_dir,
        verbose=ctx.obj["verbose"],
    )
    click.echo(f"\n完了: {result['output_path']}")


@cli.command()
@click.option("--input", "-i", "input_file", required=True, type=click.Path(exists=True), help="チェックするマニュアルファイル")
@click.option("--output-dir", "-o", default=None, help="レポート出力先")
@click.pass_context
def check(ctx, input_file, output_dir):
    """マニュアルの適合性チェックのみを実行する"""
    from src.config import config
    from src.pipeline.check import run_check

    errors = config.validate()
    if errors:
        for e in errors:
            click.echo(f"エラー: {e}", err=True)
        raise SystemExit(1)

    out_dir = Path(output_dir) if output_dir else config.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manual_md = Path(input_file).read_text(encoding="utf-8")
    report = run_check(manual_md, verbose=ctx.obj["verbose"])

    report_path = out_dir / "check_report.md"
    report_path.write_text(report, encoding="utf-8")
    click.echo(f"チェックレポート: {report_path}")


@cli.command()
@click.option("--input", "-i", "input_file", required=True, type=click.Path(exists=True), help="マニュアルファイル")
@click.pass_context
def miro(ctx, input_file):
    """マニュアルからMiro業務フローを生成する"""
    from src.config import config
    from src.integrations.miro_client import create_flowchart_from_manual

    errors = config.validate(require_miro=True)
    if errors:
        for e in errors:
            click.echo(f"エラー: {e}", err=True)
        raise SystemExit(1)

    manual_md = Path(input_file).read_text(encoding="utf-8")
    board_url = create_flowchart_from_manual(manual_md, verbose=ctx.obj["verbose"])
    click.echo(f"Miroボード: {board_url}")


if __name__ == "__main__":
    cli()
