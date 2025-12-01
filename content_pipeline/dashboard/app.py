"""
Streamlit Dashboard for Content Pipeline Review
Human review interface for approving generated content
"""
import os
import sys
import streamlit as st
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import db
from main import run_pipeline, get_pipeline_outputs


st.set_page_config(
    page_title="Sendmarc Content Pipeline",
    page_icon="📝",
    layout="wide"
)


def init_session_state():
    """Initialize session state variables"""
    if 'current_pipeline_id' not in st.session_state:
        st.session_state.current_pipeline_id = None
    if 'pipeline_outputs' not in st.session_state:
        st.session_state.pipeline_outputs = None


def run_new_pipeline():
    """Run a new pipeline from URL"""
    url = st.session_state.get('url_input', '')
    
    if not url:
        st.error("Please enter a URL")
        return
    
    with st.spinner("Running content pipeline... This may take several minutes."):
        try:
            pipeline_id = run_pipeline(url)
            st.session_state.current_pipeline_id = pipeline_id
            st.session_state.pipeline_outputs = get_pipeline_outputs(pipeline_id)
            st.success(f"Pipeline completed! ID: {pipeline_id}")
        except Exception as e:
            st.error(f"Pipeline failed: {str(e)}")


def load_pipeline(pipeline_id: str):
    """Load an existing pipeline"""
    try:
        st.session_state.current_pipeline_id = pipeline_id
        st.session_state.pipeline_outputs = get_pipeline_outputs(pipeline_id)
        st.success(f"Loaded pipeline: {pipeline_id}")
    except Exception as e:
        st.error(f"Failed to load pipeline: {str(e)}")


def render_sidebar():
    """Render sidebar with pipeline controls"""
    st.sidebar.title("🚀 Content Pipeline")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Run New Pipeline")
    
    url = st.sidebar.text_input(
        "Competitor Blog URL",
        key="url_input",
        placeholder="https://example.com/blog/article"
    )
    
    if st.sidebar.button("▶️ Run Pipeline", type="primary"):
        run_new_pipeline()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Load Existing Pipeline")
    
    # List recent pipelines
    pipelines = db.list_pipelines(limit=10)
    
    if pipelines:
        for pipeline in pipelines:
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.text(f"{pipeline['id'][:8]}... ({pipeline['status']})")
            with col2:
                if st.button("📂", key=f"load_{pipeline['id']}"):
                    load_pipeline(pipeline['id'])
    else:
        st.sidebar.info("No pipelines yet. Run one above!")


def render_overview_tab(outputs: dict, state: dict):
    """Render overview tab"""
    st.header("📊 Pipeline Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Status", state.get('status', 'unknown').upper())
    
    with col2:
        st.metric("Current Stage", f"{state.get('current_stage', 0)}/8")
    
    with col3:
        safety = state.get('safety_decision', 'N/A')
        st.metric("Safety", safety, delta=None if safety == 'GREEN' else "Review Needed")
    
    with col4:
        quality = state.get('quality_score', 0)
        st.metric("Quality Score", f"{quality:.1f}/100" if quality else "N/A")
    
    st.markdown("---")
    
    # Source info
    if 1 in outputs:
        st.subheader("Source Article")
        extraction = outputs[1]
        st.write(f"**URL:** {extraction.get('source_url', 'N/A')}")
        st.write(f"**Word Count:** {extraction.get('word_count', 0)}")
        st.write(f"**Extraction Method:** {extraction.get('extraction_method', 'N/A')}")
    
    # Content brief
    if 2 in outputs:
        st.subheader("Content Brief")
        analysis = outputs[2]
        brief = analysis.get('content_brief', {})
        
        st.write(f"**Target Topic:** {brief.get('target_topic', 'N/A')}")
        st.write(f"**Primary Keyword:** {brief.get('primary_keyword', 'N/A')}")
        st.write(f"**Target Audience:** {brief.get('target_audience', 'N/A')}")
        
        if brief.get('content_gaps'):
            with st.expander("Content Gaps to Fill"):
                for gap in brief['content_gaps']:
                    st.write(f"- {gap}")


