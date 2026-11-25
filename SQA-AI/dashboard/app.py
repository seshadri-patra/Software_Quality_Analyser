"""
SQA-AI Dashboard - Enhanced Professional UI
Version 2.5 - All Fixes Applied

Fixes:
- ✅ Lavender background theme
- ✅ Page headings now visible (dark text)
- ✅ Sidebar logo visible (dark text)
- ✅ Quick Help text visible (dark/black)
- ✅ Health vs Risk dynamic message
- ✅ Trend prediction message clarified
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="SQA-AI Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    .stMetric {
        background-color: #EDE9FE;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #7C3AED;
    }
    
    .section-header {
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        font-size: 1.2rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
    }
    
    .success-box {
        background: #D1FAE5;
        border: 2px solid #10B981;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .success-box h3, .success-box strong { color: #065F46; }
    .success-box p, .success-box span { color: #065F46; font-weight: 500; }
    
    .warning-box {
        background: #FEF3C7;
        border: 2px solid #D97706;
        padding: 15px;
        border-radius: 8px;
    }
    .warning-box h4, .warning-box strong { color: #78350F; }
    .warning-box p, .warning-box span { color: #78350F; font-weight: 500; }
    
    .info-box {
        background: #DBEAFE;
        border: 2px solid #3B82F6;
        padding: 15px;
        border-radius: 8px;
    }
    .info-box h4, .info-box strong { color: #1E3A8A; }
    .info-box p, .info-box span { color: #1E3A8A; font-weight: 500; }
    
    .error-box {
        background: #FEE2E2;
        border: 2px solid #EF4444;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .error-box strong { color: #7F1D1D; }
    .error-box span { color: #991B1B; font-weight: 500; }
    
    .action-card {
        padding: 20px;
        border-radius: 10px;
        height: 120px;
        border: 2px solid transparent;
        transition: all 0.2s ease;
    }
    .action-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .action-card h4 { color: #0F172A; margin: 0 0 10px 0; }
    .action-card p { color: #334155; margin: 0; font-size: 0.9rem; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stMarkdown p { color: #1E293B; }
    .stDataFrame { border: 1px solid #DDD6FE; border-radius: 8px; }
    
    /* Sidebar text visibility */
    [data-testid="stSidebar"] .stMarkdown p { color: #1E293B; }
    [data-testid="stSidebar"] label { color: #1E293B !important; }
</style>
""", unsafe_allow_html=True)

from database.db_manager import DBManager
from dashboard.components import (
    render_progress_cards,
    render_health_gauge_large,
    render_rich_file_table,
    render_trend_dashboard,
    render_file_deep_dive_panel,
    render_recommendations_panel,
    render_risk_overview_chart,
    render_project_stats_bar,
    render_trust_stats_bar,
    check_dependencies
)

HISTORY_LIMIT_OVERVIEW = 30
HISTORY_LIMIT_TRENDS = 30
MAX_HIGH_RISK_DISPLAY = 10
MAX_RECOMMENDATIONS = 50

COLORS = {
    'primary': '#4F46E5',
    'secondary': '#7C3AED',
    'success': '#059669',
    'warning': '#D97706',
    'danger': '#DC2626',
    'info': '#2563EB',
    'text_dark': '#0F172A',
    'text_medium': '#334155',
    'text_light': '#64748B',
    'bg_light': '#F5F3FF',
    'border': '#DDD6FE',
}

if 'db' not in st.session_state:
    st.session_state.db = DBManager()
if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None


def section_header(title: str, icon: str = "📊"):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)


