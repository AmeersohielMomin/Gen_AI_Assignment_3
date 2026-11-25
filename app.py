"""
Meeting Minutes Generator
Roll No: 03 | Enrollment: ADT23SOCB0116
Name: Ameersohiel N Momin | Class: LYAIA04
PS-3: Convert meeting transcripts to structured minutes using DeepSeek API.
"""

import time
import streamlit as st
from prompts import build_system_prompt
from utils import (
    analyze_transcript,
    create_docx,
    create_txt,
    extract_minutes_stats,
    generate_minutes,
    get_api_key,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Meeting Minutes Generator · DeepSeek AI",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — Modern DeepSeek Slate & Indigo Theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Canvas */
    .stApp {
        background: radial-gradient(circle at 12% 10%, rgba(77, 107, 254, 0.10), transparent 38%),
                    radial-gradient(circle at 88% 15%, rgba(56, 189, 248, 0.08), transparent 34%),
                    #0B0F19;
        color: #E2E8F0;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 55%, #172554 100%);
        border: 1px solid rgba(77, 107, 254, 0.35);
        box-shadow: 0 12px 32px rgba(2, 6, 23, 0.55);
        padding: 1.75rem 2.2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(77, 107, 254, 0.18);
        border: 1px solid rgba(77, 107, 254, 0.45);
        color: #93C5FD;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        margin-bottom: 0.7rem;
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 2.15rem;
        font-weight: 700;
        color: #F8FAFC;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        margin: 0.45rem 0 0.9rem 0;
        color: #94A3B8;
        font-size: 0.98rem;
    }
    .meta-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .meta-pill {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(148, 163, 184, 0.2);
        color: #CBD5E1;
        padding: 0.25rem 0.7rem;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 500;
    }

    /* Section Header */
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #F1F5F9;
        margin: 0.2rem 0 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Metric Cards */
    .metric-card {
        background: #111827;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        text-align: center;
        transition: border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: rgba(77, 107, 254, 0.5);
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #60A5FA;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* Status Pill in Sidebar */
    .status-pill-ok {
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #6EE7B7;
        padding: 0.45rem 0.75rem;
        border-radius: 10px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 0.75rem;
    }
    .status-pill-warn {
        background: rgba(245, 158, 11, 0.14);
        border: 1px solid rgba(245, 158, 11, 0.4);
        color: #FCD34D;
        padding: 0.45rem 0.75rem;
        border-radius: 10px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 0.75rem;
    }

    /* Styled Container Borders */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #111827;
        border-color: rgba(77, 107, 254, 0.28) !important;
        border-radius: 14px !important;
        padding: 0.5rem;
    }

    /* TextArea */
    .stTextArea textarea {
        background-color: #0F172A !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        border-radius: 12px !important;
        color: #E2E8F0 !important;
        font-size: 0.93rem !important;
        line-height: 1.55 !important;
    }
    .stTextArea textarea:focus {
        border-color: #4D6BFE !important;
        box-shadow: 0 0 0 1px #4D6BFE !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #111827;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 7px;
        padding: 0.45rem 1rem;
        color: #94A3B8;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4D6BFE, #2563EB) !important;
        color: #FFFFFF !important;
    }

    /* Primary Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4D6BFE 0%, #2563EB 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 1.5rem;
        font-weight: 600;
        font-size: 0.98rem;
        box-shadow: 0 6px 20px rgba(77, 107, 254, 0.32);
        transition: all 0.18s ease;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 26px rgba(77, 107, 254, 0.48);
    }

    /* Secondary Buttons (Samples & Clear) */
    .stButton > button[kind="secondary"] {
        background: #111827;
        color: #CBD5E1;
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: #4D6BFE;
        color: #FFFFFF;
        background: rgba(77, 107, 254, 0.14);
    }

    /* Download Buttons */
    .stDownloadButton > button {
        background: #111827;
        border: 1px solid rgba(77, 107, 254, 0.55);
        color: #93C5FD;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
        padding: 0.6rem 1rem;
        transition: all 0.18s ease;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #4D6BFE, #2563EB);
        border-color: transparent;
        color: #FFFFFF;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(148, 163, 184, 0.14);
    }

    /* Markdown Tables in Result */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.75rem 0;
    }
    th {
        background-color: rgba(77, 107, 254, 0.22);
        color: #E2E8F0;
        text-align: left;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #64748B;
        font-size: 0.78rem;
        padding: 1.5rem 0 0.5rem;
        border-top: 1px solid rgba(148, 163, 184, 0.14);
        margin-top: 2.2rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sample Transcripts
# ─────────────────────────────────────────────────────────────────────────────
SAMPLES = {
    "Team Standup": """Team Standup Meeting
Date: November 20, 2026
Time: 9:00 AM
Platform: Google Meet

Attendees: Priya Sharma (Tech Lead), Rahul Verma (Backend Dev), Anjali Nair (Frontend Dev), Dev Patel (QA Engineer)

Priya: Good morning everyone. Let's keep this quick. Rahul, what's your update?

Rahul: I finished the user authentication module yesterday. It's ready for review. I'll start working on the payment gateway integration today.

Priya: Great. Anjali?

Anjali: The dashboard UI is 80% done. I need the API endpoints from Rahul to complete the data binding. I should be done by tomorrow.

Priya: Rahul, can you share the API docs with Anjali today?

Rahul: Sure, I'll send them by noon.

Dev: I've completed testing on the registration flow. Found 3 bugs — I'll log them in Jira. Need the auth module from Rahul to start integration testing.

Priya: Decided: We'll freeze all feature additions by November 25th. QA testing sprint begins November 26th.

Priya: Also, our demo to the client is scheduled for December 1st. Everyone must have their modules demo-ready by November 28th.

Dev: Should I prepare test reports for the client demo?

Priya: Yes, please prepare a one-page test summary report by November 27th.

Priya: Any blockers?

Anjali: I'll be blocked until I get the API endpoints.

Priya: Rahul, please prioritize that. Alright, that's it. Have a productive day everyone.
""",

    "Project Planning": """Project Planning Meeting — EduTrack Mobile App
Date: November 18, 2026
Time: 2:00 PM – 3:30 PM
Location: Conference Room B

Attendees:
- Meera Joshi (Project Manager)
- Karan Mehta (Lead Developer)
- Suresh Pillai (UI/UX Designer)
- Fatima Sheikh (Business Analyst)
- Ravi Kumar (Database Architect)

Meera: Welcome everyone. Today we're planning the EduTrack mobile app project. Fatima, can you walk us through the requirements?

Fatima: Sure. The app needs student attendance tracking, grade management, parent-teacher messaging, and a timetable viewer. Priority is attendance and grades for the MVP.

Meera: Based on that, what's our tech stack recommendation, Karan?

Karan: I recommend React Native for cross-platform, Node.js backend, and PostgreSQL for the database. Firebase for push notifications.

Ravi: Agreed on PostgreSQL. I'll need to design the schema for multi-school support. That'll take about a week.

Suresh: I'll start with wireframes for the student dashboard and attendance screens. Can I get the finalized requirements document from Fatima?

Fatima: I'll have it ready by Friday, November 22nd.

Decisions:
1. MVP scope confirmed: attendance tracking + grade management only.
2. Tech stack approved: React Native, Node.js, PostgreSQL, Firebase.
3. Project deadline set for February 15, 2027.
4. Weekly progress reviews every Monday at 2 PM.
5. Karan will set up the GitHub repository and CI/CD pipeline.

Action items:
- Ravi to complete database schema design by November 25.
- Suresh to deliver wireframes for 5 core screens by November 29.
- Fatima to send finalized requirements doc by November 22.
- Karan to set up the project repository and dev environment by November 22.
- Meera to schedule the kickoff meeting with the client for November 25.

Meera: Any concerns?

Karan: We may need an extra developer for the backend. I'll flag it if needed after reviewing the schema.

Meera: Noted. I'll keep a resource buffer. Let's reconvene next Monday.
""",

    "Client Call": """Client Call — Website Redesign Project
Date: November 21, 2026
Time: 11:00 AM
Platform: Zoom

Attendees:
- Sarah Thompson (Client — CEO, GreenLeaf Organics)
- Tom Baker (Client — Marketing Head, GreenLeaf Organics)
- Nikhil Desai (Account Manager, WebCraft Agency)
- Pooja Reddy (Lead Designer, WebCraft Agency)

Nikhil: Good morning Sarah, Tom. Thanks for joining. We're here to review the design mockups and discuss next steps.

Sarah: Of course. We've had a chance to look at the mockups. Overall we love the clean look. The green color palette is perfect for our brand.

Tom: My only concern is the homepage hero section. The image feels generic. We want something that showcases our actual farm and products.

Pooja: Completely understood. We can replace the stock photo with your brand photography. Do you have high-resolution images we can use?

Tom: Yes, I'll send over a Dropbox link with our photo library today.

Sarah: Also, we need the product listing page to have filter options — by category, price range, and organic certification level.

Nikhil: Noted. Pooja, can we incorporate that?

Pooja: Yes. I'll add filter components to the product page wireframe. I'll have a revised mockup ready by November 26th.

Sarah: One more thing — we need the site live before December 15th. That's our holiday sale launch.

Nikhil: We can make that work if we finalize designs by November 28th and start development by December 1st.

Decisions:
1. Homepage hero image will be replaced with client's own photography.
2. Product listing page will include category, price, and certification filters.
3. Final design sign-off deadline: November 28, 2026.
4. Development start: December 1, 2026.
5. Website launch deadline: December 15, 2026.

Tom: We're also considering adding a blog section. Can that be in scope?

Nikhil: That would be a Phase 2 addition to avoid delaying the launch. We can discuss it after go-live.

Sarah: That works for us.

Nikhil: Great. I'll send a follow-up email summarizing today's decisions and next steps.
""",
}

# Initialize session state cleanly
if "transcript_text" not in st.session_state:
    st.session_state["transcript_text"] = ""


def _render_metric_card(col, value: str, label: str) -> None:
    col.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 DeepSeek Settings")

    env_key = get_api_key()
    if env_key:
        st.markdown(
            '<div class="status-pill-ok">● API Key Connected (.env)</div>',
            unsafe_allow_html=True,
        )
        custom_api_key = None
    else:
        st.markdown(
            '<div class="status-pill-warn">▲ No .env key detected</div>',
            unsafe_allow_html=True,
        )
        custom_api_key = st.text_input(
            "Enter DeepSeek API Key",
            type="password",
            placeholder="sk-...",
        )

    model_choice = st.selectbox(
        "Model",
        options=["deepseek-chat", "deepseek-reasoner"],
        format_func=lambda m: (
            "deepseek-chat (V3 · Fast)" if m == "deepseek-chat" else "deepseek-reasoner (R1 · Deep)"
        ),
    )

    detail_level = st.radio(
        "Summary Detail Level",
        options=["Standard", "Concise (Executive)", "Detailed"],
        index=0,
    )

    meeting_type_hint = st.selectbox(
        "Meeting Type Hint",
        options=["Auto-detect", "Team Standup", "Project Planning", "Client Call", "Academic / Review"],
    )

    st.markdown("---")
    st.markdown("### 🎓 Student & Project Info")
    st.markdown(
        """
| Field | Details |
|---|---|
| **Student** | Ameersohiel N Momin |
| **Roll No** | 03 |
| **Enrollment** | ADT23SOCB0116 |
| **Class** | LYAIA04 |
| **Problem** | PS-3 (Minutes Generator) |
"""
    )

    st.markdown("---")
    st.markdown("### 📖 Workflow")
    st.markdown(
        """
1. Load a sample or upload `.txt`
2. Adjust model & detail preferences
3. Click **Generate Meeting Minutes**
4. Export as `.docx`, `.txt`, or `.md`
"""
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hero Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero-banner">
    <div class="hero-badge">PS-3 · DeepSeek AI Powered</div>
    <h1>📋 Meeting Minutes Generator</h1>
    <p class="hero-subtitle">
        Transform raw meeting transcripts into structured minutes with attendees, key decisions, and assigned action items.
    </p>
    <div class="meta-pills">
        <span class="meta-pill">👤 Ameersohiel N Momin</span>
        <span class="meta-pill">🆔 Roll No: 03</span>
        <span class="meta-pill">🎓 ADT23SOCB0116</span>
        <span class="meta-pill">🏫 LYAIA04</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Input Section
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">1️⃣ Meeting Transcript Input</div>', unsafe_allow_html=True)

input_mode = st.radio(
    "Choose input method",
    options=["📝 Paste / Edit Text", "📄 Upload .txt File"],
    horizontal=True,
    label_visibility="collapsed",
)

transcript = ""

if input_mode == "📝 Paste / Edit Text":
    st.caption("Quick-load a sample transcript or paste your own below:")
    s_col1, s_col2, s_col3, s_col4 = st.columns([1, 1, 1, 0.7])
    if s_col1.button("📌 Team Standup", use_container_width=True):
        st.session_state["transcript_text"] = SAMPLES["Team Standup"]
    if s_col2.button("🗓️ Project Planning", use_container_width=True):
        st.session_state["transcript_text"] = SAMPLES["Project Planning"]
    if s_col3.button("🤝 Client Call", use_container_width=True):
        st.session_state["transcript_text"] = SAMPLES["Client Call"]
    if s_col4.button("🗑️ Clear", use_container_width=True):
        st.session_state["transcript_text"] = ""

    transcript = st.text_area(
        "Meeting Transcript",
        key="transcript_text",
        height=260,
        placeholder="Example:\nAlice: Let's finalize the Q4 budget by Friday.\nBob: Agreed. I will send the spreadsheet tomorrow.",
        label_visibility="collapsed",
    )
else:
    uploaded_file = st.file_uploader(
        "Upload a plain-text transcript (.txt)",
        type=["txt"],
        help="Upload a .txt file containing the meeting conversation.",
    )
    if uploaded_file is not None:
        transcript = uploaded_file.read().decode("utf-8", errors="ignore")
        st.success(f"✅ Loaded **{uploaded_file.name}** ({len(transcript):,} characters)")
        with st.expander("👁️ Preview uploaded transcript", expanded=False):
            st.text(transcript[:3000] + ("\n..." if len(transcript) > 3000 else ""))

# Live transcript metrics
metrics = analyze_transcript(transcript)
m1, m2, m3, m4 = st.columns(4)
_render_metric_card(m1, f"{metrics['words']:,}", "Words")
_render_metric_card(m2, f"{metrics['chars']:,}", "Characters")
_render_metric_card(m3, f"{metrics['lines']:,}", "Non-Empty Lines")
_render_metric_card(m4, f"{metrics['speakers']}", "Detected Speakers")

st.markdown("<div style='height: 0.85rem;'></div>", unsafe_allow_html=True)

# Generate Action Row
col_action, col_hint = st.columns([1.2, 2.8])
with col_action:
    generate_clicked = st.button(
        "✨ Generate Meeting Minutes",
        type="primary",
        use_container_width=True,
        disabled=not transcript.strip(),
    )
with col_hint:
    if not transcript.strip():
        st.info("Select a sample above, paste a transcript, or upload a `.txt` file to begin.")
    else:
        st.caption(
            f"Ready to process with **{model_choice}** · Detail: **{detail_level}** · Type: **{meeting_type_hint}**"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Generate & Display Minutes
# ─────────────────────────────────────────────────────────────────────────────
if generate_clicked and transcript.strip():
    system_prompt = build_system_prompt(detail_level, meeting_type_hint)
    with st.spinner(f"🔄 Analyzing transcript with DeepSeek ({model_choice})..."):
        started = time.perf_counter()
        try:
            minutes = generate_minutes(
                transcript=transcript,
                system_prompt=system_prompt,
                model=model_choice,
                api_key=custom_api_key,
            )
            elapsed = round(time.perf_counter() - started, 2)
            st.session_state["minutes"] = minutes
            st.session_state["last_model"] = model_choice
            st.session_state["last_elapsed"] = elapsed
            st.session_state["generated"] = True
        except ValueError as err:
            st.error(f"🔑 Configuration Error: {err}")
        except Exception as err:
            st.error(f"❌ DeepSeek API Error: {err}")

if st.session_state.get("generated") and st.session_state.get("minutes"):
    minutes = st.session_state["minutes"]
    stats = extract_minutes_stats(minutes)
    last_model = st.session_state.get("last_model", model_choice)
    last_elapsed = st.session_state.get("last_elapsed", 0.0)

    st.markdown("---")
    st.markdown('<div class="section-title">2️⃣ Generated Meeting Minutes</div>', unsafe_allow_html=True)

    # Summary KPI cards
    k1, k2, k3, k4 = st.columns(4)
    _render_metric_card(k1, str(stats["attendees"]), "Attendees Extracted")
    _render_metric_card(k2, str(stats["decisions"]), "Decisions Logged")
    _render_metric_card(k3, str(stats["action_items"]), "Action Items")
    _render_metric_card(k4, f"{last_elapsed}s", f"Model · {last_model}")

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Output Tabs
    view_tab, raw_tab = st.tabs(["📋 Formatted Minutes", "💻 Raw Markdown (Copy)"])
    with view_tab:
        with st.container(border=True):
            st.markdown(minutes)
    with raw_tab:
        st.code(minutes, language="markdown")

    # Export Toolbar
    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">3️⃣ Export & Download</div>', unsafe_allow_html=True)

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        try:
            docx_bytes = create_docx(minutes)
            st.download_button(
                label="📝 Download Word (.docx)",
                data=docx_bytes,
                file_name="meeting_minutes.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except Exception as err:
            st.error(f"DOCX export failed: {err}")

    with dl_col2:
        txt_bytes = create_txt(minutes)
        st.download_button(
            label="📄 Download Plain Text (.txt)",
            data=txt_bytes,
            file_name="meeting_minutes.txt",
            mime="text/plain",
        )

    with dl_col3:
        st.download_button(
            label="📋 Download Markdown (.md)",
            data=minutes.encode("utf-8"),
            file_name="meeting_minutes.md",
            mime="text/markdown",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="footer">
    Meeting Minutes Generator · PS-3 · Ameersohiel N Momin (Roll No: 03 · ADT23SOCB0116 · LYAIA04)<br/>
    Powered by DeepSeek API (<code>deepseek-chat</code> / <code>deepseek-reasoner</code>)
</div>
""",
    unsafe_allow_html=True,
)
