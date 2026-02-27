"""マニュアル自動作成 Streamlit アプリ"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

import streamlit as st

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config

# --- ページ設定 ---
st.set_page_config(
    page_title="マニュアル自動作成ツール",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- カスタムCSS ---
st.markdown("""
<style>
    .stApp { max-width: 1200px; margin: 0 auto; }
    .step-done { color: #22c55e; }
    .step-running { color: #3b82f6; }
    .step-pending { color: #9ca3af; }
    .result-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
    }
    div[data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# --- セッション初期化 ---
if "step_status" not in st.session_state:
    st.session_state.step_status = {}
if "results" not in st.session_state:
    st.session_state.results = {}
if "running" not in st.session_state:
    st.session_state.running = False


def update_step(step_name: str, status: str):
    """ステップ状態を更新"""
    st.session_state.step_status[step_name] = status


def get_step_icon(step_name: str) -> str:
    """ステップのアイコンを返す"""
    status = st.session_state.step_status.get(step_name, "pending")
    if status == "done":
        return "✅"
    elif status == "running":
        return "🔄"
    elif status == "error":
        return "❌"
    return "⬜"


# --- サイドバー ---
with st.sidebar:
    st.title("⚙️ 出力設定")

    enable_notion = st.toggle("📝 Notionに出力", value=False)
    enable_miro = st.toggle("🗺️ Miroにフロー描画", value=False)

    if enable_notion or enable_miro:
        st.divider()
        st.caption("接続状態")
        if enable_notion:
            if config.notion_secret and config.notion_parent_page_id:
                st.success("Notion: 接続済み")
            else:
                st.error("Notion: 未設定（Secretsを確認）")
        if enable_miro:
            if config.miro_access_token and config.miro_board_id:
                st.success("Miro: 接続済み")
            else:
                st.error("Miro: 未設定（Secretsを確認）")

    # デバッグ（問題解決後に削除）
    with st.expander("🔍 デバッグ情報"):
        st.text(f"API Key: {'あり' if config.anthropic_api_key else 'なし'}")
        st.text(f"Notion Secret: {'あり' if config.notion_secret else 'なし'}")
        st.text(f"Notion Page ID: {'あり' if config.notion_parent_page_id else 'なし'}")
        st.text(f"Miro Token: {'あり' if config.miro_access_token else 'なし'}")
        st.text(f"Miro Board: {'あり' if config.miro_board_id else 'なし'}")
        try:
            secrets_keys = list(st.secrets.keys())
            st.text(f"Secrets keys: {secrets_keys}")
        except Exception as e:
            st.text(f"Secrets error: {e}")


# --- メインUI ---
st.title("📋 マニュアル自動作成ツール")
st.caption("議事録・MTG文字起こしから、ルール準拠のマニュアルを自動生成します")

# モード選択
mode = st.segmented_control(
    "モード",
    options=["新規作成", "既存修正", "チェックのみ"],
    default="新規作成",
)

st.divider()

# --- 入力エリア ---
col_input, col_options = st.columns([3, 1])

with col_input:
    if mode == "新規作成":
        st.subheader("📎 議事録をアップロード")
        uploaded = st.file_uploader(
            "テキストファイル (.txt / .md)",
            type=["txt", "md"],
            key="input_file",
        )
        title = st.text_input("マニュアルタイトル", placeholder="例: 月次セミナー運営マニュアル")

        st.markdown("**または直接テキストを貼り付け:**")
        pasted = st.text_area(
            "議事録テキスト",
            height=200,
            placeholder="ここに議事録や文字起こしの内容を貼り付け...",
            label_visibility="collapsed",
        )

    elif mode == "既存修正":
        st.subheader("📎 ファイルをアップロード")
        existing_file = st.file_uploader(
            "既存マニュアル (.md) *必須",
            type=["txt", "md"],
            key="existing_file",
        )
        new_minutes = st.file_uploader(
            "新しい議事録 (.txt / .md) *任意",
            type=["txt", "md"],
            key="new_minutes",
            help="新しい情報がある場合のみアップロードしてください。なければ既存マニュアルのルール適合チェック→改善を行います。",
        )

    else:  # チェックのみ
        st.subheader("📎 チェック対象マニュアル")
        check_file = st.file_uploader(
            "マニュアルファイル (.md)",
            type=["txt", "md"],
            key="check_file",
        )

with col_options:
    if mode == "新規作成":
        st.subheader("オプション")
        manual_type = st.radio(
            "種別",
            ["業務マニュアル", "操作マニュアル", "人材育成マニュアル"],
        )
        type_map = {"業務マニュアル": "business", "操作マニュアル": "operation", "人材育成マニュアル": "hr"}

st.divider()


# --- 実行ボタン ---
def validate_inputs() -> str | None:
    """入力バリデーション。エラーメッセージを返す。"""
    if not config.anthropic_api_key:
        return "サイドバーでAnthropic APIキーを設定してください"
    if mode == "新規作成":
        if not uploaded and not pasted:
            return "議事録ファイルをアップロードするか、テキストを貼り付けてください"
        if not title and not pasted:
            return "マニュアルタイトルを入力してください"
    elif mode == "既存修正":
        if not existing_file:
            return "既存マニュアルをアップロードしてください"
    else:
        if not check_file:
            return "チェック対象のマニュアルファイルをアップロードしてください"
    return None


# ============================================================
# パイプライン関数
# ============================================================

def _run_miro_extract(final: str, ts: str, output_dir: Path):
    """マニュアルからMiroフローデータを抽出"""
    update_step("miro_extract", "running")
    progress_placeholder.markdown(render_progress())
    from src.utils.markdown_parser import extract_section
    from src.prompts.custom import get_flowchart_extract_prompt
    from src.utils.claude_client import call_claude

    overview = extract_section(final, "全体像")
    if overview:
        prompt = get_flowchart_extract_prompt(overview)
        fc_response = call_claude(messages=[{"role": "user", "content": prompt}], max_tokens=4000)
        json_match = re.search(r"```json\s*(.*?)\s*```", fc_response, re.DOTALL)
        fc_json = json_match.group(1) if json_match else fc_response
        fc_path = output_dir / f"{ts}_miro_flowchart.json"
        fc_path.write_text(fc_json, encoding="utf-8")
        st.session_state.results["flowchart_json"] = fc_json
        st.session_state.results["flowchart_path"] = str(fc_path)
    update_step("miro_extract", "done")
    progress_placeholder.markdown(render_progress())


def _run_notion_push(manual_title: str, final: str):
    """Notionにページを作成"""
    update_step("notion", "running")
    progress_placeholder.markdown(render_progress())
    try:
        from src.integrations.notion_client import create_notion_page
        url = create_notion_page(manual_title, final)
        st.session_state.results["notion_url"] = url
        update_step("notion", "done")
    except Exception as e:
        st.session_state.results["notion_error"] = str(e)
        update_step("notion", "error")
    progress_placeholder.markdown(render_progress())


def _run_miro_push(fc_json: str):
    """Miroにフローチャートを描画"""
    update_step("miro_push", "running")
    progress_placeholder.markdown(render_progress())
    try:
        from src.integrations.miro_client import create_flowchart_from_json
        miro_url = create_flowchart_from_json(fc_json)
        st.session_state.results["miro_url"] = miro_url
        update_step("miro_push", "done")
    except Exception as e:
        st.session_state.results["miro_error"] = str(e)
        update_step("miro_push", "error")
    progress_placeholder.markdown(render_progress())


def run_create_pipeline(minutes_text: str, manual_title: str, m_type: str):
    """新規作成パイプライン: ①構造化抽出 → ②マニュアル生成 → 出力"""
    from src.pipeline.analyze import run_analyze
    from src.pipeline.draft import run_draft

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: 構造化抽出
    update_step("step1", "running")
    progress_placeholder.markdown(render_progress())
    structured = run_analyze(minutes_text, m_type, verbose=False)
    (output_dir / f"{ts}_step1_analysis.json").write_text(structured, encoding="utf-8")
    st.session_state.results["analysis"] = structured
    update_step("step1", "done")
    progress_placeholder.markdown(render_progress())

    # Step 2: マニュアル生成（一発完成版）
    update_step("step2", "running")
    progress_placeholder.markdown(render_progress())
    final = run_draft(structured, verbose=False)
    final_path = output_dir / f"{ts}_{manual_title}.md"
    final_path.write_text(final, encoding="utf-8")
    st.session_state.results["final"] = final
    st.session_state.results["final_path"] = str(final_path)
    update_step("step2", "done")
    progress_placeholder.markdown(render_progress())

    # Miroフローデータ抽出
    _run_miro_extract(final, ts, output_dir)

    # Notion出力
    if enable_notion:
        _run_notion_push(manual_title, final)

    # Miro描画
    if enable_miro and st.session_state.results.get("flowchart_json"):
        _run_miro_push(st.session_state.results["flowchart_json"])


def run_update_pipeline(existing_text: str, minutes_text: str | None):
    """既存修正パイプライン

    議事録あり: ①差分分析 → ②更新草稿 → ③チェック → ④改善 → ⑤適用 → 出力
    議事録なし: ①チェック → ②改善 → ③適用 → 出力
    """
    from src.pipeline.check import run_check
    from src.pipeline.improve import run_improve
    from src.pipeline.apply import run_apply

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if minutes_text:
        # --- パターンA: 議事録あり ---
        from src.pipeline.analyze import run_merge_analyze
        from src.pipeline.draft import run_update_draft

        # Step 1: 差分分析
        update_step("step1", "running")
        progress_placeholder.markdown(render_progress())
        updates = run_merge_analyze(existing_text, minutes_text, verbose=False)
        (output_dir / f"{ts}_step1_updates.json").write_text(updates, encoding="utf-8")
        update_step("step1", "done")
        progress_placeholder.markdown(render_progress())

        # Step 2: 更新草稿
        update_step("step2", "running")
        progress_placeholder.markdown(render_progress())
        draft = run_update_draft(existing_text, updates, verbose=False)
        (output_dir / f"{ts}_step2_draft.md").write_text(draft, encoding="utf-8")
        st.session_state.results["draft"] = draft
        update_step("step2", "done")
        progress_placeholder.markdown(render_progress())
    else:
        # --- パターンB: 議事録なし（既存マニュアルのみ） ---
        draft = existing_text

    # チェック → 改善 → 適用（共通）
    update_step("check", "running")
    progress_placeholder.markdown(render_progress())
    check_result = run_check(draft, verbose=False)
    (output_dir / f"{ts}_check.md").write_text(check_result, encoding="utf-8")
    st.session_state.results["check"] = check_result
    update_step("check", "done")
    progress_placeholder.markdown(render_progress())

    update_step("improve", "running")
    progress_placeholder.markdown(render_progress())
    improve_result = run_improve(draft, check_result, verbose=False)
    (output_dir / f"{ts}_improve.md").write_text(improve_result, encoding="utf-8")
    st.session_state.results["improve"] = improve_result
    update_step("improve", "done")
    progress_placeholder.markdown(render_progress())

    update_step("apply", "running")
    progress_placeholder.markdown(render_progress())
    final = run_apply(draft, improve_result, verbose=False)
    final_path = output_dir / f"{ts}_updated_manual.md"
    final_path.write_text(final, encoding="utf-8")
    st.session_state.results["final"] = final
    st.session_state.results["final_path"] = str(final_path)
    update_step("apply", "done")
    progress_placeholder.markdown(render_progress())

    # Miroフローデータ抽出
    _run_miro_extract(final, ts, output_dir)

    # Notion出力
    if enable_notion:
        _run_notion_push("更新マニュアル", final)

    # Miro描画
    if enable_miro and st.session_state.results.get("flowchart_json"):
        _run_miro_push(st.session_state.results["flowchart_json"])


def run_check_only(manual_text: str):
    """チェックのみパイプライン: ①チェック → ②改善提案（適用しない）"""
    from src.pipeline.check import run_check
    from src.pipeline.improve import run_improve

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    update_step("check", "running")
    progress_placeholder.markdown(render_progress())
    check_result = run_check(manual_text, verbose=False)
    (output_dir / f"{ts}_check.md").write_text(check_result, encoding="utf-8")
    st.session_state.results["check"] = check_result
    update_step("check", "done")
    progress_placeholder.markdown(render_progress())

    update_step("improve", "running")
    progress_placeholder.markdown(render_progress())
    improve_result = run_improve(manual_text, check_result, verbose=False)
    (output_dir / f"{ts}_improve.md").write_text(improve_result, encoding="utf-8")
    st.session_state.results["improve"] = improve_result
    update_step("improve", "done")
    progress_placeholder.markdown(render_progress())


# ============================================================
# 進行状況表示
# ============================================================

def render_progress() -> str:
    """進行状況の表示テキスト"""
    if mode == "新規作成":
        steps = [
            ("step1", "構造化抽出"),
            ("step2", "マニュアル生成"),
            ("miro_extract", "Miroフローデータ生成"),
        ]
        if enable_notion:
            steps.append(("notion", "Notion出力"))
        if enable_miro:
            steps.append(("miro_push", "Miro描画"))

    elif mode == "既存修正":
        # 議事録の有無で表示を分岐
        has_minutes = st.session_state.get("_update_has_minutes", False)
        if has_minutes:
            steps = [
                ("step1", "差分分析"),
                ("step2", "更新草稿生成"),
                ("check", "適合性チェック（26項目）"),
                ("improve", "改善提案生成"),
                ("apply", "改善適用 → 最終版"),
                ("miro_extract", "Miroフローデータ生成"),
            ]
        else:
            steps = [
                ("check", "適合性チェック（26項目）"),
                ("improve", "改善提案生成"),
                ("apply", "改善適用 → 最終版"),
                ("miro_extract", "Miroフローデータ生成"),
            ]
        if enable_notion:
            steps.append(("notion", "Notion出力"))
        if enable_miro:
            steps.append(("miro_push", "Miro描画"))

    else:  # チェックのみ
        steps = [
            ("check", "適合性チェック（26項目）"),
            ("improve", "改善提案生成"),
        ]

    lines = []
    for key, label in steps:
        icon = get_step_icon(key)
        lines.append(f"{icon} {label}")
    return "\n\n".join(lines)


# 進行状況プレースホルダー
progress_placeholder = st.empty()

# 実行ボタン
error_msg = validate_inputs()
if st.button("▶ 実行", type="primary", use_container_width=True, disabled=bool(error_msg)):
    st.session_state.step_status = {}
    st.session_state.results = {}

    if mode == "新規作成":
        if uploaded:
            text = uploaded.read().decode("utf-8")
        else:
            text = pasted
        m_title = title or "マニュアル"
        m_type = type_map.get(manual_type, "business")

        with st.spinner("マニュアルを生成中..."):
            try:
                run_create_pipeline(text, m_title, m_type)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

    elif mode == "既存修正":
        existing_text = existing_file.read().decode("utf-8")
        new_text = new_minutes.read().decode("utf-8") if new_minutes else None
        st.session_state["_update_has_minutes"] = bool(new_text)

        with st.spinner("マニュアルを更新中..."):
            try:
                run_update_pipeline(existing_text, new_text)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

    else:  # チェックのみ
        manual_text = check_file.read().decode("utf-8")

        with st.spinner("チェック実行中..."):
            try:
                run_check_only(manual_text)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

if error_msg:
    st.warning(error_msg)

# --- 結果表示 ---
results = st.session_state.results

if results:
    st.divider()
    st.subheader("📊 結果")

    # メトリクス行
    if results.get("check"):
        rate_match = re.search(r"適合率[：:](\d+)%", results["check"])
        grade_match = re.search(r"総合評価[：:]([A-D])", results["check"])
        rate = rate_match.group(1) if rate_match else "—"
        grade = grade_match.group(1) if grade_match else "—"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("適合率", f"{rate}%")
        with col2:
            st.metric("総合評価", grade)
        with col3:
            step_count = sum(1 for v in st.session_state.step_status.values() if v == "done")
            st.metric("完了ステップ", f"{step_count}")

    # リンク
    if results.get("notion_url") or results.get("miro_url"):
        link_cols = st.columns(2)
        if results.get("notion_url"):
            with link_cols[0]:
                st.link_button("📝 Notionページを開く", results["notion_url"], use_container_width=True)
        if results.get("miro_url"):
            with link_cols[1]:
                st.link_button("🗺️ Miroボードを開く", results["miro_url"], use_container_width=True)

    if results.get("notion_error"):
        st.warning(f"Notion出力エラー: {results['notion_error']}")
    if results.get("miro_error"):
        st.warning(f"Miro出力エラー: {results['miro_error']}")

    # タブで結果表示
    tab_names = []
    tab_contents = []

    if results.get("final"):
        tab_names.append("📄 最終マニュアル")
        tab_contents.append("final")
    if results.get("check"):
        tab_names.append("📋 チェック結果")
        tab_contents.append("check")
    if results.get("improve"):
        tab_names.append("💡 改善提案")
        tab_contents.append("improve")
    if results.get("draft"):
        tab_names.append("📝 草稿")
        tab_contents.append("draft")
    if results.get("flowchart_json"):
        tab_names.append("🗺️ フローデータ")
        tab_contents.append("flowchart_json")

    if tab_names:
        tabs = st.tabs(tab_names)
        for tab, content_key in zip(tabs, tab_contents):
            with tab:
                content = results[content_key]
                st.markdown(content)

                # ダウンロードボタン
                if content_key == "flowchart_json":
                    st.download_button(
                        "⬇ JSONダウンロード",
                        data=content,
                        file_name="miro_flowchart.json",
                        mime="application/json",
                    )
                else:
                    fname_map = {
                        "final": "final_manual.md",
                        "check": "check_report.md",
                        "improve": "improve_report.md",
                        "draft": "draft.md",
                    }
                    st.download_button(
                        "⬇ Markdownダウンロード",
                        data=content,
                        file_name=fname_map.get(content_key, "output.md"),
                        mime="text/markdown",
                    )