def render_sidebar():
    """Enhanced sidebar - FIXED: Dark text on lavender background"""

    # Logo - FIXED: Dark text (not white)
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #3730A3; margin: 0;">🛡️ SQA-AI</h1>
        <p style="color: #4338CA; font-size: 0.9rem; margin: 5px 0; font-weight: 500;">
            Code Quality Analytics
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.divider()
    st.sidebar.markdown("### 📁 Project")

    try:
        projects = st.session_state.db.get_all_projects()
    except Exception as e:
        st.sidebar.error(f"Database error: {e}")
        return "Overview"

    if projects:
        opts = {p.name: p.project_id for p in projects}
        choice = st.sidebar.selectbox(
            "Select Project",
            list(opts.keys()),
            label_visibility="collapsed"
        )
        st.session_state.selected_project = opts[choice]

        try:
            summary = st.session_state.db.get_project_summary(opts[choice])
            if summary:
                st.sidebar.markdown(f"""
                <div style="background: #EDE9FE; padding: 12px; border-radius: 8px; 
                            margin: 10px 0; border: 1px solid #DDD6FE;">
                    <small style="color: #3730A3;">
                        📄 <b>{summary.get('total_files', 0)}</b> files &nbsp;|&nbsp; 
                        📝 <b>{summary.get('total_sloc', 0):,}</b> lines
                    </small>
                </div>
                """, unsafe_allow_html=True)
        except:
            pass
    else:
        st.sidebar.warning("⚠️ No projects found")
        st.sidebar.info("Run `python main.py scan -p <path> -n <name>`")

    st.sidebar.divider()
    st.sidebar.markdown("### 🧭 Navigation")

    pages = {
        "Overview": "🏠",
        "Files": "📁",
        "Trends": "📈",
        "Recommendations": "💡"
    }

    page = st.sidebar.radio(
        "Go to",
        list(pages.keys()),
        format_func=lambda x: f"{pages[x]} {x}",
        label_visibility="collapsed"
    )

    st.sidebar.divider()

    # Quick Help - FIXED: Black text
    with st.sidebar.expander("💡 Quick Help"):
        st.markdown("""
        <div style="color: #1E293B; font-size: 0.9rem; line-height: 1.8;">
            <b style="color: #3730A3;">Overview</b> - Project health at a glance<br>
            <b style="color: #3730A3;">Files</b> - Inspect individual files<br>
            <b style="color: #3730A3;">Trends</b> - Track progress over time<br>
            <b style="color: #3730A3;">Recommendations</b> - Action items to fix
        </div>
        """, unsafe_allow_html=True)

    # Version - FIXED: Visible color
    st.sidebar.markdown("""
    <div style="padding: 10px 0; color: #6D28D9; font-size: 0.8rem; font-weight: 500;">
        SQA-AI v2.5.0
    </div>
    """, unsafe_allow_html=True)

    return page


