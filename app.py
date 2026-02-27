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

# Streamlit Cloud: Secrets が利用可能になった後にリロード
config.reload()

# --- ページ設定 ---
st.set_page_config(
    page_title="Manual Studio",
    page_icon="https://em-content.zobj.net/source/twitter/408/memo_1f4dd.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- カスタムCSS ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700&family=M+PLUS+1p:wght@400;500;700&family=Zen+Maru+Gothic:wght@500;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0" rel="stylesheet">
<style>
    :root {
        --teal: #2AACB8;
        --teal-dark: #1E8E99;
        --teal-deep: #16737D;
        --teal-light: #E7F5F7;
        --teal-pale: #F2FAFB;
        --navy: #1A3040;
        --navy-light: #2D4A5C;
        --text-muted: #5D8090;
        --border: #D0E4E8;
        --border-light: #E8F0F2;
        --white: #FFFFFF;
        --bg: #F7FBFC;
        --success: #10B981;
        --error: #EF4444;
    }

    /* ===== Base ===== */
    .stApp {
        font-family: 'M PLUS 1p', sans-serif !important;
    }
    .stMainBlockContainer {
        max-width: 1060px;
    }
    h1, h2, h3, h4 {
        font-family: 'Zen Maru Gothic', 'M PLUS 1p', sans-serif !important;
    }
    .stApp p, .stApp span, .stApp label, .stApp div {
        font-family: 'M PLUS 1p', sans-serif;
    }

    /* ===== Hero Header ===== */
    .hero-header {
        background: linear-gradient(135deg, #1A9EAB 0%, #2AACB8 40%, #5DC4CE 100%);
        border-radius: 18px;
        padding: 2.25rem 2.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -60%;
        right: -15%;
        width: 360px;
        height: 360px;
        background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-header::after {
        content: '';
        position: absolute;
        bottom: -40%;
        left: 10%;
        width: 240px;
        height: 240px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-header h1 {
        color: #FFFFFF;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
        position: relative;
        letter-spacing: 0.01em;
    }
    .hero-header p {
        color: rgba(255,255,255,0.82);
        font-size: 0.88rem;
        margin: 0;
        position: relative;
        font-family: 'M PLUS 1p', sans-serif;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(255,255,255,0.18);
        color: #FFFFFF;
        font-size: 0.68rem;
        font-weight: 700;
        font-family: 'DM Sans', sans-serif;
        padding: 0.25rem 0.7rem;
        border-radius: 100px;
        margin-bottom: 0.85rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        backdrop-filter: blur(4px);
    }
    .hero-badge .material-symbols-rounded {
        font-size: 14px;
    }

    /* ===== Section Labels ===== */
    .section-label {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        color: var(--teal-dark);
        font-family: 'Zen Maru Gothic', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
    }
    .section-label .material-symbols-rounded {
        font-size: 20px;
        color: var(--teal);
    }

    /* ===== Mode Selector ===== */
    div[data-testid="stSegmentedControl"] button {
        font-family: 'M PLUS 1p', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.15s ease;
    }
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        background: var(--teal) !important;
        color: white !important;
    }

    /* ===== Progress Pipeline ===== */
    .pipeline-container {
        background: var(--white);
        border: 1.5px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
    }
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        padding: 0.55rem 0;
        font-size: 0.88rem;
        font-family: 'M PLUS 1p', sans-serif;
        color: var(--text-muted);
        transition: all 0.2s;
    }
    .pipeline-step.done { color: var(--navy); font-weight: 500; }
    .pipeline-step.running { color: var(--teal-dark); font-weight: 700; }
    .pipeline-step.error { color: var(--error); }
    .step-num {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        flex-shrink: 0;
        transition: all 0.3s;
    }
    .num-pending {
        background: var(--teal-pale);
        color: var(--text-muted);
        border: 2px solid var(--border);
    }
    .num-running {
        background: var(--teal-light);
        color: var(--teal-dark);
        border: 2px solid var(--teal);
        animation: teal-pulse 1.8s ease-in-out infinite;
    }
    .num-done {
        background: var(--teal);
        color: var(--white);
        border: 2px solid var(--teal);
    }
    .num-done .material-symbols-rounded {
        font-size: 16px;
    }
    .num-error {
        background: #FEF2F2;
        color: var(--error);
        border: 2px solid var(--error);
    }
    @keyframes teal-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(42,172,184,0.35); }
        50% { box-shadow: 0 0 0 7px rgba(42,172,184,0); }
    }
    .step-connector {
        width: 2px;
        height: 10px;
        background: var(--border);
        margin-left: 14px;
        border-radius: 1px;
        transition: background 0.3s;
    }
    .step-connector.done { background: var(--teal); }

    /* ===== Metrics ===== */
    div[data-testid="stMetric"] {
        background: var(--white);
        border: 1.5px solid var(--border);
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 1px 4px rgba(42,172,184,0.06);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.72rem !important;
        font-family: 'M PLUS 1p', sans-serif !important;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'DM Sans', 'M PLUS 1p', sans-serif !important;
        color: var(--navy) !important;
    }

    /* ===== Link Buttons ===== */
    .stLinkButton a {
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        font-family: 'M PLUS 1p', sans-serif !important;
        border: 1.5px solid var(--teal) !important;
        color: var(--teal-dark) !important;
        transition: all 0.15s;
    }
    .stLinkButton a:hover {
        background: var(--teal-light) !important;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F2FAFB 0%, #E7F5F7 100%);
        border-right: 1.5px solid var(--border);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--navy) !important;
    }
    section[data-testid="stSidebar"] * {
        color: var(--navy-light) !important;
    }
    section[data-testid="stSidebar"] .stAlert p {
        font-size: 0.8rem !important;
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 2px solid var(--border-light);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0 !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        font-family: 'M PLUS 1p', sans-serif !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--teal-dark) !important;
        border-bottom-color: var(--teal) !important;
    }

    /* ===== File Uploader ===== */
    div[data-testid="stFileUploader"] section {
        border-radius: 14px !important;
        border: 2px dashed var(--border) !important;
        padding: 1.25rem !important;
        background: var(--teal-pale) !important;
        transition: border-color 0.2s;
    }
    div[data-testid="stFileUploader"] section:hover {
        border-color: var(--teal) !important;
    }

    /* ===== Primary Button ===== */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--teal) 0%, var(--teal-dark) 100%) !important;
        border: none !important;
        border-radius: 14px !important;
        font-family: 'Zen Maru Gothic', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.8rem !important;
        letter-spacing: 0.04em;
        color: white !important;
        box-shadow: 0 4px 14px rgba(42,172,184,0.3);
        transition: all 0.2s;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 22px rgba(42,172,184,0.4);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0px);
    }

    /* ===== Download Button ===== */
    .stDownloadButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1.5px solid var(--border) !important;
        font-family: 'M PLUS 1p', sans-serif !important;
    }

    /* ===== Text Input ===== */
    .stTextInput input {
        border-radius: 10px !important;
        border: 1.5px solid var(--border) !important;
        font-family: 'M PLUS 1p', sans-serif !important;
    }
    .stTextInput input:focus {
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 2px rgba(42,172,184,0.15) !important;
    }
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 1.5px solid var(--border) !important;
        font-family: 'M PLUS 1p', sans-serif !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 2px rgba(42,172,184,0.15) !important;
    }

    /* ===== Divider ===== */
    hr {
        border-color: var(--border-light) !important;
    }

    /* ===== Completion Banner ===== */
    .completion-banner {
        background: linear-gradient(135deg, #E7F5F7 0%, #D4F0F3 100%);
        border: 1.5px solid var(--teal);
        border-radius: 14px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .completion-banner .material-symbols-rounded {
        font-size: 22px;
        color: var(--teal-dark);
    }
    .completion-banner span {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--teal-deep);
        font-family: 'Zen Maru Gothic', sans-serif;
    }

    /* ===== Warning override ===== */
    .stAlert [data-testid="stNotificationContentWarning"] {
        font-family: 'M PLUS 1p', sans-serif !important;
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


def _update_progress():
    """進行状況HTMLを再描画"""
    progress_placeholder.markdown(render_progress(), unsafe_allow_html=True)


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
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.5rem;">
        <span class="material-symbols-rounded" style="font-size:22px; color:#1E8E99;">tune</span>
        <span style="font-family:'Zen Maru Gothic',sans-serif; font-weight:700; font-size:1.1rem; color:#1A3040;">出力設定</span>
    </div>
    """, unsafe_allow_html=True)

    enable_notion = st.toggle("Notionに出力", value=False)
    enable_miro = st.toggle("Miroにフロー描画", value=False)

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



# --- メインUI ---
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">
        <span class="material-symbols-rounded">auto_awesome</span>
        AI-Powered
    </div>
    <h1>Manual Studio</h1>
    <p>議事録・MTG文字起こしから、ルール準拠のマニュアルを自動生成 → Notion / Miro に出力</p>
</div>
""", unsafe_allow_html=True)

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
        st.markdown('<div class="section-label"><span class="material-symbols-rounded">upload_file</span>議事録をアップロード</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="section-label"><span class="material-symbols-rounded">upload_file</span>ファイルをアップロード</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="section-label"><span class="material-symbols-rounded">fact_check</span>チェック対象マニュアル</div>', unsafe_allow_html=True)
        check_file = st.file_uploader(
            "マニュアルファイル (.md)",
            type=["txt", "md"],
            key="check_file",
        )

with col_options:
    if mode == "新規作成":
        st.markdown('<div class="section-label"><span class="material-symbols-rounded">settings</span>オプション</div>', unsafe_allow_html=True)
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
        return "ANTHROPIC_API_KEY が未設定です（.env または Secrets を確認）"
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
    _update_progress()
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
    _update_progress()


def _run_notion_push(manual_title: str, final: str):
    """Notionにページを作成"""
    update_step("notion", "running")
    _update_progress()
    try:
        from src.integrations.notion_client import create_notion_page
        url = create_notion_page(manual_title, final)
        st.session_state.results["notion_url"] = url
        update_step("notion", "done")
    except Exception as e:
        st.session_state.results["notion_error"] = str(e)
        update_step("notion", "error")
    _update_progress()


def _run_miro_push(fc_json: str):
    """Miroにフローチャートを描画"""
    update_step("miro_push", "running")
    _update_progress()
    try:
        from src.integrations.miro_client import create_flowchart_from_json
        miro_url = create_flowchart_from_json(fc_json)
        st.session_state.results["miro_url"] = miro_url
        update_step("miro_push", "done")
    except Exception as e:
        st.session_state.results["miro_error"] = str(e)
        update_step("miro_push", "error")
    _update_progress()


def run_create_pipeline(minutes_text: str, manual_title: str, m_type: str):
    """新規作成パイプライン: ①構造化抽出 → ②マニュアル生成 → 出力"""
    from src.pipeline.analyze import run_analyze
    from src.pipeline.draft import run_draft

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: 構造化抽出
    update_step("step1", "running")
    _update_progress()
    structured = run_analyze(minutes_text, m_type, verbose=False)
    (output_dir / f"{ts}_step1_analysis.json").write_text(structured, encoding="utf-8")
    st.session_state.results["analysis"] = structured
    update_step("step1", "done")
    _update_progress()

    # Step 2: マニュアル生成（一発完成版）
    update_step("step2", "running")
    _update_progress()
    final = run_draft(structured, verbose=False)
    final_path = output_dir / f"{ts}_{manual_title}.md"
    final_path.write_text(final, encoding="utf-8")
    st.session_state.results["final"] = final
    st.session_state.results["final_path"] = str(final_path)
    update_step("step2", "done")
    _update_progress()

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
        _update_progress()
        updates = run_merge_analyze(existing_text, minutes_text, verbose=False)
        (output_dir / f"{ts}_step1_updates.json").write_text(updates, encoding="utf-8")
        update_step("step1", "done")
        _update_progress()

        # Step 2: 更新草稿
        update_step("step2", "running")
        _update_progress()
        draft = run_update_draft(existing_text, updates, verbose=False)
        (output_dir / f"{ts}_step2_draft.md").write_text(draft, encoding="utf-8")
        st.session_state.results["draft"] = draft
        update_step("step2", "done")
        _update_progress()
    else:
        # --- パターンB: 議事録なし（既存マニュアルのみ） ---
        draft = existing_text

    # チェック → 改善 → 適用（共通）
    update_step("check", "running")
    _update_progress()
    check_result = run_check(draft, verbose=False)
    (output_dir / f"{ts}_check.md").write_text(check_result, encoding="utf-8")
    st.session_state.results["check"] = check_result
    update_step("check", "done")
    _update_progress()

    update_step("improve", "running")
    _update_progress()
    improve_result = run_improve(draft, check_result, verbose=False)
    (output_dir / f"{ts}_improve.md").write_text(improve_result, encoding="utf-8")
    st.session_state.results["improve"] = improve_result
    update_step("improve", "done")
    _update_progress()

    update_step("apply", "running")
    _update_progress()
    final = run_apply(draft, improve_result, verbose=False)
    final_path = output_dir / f"{ts}_updated_manual.md"
    final_path.write_text(final, encoding="utf-8")
    st.session_state.results["final"] = final
    st.session_state.results["final_path"] = str(final_path)
    update_step("apply", "done")
    _update_progress()

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
    _update_progress()
    check_result = run_check(manual_text, verbose=False)
    (output_dir / f"{ts}_check.md").write_text(check_result, encoding="utf-8")
    st.session_state.results["check"] = check_result
    update_step("check", "done")
    _update_progress()

    update_step("improve", "running")
    _update_progress()
    improve_result = run_improve(manual_text, check_result, verbose=False)
    (output_dir / f"{ts}_improve.md").write_text(improve_result, encoding="utf-8")
    st.session_state.results["improve"] = improve_result
    update_step("improve", "done")
    _update_progress()


# ============================================================
# 進行状況表示
# ============================================================

def _get_steps_for_mode():
    """現在のモードに応じたステップリストを返す"""
    if mode == "新規作成":
        steps = [
            ("step1", "構造化抽出"),
            ("step2", "マニュアル生成"),
            ("miro_extract", "フローデータ生成"),
        ]
        if enable_notion:
            steps.append(("notion", "Notion出力"))
        if enable_miro:
            steps.append(("miro_push", "Miro描画"))

    elif mode == "既存修正":
        has_minutes = st.session_state.get("_update_has_minutes", False)
        if has_minutes:
            steps = [
                ("step1", "差分分析"),
                ("step2", "更新草稿生成"),
                ("check", "適合性チェック"),
                ("improve", "改善提案"),
                ("apply", "改善適用"),
                ("miro_extract", "フローデータ生成"),
            ]
        else:
            steps = [
                ("check", "適合性チェック"),
                ("improve", "改善提案"),
                ("apply", "改善適用"),
                ("miro_extract", "フローデータ生成"),
            ]
        if enable_notion:
            steps.append(("notion", "Notion出力"))
        if enable_miro:
            steps.append(("miro_push", "Miro描画"))

    else:
        steps = [
            ("check", "適合性チェック"),
            ("improve", "改善提案"),
        ]
    return steps


def render_progress() -> str:
    """パイプライン風の進行状況HTML"""
    steps = _get_steps_for_mode()
    html_parts = ['<div class="pipeline-container">']

    for i, (key, label) in enumerate(steps):
        status = st.session_state.step_status.get(key, "pending")
        num = f"{i + 1:02d}"

        if status == "done":
            num_class = "num-done"
            step_class = "done"
            inner = '<span class="material-symbols-rounded">check</span>'
        elif status == "running":
            num_class = "num-running"
            step_class = "running"
            inner = num
        elif status == "error":
            num_class = "num-error"
            step_class = "error"
            inner = '<span class="material-symbols-rounded" style="font-size:16px">close</span>'
        else:
            num_class = "num-pending"
            step_class = ""
            inner = num

        html_parts.append(f'''
            <div class="pipeline-step {step_class}">
                <div class="step-num {num_class}">{inner}</div>
                <span>{label}</span>
            </div>
        ''')

        if i < len(steps) - 1:
            conn_class = "done" if status == "done" else ""
            html_parts.append(f'<div class="step-connector {conn_class}"></div>')

    html_parts.append('</div>')
    return ''.join(html_parts)


# 進行状況プレースホルダー
progress_placeholder = st.empty()

# 実行ボタン
error_msg = validate_inputs()
if st.button("実行する", type="primary", use_container_width=True, disabled=bool(error_msg)):
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

    # 完了バナー
    done_count = sum(1 for v in st.session_state.step_status.values() if v == "done")
    error_count = sum(1 for v in st.session_state.step_status.values() if v == "error")
    if done_count > 0 and error_count == 0:
        st.markdown("""
        <div class="completion-banner">
            <span class="material-symbols-rounded">task_alt</span>
            <span>完了 — 全ステップが正常に終了しました</span>
        </div>
        """, unsafe_allow_html=True)

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
            st.metric("完了ステップ", f"{done_count}")

    # 出力リンク
    if results.get("notion_url") or results.get("miro_url"):
        st.markdown("")  # spacing
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