def render_content_tab(outputs: dict):
    """Render content preview tab"""
    st.header("📝 Generated Content")
    
    if 6 not in outputs:
        st.warning("Content not yet generated")
        return
    
    draft = outputs[6]
    content = draft.get('content', '')
    metadata = draft.get('metadata', {})
    
    # Metadata
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Article Metadata")
        st.write(f"**Title:** {metadata.get('title', 'N/A')}")
        st.write(f"**Word Count:** {metadata.get('word_count', 0)}")
    
    with col2:
        st.write(f"**Slug:** {metadata.get('slug', 'N/A')}")
        st.write(f"**Meta Description:**")
        st.caption(metadata.get('meta_description', 'N/A'))
    
    st.markdown("---")
    
    # Content tabs
    content_tab, html_tab = st.tabs(["📄 Markdown", "🌐 HTML Preview"])
    
    with content_tab:
        st.text_area("Generated Content", content, height=500)
    
    with html_tab:
        if 8 in outputs:
            html_output = outputs[8]
            html_file = html_output.get('html_file', '')
            
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=600, scrolling=True)
            else:
                st.warning("HTML file not found")
        else:
            st.warning("HTML not yet generated")


def render_quality_tab(outputs: dict):
    """Render quality scores tab"""
    st.header("✅ Quality Assurance")
    
    if 7 not in outputs:
        st.warning("Quality check not yet performed")
        return
    
    qa = outputs[7]
    quality_report = qa.get('quality_report', {})
    
    # Overall status
    status = quality_report.get('overall_status', 'UNKNOWN')
    
    if status == 'PASS':
        st.success("✅ Quality Check PASSED")
    else:
        st.error("🛑 Quality Check BLOCKED")
    
    # Scores
    st.subheader("Scores")
    col1, col2, col3 = st.columns(3)
    
    scores = quality_report.get('scores', {})
    
    with col1:
        seo_score = scores.get('seo_score', 0)
        st.metric("SEO Score", f"{seo_score:.1f}/100")
        
        if seo_score >= 70:
            st.success("Excellent")
        elif seo_score >= 50:
            st.warning("Good")
        else:
            st.error("Needs Improvement")
    
    with col2:
        plag_sim = scores.get('plagiarism_max_similarity', 0)
        st.metric("Max Plagiarism Similarity", f"{plag_sim:.1%}")
        
        if plag_sim < 0.70:
            st.success("Low")
        elif plag_sim < 0.85:
            st.warning("Medium")
        else:
            st.error("High")
    
    with col3:
        readability = scores.get('readability_score', 0)
        st.metric("Readability (Flesch)", f"{readability:.1f}")
        
        if 50 <= readability <= 70:
            st.success("Ideal")
        elif 30 <= readability <= 80:
            st.warning("Acceptable")
        else:
            st.error("Out of Range")
    
    # SEO Component Scores
    st.subheader("SEO Component Scores")
    seo_analysis = qa.get('seo_analysis', {})
    component_scores = seo_analysis.get('component_scores', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Keyword Optimization", f"{component_scores.get('keyword_optimization', 0):.1f}")
        st.metric("Structure", f"{component_scores.get('structure', 0):.1f}")
    
    with col2:
        st.metric("Readability", f"{component_scores.get('readability', 0):.1f}")
        st.metric("Content Length", f"{component_scores.get('content_length', 0):.1f}")
    
    with col3:
        st.metric("Internal Linking", f"{component_scores.get('internal_linking', 0):.1f}")
        st.metric("Meta Optimization", f"{component_scores.get('meta_optimization', 0):.1f}")
    
    # Issues
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛑 Blocking Issues")
        blocking = quality_report.get('blocking_issues', [])
        if blocking:
            for issue in blocking:
                st.error(issue)
        else:
            st.success("No blocking issues")
    
    with col2:
        st.subheader("⚠️ Warnings")
        warnings = quality_report.get('warnings', [])
        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.success("No warnings")
    
    # Recommendations
    if quality_report.get('recommendations'):
        st.subheader("💡 Recommendations")
        for rec in quality_report['recommendations']:
            st.info(rec)


def render_comparison_tab(outputs: dict):
    """Render side-by-side comparison tab"""
    st.header("🔄 Competitor vs Sendmarc")
    
    if 1 not in outputs or 6 not in outputs:
        st.warning("Both competitor and generated content required")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Competitor Content")
        
        extraction = outputs[1]
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
            st.text_area("Competitor", competitor_content[:2000] + "...", height=400)
        else:
            st.warning("Competitor content file not found")
    
    with col2:
        st.subheader("Sendmarc Content")
        
        draft = outputs[6]
        content = draft.get('content', '')
        st.text_area("Sendmarc", content[:2000] + "...", height=400)


def render_stages_tab(outputs: dict):
    """Render stage outputs tab"""
    st.header("🔧 Stage-by-Stage Outputs")
    
    stage_names = {
        1: "Content Extraction",
        2: "Content Intelligence Analysis",
        3: "Safety & Ethics Gate",
        4: "Brand Voice RAG",
        5: "Outline Generation",
        6: "Full Draft Generation",
        7: "Quality Assurance",
        8: "HTML Formatting"
    }
    
    for stage_num in sorted(outputs.keys()):
        stage_name = stage_names.get(stage_num, f"Stage {stage_num}")
        
        with st.expander(f"Stage {stage_num}: {stage_name}"):
            output = outputs[stage_num]
            
            if output.get('success'):
                st.success("✅ Success")
            else:
                st.error(f"❌ Failed: {output.get('error', 'Unknown error')}")
            
            st.json(output)


def render_approval_actions(pipeline_id: str, outputs: dict):
    """Render approval action buttons"""
    st.markdown("---")
    st.header("🎯 Approval Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Approve for Publication", type="primary", use_container_width=True):
            db.update_pipeline_status(pipeline_id, 'approved')
            db.log_audit_event(
                pipeline_id,
                'approved',
                metadata={'reviewer': 'dashboard_user'},
                reviewer='dashboard_user'
            )
            st.success("Content approved! Ready for publication.")
            st.balloons()
    
    with col2:
        if st.button("🔄 Request Changes", use_container_width=True):
            feedback = st.text_area("Provide feedback for regeneration")
            if feedback:
                db.update_pipeline_status(pipeline_id, 'changes_requested')
                db.log_audit_event(
                    pipeline_id,
                    'changes_requested',
                    metadata={'feedback': feedback, 'reviewer': 'dashboard_user'},
                    reviewer='dashboard_user'
                )
                st.info("Changes requested. Feedback logged for regeneration.")
    
    with col3:
        if st.button("❌ Reject", use_container_width=True):
            reason = st.text_area("Rejection reason")
            if reason:
                db.update_pipeline_status(pipeline_id, 'rejected')
                db.log_audit_event(
                    pipeline_id,
                    'rejected',
                    metadata={'reason': reason, 'reviewer': 'dashboard_user'},
                    reviewer='dashboard_user'
                )
                st.error("Content rejected. Logged for analytics.")


def main():
    """Main dashboard application"""
    st.title("📝 Sendmarc Content Intelligence Pipeline")
    st.caption("MVP Review Dashboard")
    
    # Initialize database
    db.init_database()
    
    # Initialize session state
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    pipeline_id = st.session_state.current_pipeline_id
    outputs = st.session_state.pipeline_outputs
    
    if not pipeline_id:
        st.info("👈 Enter a competitor URL in the sidebar to start a new pipeline, or load an existing one.")
        
        # Show instructions
        st.markdown("""
        ## How to Use This Dashboard
        
        1. **Run New Pipeline:** Enter a competitor blog URL in the sidebar and click "Run Pipeline"
        2. **Review Content:** Use the tabs to review generated content, quality scores, and comparisons
        3. **Approve or Reject:** Use the approval actions at the bottom of the review page
        
        ## Pipeline Stages
        
        1. Content Extraction
        2. Content Intelligence Analysis  
        3. Safety & Ethics Gate
        4. Brand Voice RAG Setup
        5. Outline Generation
        6. Full Draft Generation
        7. Quality Assurance
        8. HTML Formatting
        9. Human Review (You are here!)
        """)
        
        return
    
    # Get pipeline state
    state = db.get_pipeline_state(pipeline_id)
    
    if not state or not outputs:
        st.error("Failed to load pipeline data")
        return
    
    # Render tabs
    tabs = st.tabs([
        "📊 Overview",
        "📝 Content",
        "✅ Quality",
        "🔄 Comparison",
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
    
    # Approval actions (only if pipeline is complete and not already approved/rejected)
    if state['status'] in ['completed', 'review_required']:
        render_approval_actions(pipeline_id, outputs)


if __name__ == '__main__':
    main()