def page_overview():
    """Overview page - ALL FIXES APPLIED"""

    pid = st.session_state.selected_project
    if not pid:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <h2 style="color: #3730A3;">👋 Welcome to SQA-AI</h2>
            <p style="color: #4338CA; font-size: 1.1rem;">
                Select a project from the sidebar to get started
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    try:
        with st.spinner("Loading dashboard..."):
            summary = st.session_state.db.get_project_summary(pid)
            history = st.session_state.db.get_analysis_history(
                pid, limit=HISTORY_LIMIT_OVERVIEW
            )
            all_history = st.session_state.db.get_analysis_history(pid, limit=100)
            high_risk = st.session_state.db.get_high_risk_files(pid)
            latest = st.session_state.db.get_latest_analysis(pid)

            recs_count = 0
            if latest:
                recs = st.session_state.db.get_recommendations_with_file_info(
                    latest.analysis_id
                )
                recs_count = len(recs) if recs else 0

        current = history[0].to_dict() if len(history) > 0 else {}
        previous = history[1].to_dict() if len(history) > 1 else None

        # Page Title - FIXED: Dark purple text (visible on lavender)
        st.markdown(f"""
        <h1 style="margin-bottom: 5px; color: #3730A3; font-weight: 700;">
            📊 {summary.get('name', 'Project')} Dashboard
        </h1>
        <p style="color: #6D28D9; margin-bottom: 20px;">
            Last scan: {current.get('run_at', 'Never')[:16] 
            if current.get('run_at') else 'Never'}
        </p>
        """, unsafe_allow_html=True)

        # Trust Stats Bar
        total_scans = len(all_history)
        total_files = current.get('total_files', 0)
        total_sloc = current.get('total_sloc', 0)

        days_tracking = 0
        if all_history and len(all_history) > 0:
            try:
                first_scan = all_history[-1].to_dict()
                if first_scan.get('run_at'):
                    first_date = datetime.fromisoformat(
                        first_scan['run_at'].replace('Z', '+00:00')
                    )
                    days_tracking = (
                        datetime.now() - first_date.replace(tzinfo=None)
                    ).days
            except:
                days_tracking = 0

        render_trust_stats_bar(
            total_scans=total_scans,
            total_files=total_files,
            total_sloc=total_sloc,
            days_tracking=days_tracking,
            recommendations_count=recs_count
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Key Metrics
        section_header("Key Metrics", "📈")
        render_progress_cards(current, previous, total_scans)

        st.markdown("<br>", unsafe_allow_html=True)

        # Health + Risk
        col1, col2 = st.columns([1, 1.5], gap="large")

        with col1:
            section_header("Health Score", "🏥")
            fig = render_health_gauge_large(
                current.get('overall_health_score', 0),
                current.get('overall_status', 'unknown')
            )
            if fig:
                st.plotly_chart(
                    fig, 
                    use_container_width=True, 
                    config={'displayModeBar': False}
                )

            score = current.get('overall_health_score', 0)
            
            if score >= 80:
                st.markdown("""
                <div class="success-box">
                    <strong>✅ Excellent!</strong><br>
                    <span>Your codebase is in great shape.</span>
                </div>
                """, unsafe_allow_html=True)
            elif score >= 60:
                st.markdown("""
                <div class="info-box">
                    <strong>👍 Good</strong><br>
                    <span>Some improvements recommended.</span>
                </div>
                """, unsafe_allow_html=True)
            elif score >= 40:
                # FIXED: Dynamic message using actual high_risk data
                if high_risk and len(high_risk) > 0:
                    risk_msg = f"Review {len(high_risk)} high-risk file(s) below."
                else:
                    risk_msg = "Some areas need improvement."

                st.markdown(f"""
                <div class="warning-box">
                    <strong>⚠️ Needs Attention</strong><br>
                    <span>{risk_msg}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="error-box">
                    <strong>🚨 Critical</strong><br>
                    <span>Immediate action required.</span>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                section_header("High Risk Files", "⚠️")
                
                if high_risk:
                    # Only show HIGH + CRITICAL files (DDI >= 75)
                    fig = render_risk_overview_chart(high_risk[:MAX_HIGH_RISK_DISPLAY])
                    if fig:
                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            config={'displayModeBar': False}
                        )
                    # Show count caption
                    st.caption(
                        f"⚠️ Showing {len(high_risk)} file(s) with DDI ≥ 75 "
                        f"(High/Critical risk only)"
                    )
                else:
                    st.markdown("""
                    <div class="success-box">
                        <h3 style="color: #065F46; margin: 0;">
                            🎉 No High Risk Files!
                        </h3>
                        <p style="margin: 10px 0 0 0;">
                            No files with DDI ≥ 75. Your codebase is looking healthy.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # Project Statistics
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Project Statistics", "📋")
        render_project_stats_bar(current)

        # What's Next
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("What's Next?", "🎯")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="action-card" style="background: #DBEAFE; border-color: #BFDBFE;">
                <h4>📁 Inspect Files</h4>
                <p>Deep dive into individual files to understand their quality.</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            recs_text = (f"{recs_count} action items" 
                        if recs_count > 0 else "No issues found")
            recs_bg = "#FEF3C7" if recs_count > 0 else "#D1FAE5"
            recs_border = "#FDE68A" if recs_count > 0 else "#A7F3D0"
            st.markdown(f"""
            <div class="action-card" 
                 style="background: {recs_bg}; border-color: {recs_border};">
                <h4>💡 Recommendations</h4>
                <p>{recs_text} to improve your code quality.</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            trend_text = (
                "Track your improvement over time" 
                if total_scans >= 2 
                else f"Run {2 - total_scans} more scan(s) to see trends"
            )
            st.markdown(f"""
            <div class="action-card" 
                 style="background: #F5F3FF; border-color: #DDD6FE;">
                <h4>📈 View Trends</h4>
                <p>{trend_text}</p>
            </div>
            """, unsafe_allow_html=True)

        # Trend Prediction
        try:
            from core.trend_analyzer import TrendAnalyzer

            if len(all_history) >= 3:
                st.markdown("<br>", unsafe_allow_html=True)
                section_header("Trend Prediction", "🔮")

                analyzer = TrendAnalyzer()
                history_dicts = [h.to_dict() for h in all_history]
                trend_result = analyzer.analyze_history(history_dicts)

                if trend_result.get('has_sufficient_data'):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "30-Day Prediction",
                            f"{trend_result['predicted_30d']:.1f}",
                            f"{trend_result['slope_per_month']:+.1f}/month",
                            delta_color="inverse"
                        )
                    with col2:
                        days_crit = trend_result['days_until_critical']
                        st.metric(
                            "Days Until Critical",
                            days_crit if days_crit > 0 else "N/A"
                        )
                    with col3:
                        st.metric(
                            "Trend",
                            trend_result['trend'].replace('_', ' ').title()
                        )

                    st.info(trend_result['recommendation'])
                else:
                    st.info(
                        "📊 Scan on different days to see trend predictions."
                    )
        except ImportError:
            pass
        except Exception:
            pass

    except Exception as e:
        st.error(f"❌ Error loading overview: {str(e)}")
        st.info("Try refreshing the page or running a new scan.")
        with st.expander("🔧 Debug Information"):
            st.code(str(e))


def page_files():
    """File inspector page - FIXED HEADING"""

    pid = st.session_state.selected_project
    if not pid:
        st.info("👈 Please select a project from the sidebar.")
        return

    # FIXED: Dark purple heading
    st.markdown("""
    <h1 style="margin-bottom: 5px; color: #3730A3; font-weight: 700;">
        📁 File Inspector
    </h1>
    <p style="color: #6D28D9; margin-bottom: 20px;">
        Explore and analyze individual files
    </p>
    """, unsafe_allow_html=True)

    try:
        with st.spinner("Loading files..."):
            data = st.session_state.db.get_dashboard_data(pid)

        files = data.get('files', [])

        if not files:
            st.warning("📭 No files found. Run a scan first.")
            return

        section_header("Search & Filter", "🔍")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            query = st.text_input(
                "Search files",
                placeholder="Type filename to search...",
                label_visibility="collapsed"
            )
        with col2:
            risk_filter = st.selectbox(
                "Risk Level",
                ["All", "Critical", "High", "Medium", "Low"],
                label_visibility="collapsed"
            )
        with col3:
            sort_by = st.selectbox(
                "Sort By",
                ["DDI Score (High→Low)", "DDI Score (Low→High)", 
                 "Complexity", "Name"],
                label_visibility="collapsed"
            )

        filtered_files = files.copy()

        if query:
            filtered_files = [
                f for f in filtered_files
                if query.lower() in f['file']['filename'].lower()
            ]

        if risk_filter != "All":
            filtered_files = [
                f for f in filtered_files
                if f['ddi'].get('risk_level', '').lower() == risk_filter.lower()
            ]

        if sort_by == "DDI Score (High→Low)":
            filtered_files.sort(
                key=lambda x: x['ddi'].get('ddi_score', 0), reverse=True
            )
        elif sort_by == "DDI Score (Low→High)":
            filtered_files.sort(key=lambda x: x['ddi'].get('ddi_score', 0))
        elif sort_by == "Complexity":
            filtered_files.sort(
                key=lambda x: x['metrics'].get('cyclomatic_complexity', 0),
                reverse=True
            )
        else:
            filtered_files.sort(key=lambda x: x['file']['filename'])

        st.caption(f"Showing {len(filtered_files)} of {len(files)} files")

        section_header(f"Files ({len(filtered_files)})", "📄")
        render_rich_file_table(filtered_files)

        if filtered_files:
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("File Deep Dive", "🔬")

            file_options = {f['file']['filename']: f for f in filtered_files}

            selected_name = st.selectbox(
                "Select a file to analyze in detail",
                list(file_options.keys()),
                format_func=lambda x: (
                    f"{x} (DDI: {file_options[x]['ddi'].get('ddi_score', 0):.1f})"
                )
            )

            if selected_name:
                target = file_options[selected_name]
                render_file_deep_dive_panel(
                    target['file'],
                    target['metrics'],
                    target['ddi']
                )

    except Exception as e:
        st.error(f"❌ Error loading files: {str(e)}")


def page_trends():
    """Trends page - FIXED HEADING"""

    pid = st.session_state.selected_project
    if not pid:
        st.info("👈 Please select a project from the sidebar.")
        return

    # FIXED: Dark purple heading
    st.markdown("""
    <h1 style="margin-bottom: 5px; color: #3730A3; font-weight: 700;">
        📈 Trends & Evolution
    </h1>
    <p style="color: #6D28D9; margin-bottom: 20px;">
        Track your code quality progress over time
    </p>
    """, unsafe_allow_html=True)

    try:
        with st.spinner("Loading history..."):
            history = st.session_state.db.get_analysis_history(
                pid, limit=HISTORY_LIMIT_TRENDS
            )

        history_dicts = [h.to_dict() for h in history]

        if len(history_dicts) < 2:
            st.markdown("""
            <div style="text-align: center; padding: 60px 20px; 
                        background: #EDE9FE; border-radius: 12px; 
                        border: 2px solid #DDD6FE;">
                <h2 style="color: #3730A3;">📊 Not Enough Data Yet</h2>
                <p style="color: #4338CA;">
                    Run scans on <b>different days</b> to see trends.
                </p>
                <br>
                <p style="color: #6D28D9; font-size: 0.9rem;">
                    💡 <b>Tip:</b> Your product analyzes Git history during 
                    each scan. Run 
                    <code>python main.py scan -p &lt;path&gt; -n &lt;name&gt;</code> 
                    on different days to build comparison data.
                </p>
            </div>
            """, unsafe_allow_html=True)
            return

        render_trend_dashboard(history_dicts)

        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Scan History", "📜")

        history_table = []
        for i, h in enumerate(history_dicts):
            delta_health = ""
            delta_ddi = ""
            trend_emoji = ""

            if i < len(history_dicts) - 1:
                prev = history_dicts[i + 1]
                dh = h['overall_health_score'] - prev['overall_health_score']
                dd = h['avg_ddi_score'] - prev['avg_ddi_score']

                if dh > 0:
                    delta_health = f"↑ +{dh:.1f}"
                    trend_emoji = "📈"
                elif dh < 0:
                    delta_health = f"↓ {dh:.1f}"
                    trend_emoji = "📉"
                else:
                    delta_health = "→ 0"
                    trend_emoji = "➡️"

                if dd < 0:
                    delta_ddi = f"↓ {dd:.1f} ✓"
                elif dd > 0:
                    delta_ddi = f"↑ +{dd:.1f}"
                else:
                    delta_ddi = "→ 0"

            history_table.append({
                "📅 Date": h['run_at'][:16] if h['run_at'] else "N/A",
                "🏥 Health": f"{h['overall_health_score']:.0f}/100",
                "Trend": trend_emoji,
                "Health Δ": delta_health,
                "☢️ DDI": f"{h['avg_ddi_score']:.1f}",
                "DDI Δ": delta_ddi,
                "📁 Files": h['total_files'],
                "Status": h['overall_status'].title(),
            })

        st.dataframe(history_table, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Error loading trends: {str(e)}")


def page_recommendations():
    """Recommendations page - FIXED HEADING"""

    pid = st.session_state.selected_project
    if not pid:
        st.info("👈 Please select a project from the sidebar.")
        return

    # FIXED: Dark purple heading
    st.markdown("""
    <h1 style="margin-bottom: 5px; color: #3730A3; font-weight: 700;">
        💡 Recommendations
    </h1>
    <p style="color: #6D28D9; margin-bottom: 20px;">
        Actionable items to improve your code quality
    </p>
    """, unsafe_allow_html=True)

    try:
        with st.spinner("Loading recommendations..."):
            latest = st.session_state.db.get_latest_analysis(pid)

        if not latest:
            st.info("📭 No analysis found. Run a scan to generate recommendations.")
            return

        recs = st.session_state.db.get_recommendations_with_file_info(
            latest.analysis_id
        )

        if not recs:
            st.markdown("""
            <div class="success-box">
                <h2 style="color: #065F46; margin: 0;">🎉 No Issues Found!</h2>
                <p style="margin: 10px 0 0 0;">Your codebase is in excellent shape.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        section_header("Issue Summary", "📊")

        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for r in recs:
            sev = str(r.get('severity', 'medium')).lower()
            if sev in counts:
                counts[sev] += 1

        cols = st.columns(4)

        with cols[0]:
            st.markdown(f"""
            <div style="background: #FEE2E2; padding: 20px; border-radius: 12px; 
                        text-align: center; border: 2px solid #FECACA;">
                <h1 style="color: #0F172A; margin: 0;">{counts['critical']}</h1>
                <p style="color: #991B1B; margin: 5px 0 0 0; font-weight: 600;">
                    🔴 Critical
                </p>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"""
            <div style="background: #FFEDD5; padding: 20px; border-radius: 12px; 
                        text-align: center; border: 2px solid #FED7AA;">
                <h1 style="color: #0F172A; margin: 0;">{counts['high']}</h1>
                <p style="color: #7C2D12; margin: 5px 0 0 0; font-weight: 600;">
                    🟠 High
                </p>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"""
            <div style="background: #FEF3C7; padding: 20px; border-radius: 12px; 
                        text-align: center; border: 2px solid #FDE68A;">
                <h1 style="color: #0F172A; margin: 0;">{counts['medium']}</h1>
                <p style="color: #78350F; margin: 5px 0 0 0; font-weight: 600;">
                    🟡 Medium
                </p>
            </div>
            """, unsafe_allow_html=True)

        with cols[3]:
            st.markdown(f"""
            <div style="background: #D1FAE5; padding: 20px; border-radius: 12px; 
                        text-align: center; border: 2px solid #A7F3D0;">
                <h1 style="color: #0F172A; margin: 0;">{counts['low']}</h1>
                <p style="color: #065F46; margin: 5px 0 0 0; font-weight: 600;">
                    🟢 Low
                </p>
            </div>
            """, unsafe_allow_html=True)

        if counts['critical'] > 0:
            st.markdown(f"""
            <div style="background: #FEE2E2; border: 2px solid #FECACA; 
                        padding: 15px; border-radius: 8px; margin-top: 15px;">
                <strong style="color: #7F1D1D;">🚨 Priority:</strong>
                <span style="color: #991B1B; font-weight: 500;">
                    Fix {counts['critical']} critical issue(s) first!
                </span>
            </div>
            """, unsafe_allow_html=True)
        elif counts['high'] > 0:
            st.markdown(f"""
            <div class="warning-box" style="margin-top: 15px;">
                <strong>⚠️ Attention:</strong>
                <span>{counts['high']} high-priority issue(s) to address.</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="info-box" style="margin-top: 15px;">
                <strong>💡 Good progress!</strong>
                <span>Focus on medium/low items when you have time.</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Action Items", "✅")

        col1, col2 = st.columns([1, 3])
        with col1:
            severity_filter = st.selectbox(
                "Filter by Severity",
                ["All", "Critical", "High", "Medium", "Low"]
            )

        filtered_recs = recs
        if severity_filter != "All":
            filtered_recs = [
                r for r in recs
                if str(r.get('severity', '')).lower() == severity_filter.lower()
            ]

        st.caption(
            f"Showing {len(filtered_recs)} of {len(recs)} recommendations"
        )

        render_recommendations_panel(filtered_recs, max_items=MAX_RECOMMENDATIONS)

    except Exception as e:
        st.error(f"❌ Error loading recommendations: {str(e)}")


def main():
    if not check_dependencies():
        st.error("Missing required dependencies. Please install plotly.")
        st.stop()

    page = render_sidebar()

    if page == "Overview":
        page_overview()
    elif page == "Files":
        page_files()
    elif page == "Trends":
        page_trends()
    elif page == "Recommendations":
        page_recommendations()


if __name__ == "__main__":
    main()
