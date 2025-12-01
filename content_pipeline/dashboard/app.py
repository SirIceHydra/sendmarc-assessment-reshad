"""
Streamlit Dashboard for Content Pipeline Review
Human review interface for approving generated content
"""
import os
import sys
import streamlit as st
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import db
from main import run_pipeline, get_pipeline_outputs


# Page configuration
st.set_page_config(
    page_title="Sendmarc Content Pipeline",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern look
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0d1117 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e6edf3;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #21262d 0%, #161b22 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
    }
    
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-passed { background: #238636; color: white; }
    .status-blocked { background: #da3633; color: white; }
    .status-review { background: #9e6a03; color: white; }
    .status-running { background: #1f6feb; color: white; }
    .status-approved { background: #238636; color: white; }
    .status-rejected { background: #da3633; color: white; }
    
    /* Pipeline item styling */
    .pipeline-item {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        transition: all 0.2s ease;
    }
    
    .pipeline-item:hover {
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.2);
    }
    
    /* Score gauge */
    .score-gauge {
        background: linear-gradient(90deg, #da3633 0%, #9e6a03 50%, #238636 100%);
        height: 8px;
        border-radius: 4px;
        margin: 8px 0;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #58a6ff;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #21262d;
    }
    
    /* Info cards */
    .info-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        margin: 10px 0;
    }
    
    /* Welcome hero */
    .welcome-hero {
        background: linear-gradient(135deg, #238636 0%, #1f6feb 100%);
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Better tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #21262d;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #238636, #1f6feb);
    }
    
    /* Better buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)


def get_status_badge(status: str) -> str:
    """Generate HTML for status badge"""
    status_lower = status.lower() if status else 'unknown'
    badge_class = {
        'completed': 'status-passed',
        'review_required': 'status-review',
        'approved': 'status-approved',
        'rejected': 'status-rejected',
        'blocked_qa': 'status-blocked',
        'blocked_safety': 'status-blocked',
        'running': 'status-running',
        'failed': 'status-blocked',
    }.get(status_lower, 'status-review')
    
    display_text = status.replace('_', ' ').title() if status else 'Unknown'
    return f'<span class="status-badge {badge_class}">{display_text}</span>'


def init_session_state():
    """Initialize session state variables"""
    if 'current_pipeline_id' not in st.session_state:
        st.session_state.current_pipeline_id = None
    if 'pipeline_outputs' not in st.session_state:
        st.session_state.pipeline_outputs = None
    if 'show_feedback_form' not in st.session_state:
        st.session_state.show_feedback_form = False
    if 'show_reject_form' not in st.session_state:
        st.session_state.show_reject_form = False


def run_new_pipeline():
    """Run a new pipeline from URL"""
    url = st.session_state.get('url_input', '')
    
    if not url:
        st.error("Please enter a URL")
        return
    
    with st.spinner("🔄 Running content pipeline... This may take several minutes."):
        try:
            pipeline_id = run_pipeline(url)
            st.session_state.current_pipeline_id = pipeline_id
            st.session_state.pipeline_outputs = get_pipeline_outputs(pipeline_id)
            st.success(f"✅ Pipeline completed! ID: {pipeline_id[:8]}...")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Pipeline failed: {str(e)}")


def load_pipeline(pipeline_id: str):
    """Load an existing pipeline"""
    try:
        st.session_state.current_pipeline_id = pipeline_id
        st.session_state.pipeline_outputs = get_pipeline_outputs(pipeline_id)
        st.rerun()
    except Exception as e:
        st.error(f"Failed to load pipeline: {str(e)}")


def render_sidebar():
    """Render sidebar with pipeline controls"""
    with st.sidebar:
        # Logo/Brand area
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #58a6ff; margin: 0; font-size: 1.5rem;">✉️ Sendmarc</h1>
            <p style="color: #8b949e; margin: 5px 0 0 0; font-size: 0.85rem;">Content Intelligence Pipeline</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # New Pipeline Section
        st.markdown("### 🆕 Create New")
        
        url = st.text_input(
            "Competitor Blog URL",
            key="url_input",
            placeholder="https://example.com/blog/article",
            label_visibility="collapsed"
        )
        
        st.caption("Enter a competitor blog URL to analyze and generate content")
        
        if st.button("▶️ Run Pipeline", type="primary", use_container_width=True):
            run_new_pipeline()
        
        st.markdown("---")
        
        # Recent Pipelines Section
        st.markdown("### 📋 Recent Pipelines")
        
        pipelines = db.list_pipelines(limit=10)
        
        if pipelines:
            for pipeline in pipelines:
                pid = pipeline['id']
                status = pipeline['status']
                created = pipeline.get('created_at', '')
                
                # Format date
                if created:
                    try:
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        date_str = dt.strftime("%b %d, %H:%M")
                    except:
                        date_str = created[:10]
                else:
                    date_str = "N/A"
                
                # Status color
                status_color = {
                    'completed': '🟢',
                    'review_required': '🟡',
                    'approved': '✅',
                    'rejected': '❌',
                    'blocked_qa': '🔴',
                    'blocked_safety': '🔴',
                    'running': '🔵',
                    'failed': '🔴',
                }.get(status, '⚪')
                
                # Create clickable pipeline item
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div style="font-size: 0.85rem;">
                        <span style="color: #58a6ff; font-weight: 500;">{pid[:8]}...</span><br>
                        <span style="color: #8b949e;">{status_color} {status.replace('_', ' ').title()} • {date_str}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("📂", key=f"load_{pid}", help="Load this pipeline"):
                        load_pipeline(pid)
        else:
            st.info("No pipelines yet. Create one above!")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #8b949e; font-size: 0.75rem;">
            <p>v1.0 MVP • Made with ❤️</p>
        </div>
        """, unsafe_allow_html=True)


def render_welcome():
    """Render welcome screen when no pipeline is selected"""
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <h1 style="font-size: 2.5rem; margin-bottom: 10px;">✉️ Welcome to Sendmarc Content Pipeline</h1>
        <p style="font-size: 1.1rem; color: #8b949e; max-width: 600px; margin: 0 auto 30px auto;">
            Transform competitor content into original, brand-aligned blog posts with AI-powered analysis and generation.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="info-card">
            <h3>🔍 Analyze</h3>
            <p style="color: #8b949e;">Extract insights from competitor content, identify gaps, and find unique angles.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-card">
            <h3>✍️ Generate</h3>
            <p style="color: #8b949e;">Create original content with Sendmarc's brand voice using RAG-powered generation.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="info-card">
            <h3>✅ Review</h3>
            <p style="color: #8b949e;">Quality checks for SEO, plagiarism, and readability with human approval workflow.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How it works
    st.markdown("### 🚀 How It Works")
    
    steps = [
        ("1️⃣", "Enter URL", "Paste a competitor blog URL in the sidebar"),
        ("2️⃣", "Run Pipeline", "Click 'Run Pipeline' to start the AI analysis"),
        ("3️⃣", "Review Content", "Check quality scores, compare content, and review the draft"),
        ("4️⃣", "Approve/Edit", "Approve for publication or request changes with feedback"),
    ]
    
    cols = st.columns(4)
    for i, (icon, title, desc) in enumerate(steps):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2rem;">{icon}</div>
                <h4 style="margin: 10px 0 5px 0;">{title}</h4>
                <p style="color: #8b949e; font-size: 0.85rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick start tip
    st.info("👈 **Get Started:** Enter a competitor blog URL in the sidebar to begin!")


def render_pipeline_header(state: dict):
    """Render pipeline header with status and key metrics"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h2 style="margin: 0; color: #e6edf3;">Pipeline Review</h2>
            <p style="color: #8b949e; margin: 5px 0;">
                ID: <code>{st.session_state.current_pipeline_id[:12]}...</code>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(get_status_badge(state.get('status', 'unknown')), unsafe_allow_html=True)


def render_overview_tab(outputs: dict, state: dict):
    """Render overview tab with key metrics and summary"""
    
    # Key Metrics Row
    st.markdown("### 📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        stage = state.get('current_stage', 0)
        st.metric("Progress", f"{stage}/8 stages", delta=f"{int(stage/8*100)}%")
    
    with col2:
        safety = state.get('safety_decision', 'N/A')
        delta = "✓ Safe" if safety == 'GREEN' else ("⚠ Review" if safety == 'YELLOW' else "")
        st.metric("Safety Check", safety, delta=delta)
    
    with col3:
        quality = state.get('quality_score', 0)
        delta = "✓ Good" if quality and quality >= 60 else ("⚠ Low" if quality else None)
        st.metric("Quality Score", f"{quality:.1f}/100" if quality else "N/A", delta=delta)
    
    with col4:
        if 1 in outputs:
            word_count = outputs[1].get('word_count', 0)
            st.metric("Source Words", f"{word_count:,}")
        else:
            st.metric("Source Words", "N/A")
    
    st.markdown("---")
    
    # Source Article Info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📰 Source Article")
        if 1 in outputs:
            extraction = outputs[1]
            st.markdown(f"""
            <div class="info-card">
                <p><strong>URL:</strong> <a href="{extraction.get('source_url', '#')}" target="_blank">{extraction.get('source_url', 'N/A')[:50]}...</a></p>
                <p><strong>Word Count:</strong> {extraction.get('word_count', 0):,} words</p>
                <p><strong>Extraction:</strong> {extraction.get('extraction_method', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Source not extracted yet")
    
    with col2:
        st.markdown("### 🎯 Content Brief")
        if 2 in outputs:
            analysis = outputs[2]
            brief = analysis.get('content_brief', {})
            st.markdown(f"""
            <div class="info-card">
                <p><strong>Topic:</strong> {brief.get('target_topic', 'N/A')}</p>
                <p><strong>Keyword:</strong> {brief.get('primary_keyword', 'N/A')}</p>
                <p><strong>Audience:</strong> {brief.get('target_audience', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Content gaps
            gaps = brief.get('content_gaps', [])
            if gaps:
                with st.expander(f"💡 Content Gaps to Fill ({len(gaps)})"):
                    for gap in gaps:
                        st.markdown(f"• {gap}")
        else:
            st.warning("Analysis not complete yet")


def render_content_tab(outputs: dict):
    """Render content preview tab"""
    
    if 6 not in outputs:
        st.warning("⏳ Content not yet generated. Run the pipeline first!")
        return
    
    draft = outputs[6]
    content = draft.get('content', '')
    metadata = draft.get('metadata', {})
    
    # Metadata summary
    st.markdown("### 📋 Article Details")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Title:** {metadata.get('title', 'N/A')}")
    with col2:
        st.markdown(f"**Word Count:** {metadata.get('word_count', 0):,}")
    with col3:
        st.markdown(f"**Slug:** `{metadata.get('slug', 'N/A')}`")
    
    if metadata.get('meta_description'):
        st.caption(f"**Meta Description:** {metadata.get('meta_description', 'N/A')}")
    
    st.markdown("---")
    
    # Content display options
    view_mode = st.radio(
        "View Mode",
        ["📄 Rendered", "📝 Markdown", "🌐 HTML Preview"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_mode == "📄 Rendered":
        # Render markdown
        st.markdown(content)
    
    elif view_mode == "📝 Markdown":
        st.code(content, language="markdown")
    
    elif view_mode == "🌐 HTML Preview":
        if 8 in outputs:
            html_output = outputs[8]
            html_file = html_output.get('html_file', '')
            
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=700, scrolling=True)
            else:
                st.warning("HTML file not found")
        else:
            st.warning("HTML not yet generated")


def render_quality_tab(outputs: dict):
    """Render quality scores tab with visual indicators"""
    
    if 7 not in outputs:
        st.warning("⏳ Quality check not yet performed")
        return
    
    qa = outputs[7]
    quality_report = qa.get('quality_report', {})
    scores = quality_report.get('scores', {})
    
    # Overall Status Banner
    status = quality_report.get('overall_status', 'UNKNOWN')
    if status == 'PASS':
        st.success("### ✅ Quality Check Passed")
    else:
        st.error("### 🚫 Quality Check Blocked")
    
    st.markdown("---")
    
    # Main Scores with Progress Bars
    st.markdown("### 📊 Score Breakdown")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        seo_score = scores.get('seo_score', 0)
        st.markdown("**SEO Score**")
        st.progress(min(seo_score / 100, 1.0))
        st.markdown(f"<h2 style='text-align: center;'>{seo_score:.1f}<span style='font-size: 0.5em; color: #8b949e;'>/100</span></h2>", unsafe_allow_html=True)
        if seo_score >= 70:
            st.success("Excellent")
        elif seo_score >= 50:
            st.warning("Good")
        else:
            st.error("Needs Improvement")
    
    with col2:
        plag_sim = scores.get('plagiarism_max_similarity', 0)
        st.markdown("**Originality**")
        originality = 1 - plag_sim
        st.progress(min(originality, 1.0))
        st.markdown(f"<h2 style='text-align: center;'>{originality:.0%}</h2>", unsafe_allow_html=True)
        if plag_sim < 0.70:
            st.success("Highly Original")
        elif plag_sim < 0.85:
            st.warning("Acceptable")
        else:
            st.error("Too Similar")
    
    with col3:
        readability = scores.get('readability_score', 0)
        st.markdown("**Readability (Flesch)**")
        # Normalize readability to 0-100 scale for progress (ideal is 50-70)
        read_progress = min(max(readability / 100, 0), 1)
        st.progress(read_progress)
        st.markdown(f"<h2 style='text-align: center;'>{readability:.1f}</h2>", unsafe_allow_html=True)
        if 40 <= readability <= 60:
            st.success("Ideal")
        elif 20 <= readability <= 80:
            st.warning("Acceptable")
        else:
            st.error("Out of Range")
    
    st.markdown("---")
    
    # Component Scores
    st.markdown("### 🎯 SEO Components")
    seo_analysis = qa.get('seo_analysis', {})
    component_scores = seo_analysis.get('component_scores', {})
    
    components = [
        ("Keyword Optimization", component_scores.get('keyword_optimization', 0), "🔑"),
        ("Structure", component_scores.get('structure', 0), "🏗️"),
        ("Readability", component_scores.get('readability', 0), "📖"),
        ("Content Length", component_scores.get('content_length', 0), "📏"),
        ("Internal Linking", component_scores.get('internal_linking', 0), "🔗"),
        ("Meta Optimization", component_scores.get('meta_optimization', 0), "🏷️"),
    ]
    
    cols = st.columns(6)
    for i, (name, score, icon) in enumerate(components):
        with cols[i]:
            color = "#238636" if score >= 70 else ("#9e6a03" if score >= 40 else "#da3633")
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 1.5rem;">{icon}</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: {color};">{score:.0f}</div>
                <div style="font-size: 0.75rem; color: #8b949e;">{name}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Issues and Recommendations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚫 Blocking Issues")
        blocking = quality_report.get('blocking_issues', [])
        if blocking:
            for issue in blocking:
                st.error(f"• {issue}")
        else:
            st.success("No blocking issues! ✓")
    
    with col2:
        st.markdown("### ⚠️ Warnings")
        warnings = quality_report.get('warnings', [])
        if warnings:
            for warning in warnings:
                st.warning(f"• {warning}")
        else:
            st.success("No warnings! ✓")
    
    # Recommendations
    recommendations = quality_report.get('recommendations', [])
    if recommendations:
        st.markdown("### 💡 Recommendations")
        for rec in recommendations:
            st.info(f"→ {rec}")


def render_comparison_tab(outputs: dict):
    """Render side-by-side comparison tab"""
    
    if 1 not in outputs or 6 not in outputs:
        st.warning("⏳ Both competitor and generated content required for comparison")
        return
    
    # View options
    view_mode = st.radio(
        "Display Mode",
        ["📄 Side by Side", "📊 Diff View"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Get content
    pipeline_id = st.session_state.current_pipeline_id
    extraction_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'extractions',
        f"{pipeline_id}.md"
    )
    
    if os.path.exists(extraction_file):
        with open(extraction_file, 'r', encoding='utf-8') as f:
            competitor_content = f.read()
    else:
        competitor_content = "Competitor content not found"
    
    draft = outputs[6]
    sendmarc_content = draft.get('content', '')
    
    if view_mode == "📄 Side by Side":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏢 Competitor Content")
            st.markdown(f"<div style='color: #8b949e; font-size: 0.85rem; margin-bottom: 10px;'>{len(competitor_content.split())} words</div>", unsafe_allow_html=True)
            with st.container(height=600):
                st.markdown(competitor_content)
        
        with col2:
            st.markdown("### ✉️ Sendmarc Content")
            st.markdown(f"<div style='color: #8b949e; font-size: 0.85rem; margin-bottom: 10px;'>{len(sendmarc_content.split())} words</div>", unsafe_allow_html=True)
            with st.container(height=600):
                st.markdown(sendmarc_content)
    
    else:  # Diff View
        st.markdown("### 📊 Content Comparison")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Competitor Words", len(competitor_content.split()))
        with col2:
            st.metric("Sendmarc Words", len(sendmarc_content.split()))
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Competitor", "Sendmarc"])
        with tab1:
            st.markdown(competitor_content)
        with tab2:
            st.markdown(sendmarc_content)


def render_stages_tab(outputs: dict):
    """Render stage outputs tab with timeline view"""
    
    st.markdown("### 🔧 Pipeline Stages")
    
    stage_info = [
        (1, "Content Extraction", "Extract and clean content from source URL", "🔍"),
        (2, "Content Analysis", "Analyze topics, keywords, and content gaps", "📊"),
        (3, "Safety Gate", "Check for copyright and safety risks", "🛡️"),
        (5, "Outline Generation", "Create article structure and outline", "📝"),
        (6, "Draft Generation", "Generate full article content", "✍️"),
        (7, "Quality Assurance", "SEO, plagiarism, and readability checks", "✅"),
        (8, "HTML Formatting", "Format as production-ready HTML", "🌐"),
    ]
    
    for stage_num, name, desc, icon in stage_info:
        if stage_num in outputs:
            output = outputs[stage_num]
            success = output.get('success', False)
            
            status_icon = "✅" if success else "❌"
            status_color = "#238636" if success else "#da3633"
            
            with st.expander(f"{icon} Stage {stage_num}: {name} {status_icon}"):
                st.caption(desc)
                
                if success:
                    st.success("Completed successfully")
                else:
                    st.error(f"Failed: {output.get('error', 'Unknown error')}")
                
                # Show key output info based on stage
                if stage_num == 1 and success:
                    st.metric("Words Extracted", output.get('word_count', 0))
                elif stage_num == 2 and success:
                    brief = output.get('content_brief', {})
                    st.write(f"**Topic:** {brief.get('target_topic', 'N/A')}")
                elif stage_num == 3 and success:
                    decision = output.get('decision', {})
                    st.write(f"**Risk Level:** {decision.get('risk_level', 'N/A')}")
                elif stage_num == 7 and success:
                    report = output.get('quality_report', {})
                    st.metric("SEO Score", f"{report.get('scores', {}).get('seo_score', 0):.1f}/100")
                
                # Raw JSON in nested expander
                with st.expander("View Raw Output"):
                    st.json(output)
        else:
            st.markdown(f"""
            <div style="padding: 10px; background: #21262d; border-radius: 8px; margin: 5px 0; opacity: 0.5;">
                {icon} Stage {stage_num}: {name} — <span style="color: #8b949e;">Not yet executed</span>
            </div>
            """, unsafe_allow_html=True)


def regenerate_with_feedback(pipeline_id: str, feedback: str):
    """Regenerate content with user feedback"""
    from stages import stage5_outline, stage6_generate, stage7_qa, stage8_format
    
    try:
        outputs = get_pipeline_outputs(pipeline_id)
        if 2 not in outputs:
            return False, "Missing analysis output from Stage 2"
        
        analysis_output = outputs[2]
        brief = analysis_output.get('content_brief', {})
        brief['user_feedback'] = feedback
        brief['regeneration_instructions'] = f"USER FEEDBACK TO INCORPORATE: {feedback}"
        
        progress = st.progress(0, text="Starting regeneration...")
        
        progress.progress(20, text="Regenerating outline...")
        stage5_output = stage5_outline.run(pipeline_id, analysis_output)
        if not stage5_output.get('success'):
            return False, f"Stage 5 failed: {stage5_output.get('error')}"
        db.save_stage_output(pipeline_id, 5, stage5_output)
        
        progress.progress(50, text="Generating new content...")
        stage6_output = stage6_generate.run(pipeline_id, stage5_output, analysis_output)
        if not stage6_output.get('success'):
            return False, f"Stage 6 failed: {stage6_output.get('error')}"
        db.save_stage_output(pipeline_id, 6, stage6_output)
        
        progress.progress(75, text="Running quality checks...")
        stage7_output = stage7_qa.run(pipeline_id, stage6_output)
        if not stage7_output.get('success'):
            return False, f"Stage 7 failed: {stage7_output.get('error')}"
        db.save_stage_output(pipeline_id, 7, stage7_output)
        
        progress.progress(90, text="Formatting output...")
        stage8_output = stage8_format.run(pipeline_id, stage6_output, stage7_output)
        if not stage8_output.get('success'):
            return False, f"Stage 8 failed: {stage8_output.get('error')}"
        db.save_stage_output(pipeline_id, 8, stage8_output)
        
        quality_score = stage7_output['quality_report']['scores']['seo_score']
        db.update_pipeline_status(pipeline_id, 'review_required', quality_score=quality_score)
        
        progress.progress(100, text="Complete!")
        
        return True, "Content regenerated successfully!"
        
    except Exception as e:
        return False, str(e)


def render_approval_actions(pipeline_id: str, outputs: dict):
    """Render approval action buttons"""
    
    st.markdown("---")
    st.markdown("### 🎯 Review Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Approve", type="primary", use_container_width=True, help="Approve for publication"):
            db.update_pipeline_status(pipeline_id, 'approved')
            db.log_audit_event(pipeline_id, 'approved', metadata={'reviewer': 'dashboard_user'}, reviewer='dashboard_user')
            st.success("✅ Content approved for publication!")
            st.balloons()
    
    with col2:
        if st.button("🔄 Request Changes", use_container_width=True, help="Regenerate with feedback"):
            st.session_state.show_feedback_form = not st.session_state.show_feedback_form
            st.session_state.show_reject_form = False
    
    with col3:
        if st.button("❌ Reject", use_container_width=True, help="Reject this content"):
            st.session_state.show_reject_form = not st.session_state.show_reject_form
            st.session_state.show_feedback_form = False
    
    # Feedback form
    if st.session_state.show_feedback_form:
        st.markdown("---")
        st.markdown("### 🔄 Request Changes")
        st.caption("Provide feedback to regenerate the content with improvements")
        
        feedback = st.text_area(
            "Your feedback",
            placeholder="E.g., 'Make the introduction more engaging', 'Add more examples', 'Simplify technical terms'...",
            height=100,
            key="feedback_input",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Regenerate", type="primary", use_container_width=True):
                if feedback:
                    db.log_audit_event(pipeline_id, 'changes_requested', metadata={'feedback': feedback}, reviewer='dashboard_user')
                    success, message = regenerate_with_feedback(pipeline_id, feedback)
                    if success:
                        st.success(message)
                        st.session_state.pipeline_outputs = get_pipeline_outputs(pipeline_id)
                        st.session_state.show_feedback_form = False
                        st.rerun()
                    else:
                        st.error(f"Failed: {message}")
                else:
                    st.warning("Please provide feedback first")
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_feedback_form = False
                st.rerun()
    
    # Reject form
    if st.session_state.show_reject_form:
        st.markdown("---")
        st.markdown("### ❌ Reject Content")
        
        reason = st.text_area(
            "Rejection reason",
            placeholder="Explain why this content should be rejected...",
            height=100,
            key="reject_input",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Reject", type="primary", use_container_width=True):
                if reason:
                    db.update_pipeline_status(pipeline_id, 'rejected')
                    db.log_audit_event(pipeline_id, 'rejected', metadata={'reason': reason}, reviewer='dashboard_user')
                    st.error("Content rejected")
                    st.session_state.show_reject_form = False
                else:
                    st.warning("Please provide a reason")
        with col2:
            if st.button("Cancel ", use_container_width=True):
                st.session_state.show_reject_form = False
                st.rerun()


def main():
    """Main dashboard application"""
    
    # Initialize
    db.init_database()
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    pipeline_id = st.session_state.current_pipeline_id
    outputs = st.session_state.pipeline_outputs
    
    if not pipeline_id:
        render_welcome()
        return
    
    # Get pipeline state
    state = db.get_pipeline_state(pipeline_id)
    
    if not state or not outputs:
        st.error("Failed to load pipeline data")
        return
    
    # Pipeline header
    render_pipeline_header(state)
    
    # Main tabs
    tabs = st.tabs([
        "📊 Overview",
        "📝 Content",
        "✅ Quality",
        "🔄 Compare",
        "🔧 Stages"
    ])
    
    with tabs[0]:
        render_overview_tab(outputs, state)
    
    with tabs[1]:
        render_content_tab(outputs)
    
    with tabs[2]:
        render_quality_tab(outputs)
    
    with tabs[3]:
        render_comparison_tab(outputs)
    
    with tabs[4]:
        render_stages_tab(outputs)
    
    # Approval actions
    if state['status'] in ['completed', 'review_required']:
        render_approval_actions(pipeline_id, outputs)


if __name__ == '__main__':
    main()
