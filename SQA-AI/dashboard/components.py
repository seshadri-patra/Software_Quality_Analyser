"""
Dashboard Components for SQA-AI - Enhanced Colors Version
Version 2.4 - Fixed Contrast & Visibility (WCAG AA Compliant)

Key Improvements:
- Fixed all text contrast ratios to minimum 4.5:1
- Fixed radar chart label visibility
- Fixed quality bar chart text contrast
- Fixed trend chart labels
- Better file name display contrast
- Improved overall readability
"""
import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ============================================================
# 🎨 VIBRANT COLOR PALETTE - FIXED CONTRAST (WCAG AA)
# ============================================================

COLORS = {
    # Primary brand colors
    'primary': '#4F46E5',       # Indigo
    'secondary': '#7C3AED',     # Purple

    # Status colors - VIBRANT
    'success': '#059669',       # Emerald green
    'warning': '#D97706',       # Amber (darker for contrast)
    'danger': '#DC2626',        # Red
    'info': '#2563EB',          # Blue

    # Risk levels - BRIGHT & DISTINCT
    'critical': '#DC2626',      # Red
    'high': '#D97706',          # Orange/Amber
    'medium': '#CA8A04',        # Yellow/Gold
    'low': '#16A34A',           # Green

    # Chart colors - VIBRANT PALETTE
    'chart_1': '#4F46E5',       # Indigo
    'chart_2': '#DB2777',       # Pink
    'chart_3': '#0D9488',       # Teal
    'chart_4': '#D97706',       # Orange
    'chart_5': '#7C3AED',       # Purple

    # Specific metrics
    'health': '#059669',        # Emerald
    'decay': '#DC2626',         # Red
    'complexity': '#D97706',    # Orange
    'maintainability': '#2563EB', # Blue

    # Radar chart specific
    'radar_fill': 'rgba(79, 70, 229, 0.35)',
    'radar_line': '#4F46E5',
    'radar_decay': 'rgba(220, 38, 38, 0.4)',
    'radar_decay_line': '#DC2626',

    # Backgrounds & Text - FIXED FOR CONTRAST
    'bg_light': '#F1F5F9',
    'bg_card': '#FFFFFF',
    'bg_chart': '#FFFFFF',
    'grid': '#CBD5E1',
    'text_dark': '#0F172A',     # Very dark - 15.8:1 on white
    'text_medium': '#334155',   # Dark gray - 8.2:1 on white (FIXED from #475569)
    'text_light': '#64748B',    # Medium gray - 4.6:1 on white
}

# Gradient color scales for charts
COLOR_SCALES = {
    'health': ['#FEE2E2', '#FECACA', '#FCA5A5', '#F87171', '#EF4444', '#DC2626'],
    'quality': ['#DCFCE7', '#BBF7D0', '#86EFAC', '#4ADE80', '#22C55E', '#16A34A'],
    'heat': ['#22C55E', '#84CC16', '#EAB308', '#F97316', '#EF4444', '#DC2626'],
}

# Chart configuration
CHART_CONFIG = {
    'displayModeBar': False,
    'responsive': True
}


def check_dependencies() -> bool:
    """Check if required dependencies are available"""
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly not installed. Run: pip install plotly")
        return False
    return True


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int"""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_risk_color(level: str) -> str:
    """Get vibrant color for risk level"""
    return COLORS.get(level.lower(), COLORS['medium'])


# ============================================================
# 1. TRUST STATS BAR
# ============================================================

def render_trust_stats_bar(
    total_scans: int,
    total_files: int,
    total_sloc: int,
    days_tracking: int,
    recommendations_count: int
) -> None:
    """
    Render a trust-building stats bar with vibrant colors.
    """

    # Determine color for recommendations
    if recommendations_count == 0:
        rec_color = COLORS['success']
    elif recommendations_count <= 10:
        rec_color = COLORS['warning']
    else:
        rec_color = COLORS['danger']

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%); 
                padding: 18px 25px; border-radius: 12px; margin-bottom: 15px;
                border: 2px solid #C7D2FE; box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);">
        <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 20px;">
            <div style="text-align: center;">
                <span style="font-size: 1.8rem; font-weight: bold; color: {COLORS['primary']};">{total_scans}</span>
                <br><span style="color: {COLORS['text_medium']}; font-size: 0.85rem; font-weight: 500;">📊 Total Scans</span>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 1.8rem; font-weight: bold; color: {COLORS['info']};">{total_files}</span>
                <br><span style="color: {COLORS['text_medium']}; font-size: 0.85rem; font-weight: 500;">📁 Files Analyzed</span>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 1.8rem; font-weight: bold; color: {COLORS['secondary']};">{total_sloc:,}</span>
                <br><span style="color: {COLORS['text_medium']}; font-size: 0.85rem; font-weight: 500;">📝 Lines of Code</span>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 1.8rem; font-weight: bold; color: {COLORS['chart_3']};">{days_tracking}</span>
                <br><span style="color: {COLORS['text_medium']}; font-size: 0.85rem; font-weight: 500;">📅 Days Tracking</span>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 1.8rem; font-weight: bold; color: {rec_color};">{recommendations_count}</span>
                <br><span style="color: {COLORS['text_medium']}; font-size: 0.85rem; font-weight: 500;">💡 Open Issues</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 2. PROGRESS CARDS - Vibrant Colors
# ============================================================

def render_progress_cards(current: Dict, previous: Optional[Dict] = None, total_scans: int = 1) -> None:
    """
    Large, vibrant metric cards with clear trend indicators.
    """
    cols = st.columns(4, gap="medium")

    def get_trend_html(current_val: float, prev_val: float, higher_is_better: bool = True) -> str:
        """Returns styled HTML for trend indicator"""
        delta = current_val - prev_val
        
        if abs(delta) < 0.01:
            return '<span style="color: #64748B; font-size: 0.95rem; font-weight: 600;">→ No change</span>'
        
        if higher_is_better:
            if delta > 0:
                return f'<span style="color: #10B981; font-size: 0.95rem; font-weight: 600;">▲ +{delta:.1f}</span>'
            else:
                return f'<span style="color: #EF4444; font-size: 0.95rem; font-weight: 600;">▼ {delta:.1f}</span>'
        else:
            if delta < 0:
                return f'<span style="color: #10B981; font-size: 0.95rem; font-weight: 600;">▼ {abs(delta):.1f} ✓</span>'
            else:
                return f'<span style="color: #EF4444; font-size: 0.95rem; font-weight: 600;">▲ +{delta:.1f}</span>'

    # 1. Health Score
    curr_h = _safe_float(current.get('overall_health_score'), 0)
    prev_h = _safe_float(previous.get('overall_health_score') if previous else None, curr_h)
    health_trend = get_trend_html(curr_h, prev_h, True) if previous else '<span style="color: #64748B; font-weight: 600;">First scan</span>'

    with cols[0]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #10B981 0%, #34D399 100%); 
                    padding: 22px; border-radius: 16px; color: white; text-align: center;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);">
            <p style="margin: 0; opacity: 0.95; font-size: 0.85rem; font-weight: 600;">🏥 HEALTH SCORE</p>
            <h1 style="margin: 10px 0; font-size: 3rem; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{curr_h:.0f}</h1>
            <p style="margin: 0;">{health_trend}</p>
        </div>
        """, unsafe_allow_html=True)

    # 2. DDI Score
    curr_ddi = _safe_float(current.get('avg_ddi_score'), 0)
    prev_ddi = _safe_float(previous.get('avg_ddi_score') if previous else None, curr_ddi)
    ddi_trend = get_trend_html(curr_ddi, prev_ddi, False) if previous else '<span style="color: rgba(255,255,255,0.9); font-weight: 600;">First scan</span>'

    # Dynamic background based on DDI level
    if curr_ddi < 25:
        ddi_gradient = "linear-gradient(135deg, #10B981 0%, #34D399 100%)"
        ddi_shadow = "rgba(16, 185, 129, 0.3)"
    elif curr_ddi < 50:
        ddi_gradient = "linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)"
        ddi_shadow = "rgba(245, 158, 11, 0.3)"
    elif curr_ddi < 75:
        ddi_gradient = "linear-gradient(135deg, #F97316 0%, #FB923C 100%)"
        ddi_shadow = "rgba(249, 115, 22, 0.3)"
    else:
        ddi_gradient = "linear-gradient(135deg, #EF4444 0%, #F87171 100%)"
        ddi_shadow = "rgba(239, 68, 68, 0.3)"

    with cols[1]:
        st.markdown(f"""
        <div style="background: {ddi_gradient}; 
                    padding: 22px; border-radius: 16px; color: white; text-align: center;
                    box-shadow: 0 4px 15px {ddi_shadow};">
            <p style="margin: 0; opacity: 0.95; font-size: 0.85rem; font-weight: 600;">☢️ DECAY INDEX</p>
            <h1 style="margin: 10px 0; font-size: 3rem; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{curr_ddi:.1f}</h1>
            <p style="margin: 0;">{ddi_trend}</p>
        </div>
        """, unsafe_allow_html=True)

    # 3. Maintainability
    curr_mi = _safe_float(current.get('avg_maintainability_index'), 0)
    prev_mi = _safe_float(previous.get('avg_maintainability_index') if previous else None, curr_mi)
    mi_trend = get_trend_html(curr_mi, prev_mi, True) if previous else '<span style="color: rgba(255,255,255,0.9); font-weight: 600;">First scan</span>'

    with cols[2]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%); 
                    padding: 22px; border-radius: 16px; color: white; text-align: center;
                    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);">
            <p style="margin: 0; opacity: 0.95; font-size: 0.85rem; font-weight: 600;">🛠️ MAINTAINABILITY</p>
            <h1 style="margin: 10px 0; font-size: 3rem; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{curr_mi:.0f}</h1>
            <p style="margin: 0;">{mi_trend}</p>
        </div>
        """, unsafe_allow_html=True)

    # 4. Critical Issues
    curr_crit = _safe_int(current.get('critical_issues'), 0)
    prev_crit = _safe_int(previous.get('critical_issues') if previous else None, curr_crit)

    if previous:
        delta_crit = curr_crit - prev_crit
        if delta_crit < 0:
            crit_trend = f'<span style="color: #A7F3D0; font-weight: 600;">▼ {delta_crit} ✓</span>'
        elif delta_crit > 0:
            crit_trend = f'<span style="color: #FECACA; font-weight: 600;">▲ +{delta_crit}</span>'
        else:
            crit_trend = '<span style="color: rgba(255,255,255,0.9); font-weight: 600;">→ No change</span>'
    else:
        crit_trend = '<span style="color: rgba(255,255,255,0.9); font-weight: 600;">First scan</span>'

    crit_gradient = "linear-gradient(135deg, #10B981 0%, #34D399 100%)" if curr_crit == 0 else "linear-gradient(135deg, #EF4444 0%, #F87171 100%)"
    crit_shadow = "rgba(16, 185, 129, 0.3)" if curr_crit == 0 else "rgba(239, 68, 68, 0.3)"

    with cols[3]:
        st.markdown(f"""
        <div style="background: {crit_gradient}; 
                    padding: 22px; border-radius: 16px; color: white; text-align: center;
                    box-shadow: 0 4px 15px {crit_shadow};">
            <p style="margin: 0; opacity: 0.95; font-size: 0.85rem; font-weight: 600;">🚨 CRITICAL ISSUES</p>
            <h1 style="margin: 10px 0; font-size: 3rem; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{curr_crit}</h1>
            <p style="margin: 0;">{crit_trend}</p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 3. PROJECT STATS BAR
# ============================================================

def render_project_stats_bar(current: Dict) -> None:
    """Horizontal stats bar with colorful metrics"""

    cols = st.columns(6)

    metrics = [
        ("📁 Files", current.get('total_files', 0), COLORS['primary']),
        ("📝 SLOC", f"{current.get('total_sloc', 0):,}", COLORS['info']),
        ("🔄 Avg CC", f"{current.get('avg_complexity', 0):.1f}", COLORS['warning']),
        ("🎯 Avg MI", f"{current.get('avg_maintainability_index', 0):.0f}", COLORS['success']),
        ("⚠️ High", current.get('high_issues', 0), COLORS['high']),
        ("📋 Medium", current.get('medium_issues', 0), COLORS['medium']),
    ]

    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color}15 0%, {color}25 100%); 
                        padding: 15px; border-radius: 10px; text-align: center;
                        border: 1px solid {color}40;">
                <p style="color: {COLORS['text_medium']}; margin: 0 0 5px 0; font-size: 0.8rem; font-weight: 500;">{label}</p>
                <p style="color: {color}; margin: 0; font-size: 1.4rem; font-weight: 700;">{value}</p>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# 4. HEALTH GAUGE - Vibrant Colors
# ============================================================

def render_health_gauge_large(score: float, status: str = "unknown") -> Optional[go.Figure]:
    """
    Large, colorful health gauge with clear visibility.
    """
    if not PLOTLY_AVAILABLE:
        return None

    score = max(0, min(100, _safe_float(score, 0)))

    # Vibrant color based on score
    if score >= 80:
        bar_color = COLORS['success']
        status_text = "Excellent"
    elif score >= 60:
        bar_color = COLORS['info']
        status_text = "Good"
    elif score >= 40:
        bar_color = COLORS['warning']
        status_text = "Needs Work"
    else:
        bar_color = COLORS['danger']
        status_text = "Critical"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={
            'suffix': "<span style='font-size:0.5em;color:#64748B'>/100</span>",
            'font': {'size': 56, 'color': bar_color, 'family': 'Arial Black'}
        },
        title={
            'text': f"<b style='color:#0F172A'>Project Health</b><br><span style='font-size:0.8em;color:{bar_color}'>{status_text}</span>",
            'font': {'size': 18}
        },
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 2,
                'tickcolor': COLORS['grid'],
                'tickmode': 'array',
                'tickvals': [0, 25, 50, 75, 100],
                'ticktext': ['0', '25', '50', '75', '100'],
                'tickfont': {'size': 14, 'color': COLORS['text_dark']}
            },
            'bar': {'color': bar_color, 'thickness': 0.8},
            'bgcolor': COLORS['bg_light'],
            'borderwidth': 3,
            'bordercolor': COLORS['grid'],
            'steps': [
                {'range': [0, 25], 'color': '#FEE2E2'},
                {'range': [25, 50], 'color': '#FEF3C7'},
                {'range': [50, 75], 'color': '#DBEAFE'},
                {'range': [75, 100], 'color': '#D1FAE5'}
            ],
            'threshold': {
                'line': {'color': bar_color, 'width': 6},
                'thickness': 0.85,
                'value': score
            }
        }
    ))

    fig.update_layout(
        height=380,
        margin={'l': 30, 'r': 30, 't': 100, 'b': 30},
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial'}
    )

    return fig


# ============================================================
# 5. RISK OVERVIEW CHART - Colorful Bars
# ============================================================

def render_risk_overview_chart(high_risk_files: List[Dict]) -> Optional[go.Figure]:
    """
    Colorful horizontal bar chart with clear labels.
    """
    if not PLOTLY_AVAILABLE or not high_risk_files:
        return None

    files = high_risk_files[:10]

    # Truncate long filenames
    filenames = []
    for f in files:
        name = f.get('filename', 'Unknown')
        if len(name) > 28:
            name = name[:25] + '...'
        filenames.append(name)

    scores = [_safe_float(f.get('ddi_score'), 0) for f in files]
    risk_levels = [f.get('risk_level', 'medium').lower() for f in files]
    colors = [_get_risk_color(level) for level in risk_levels]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=filenames[::-1],
        x=scores[::-1],
        orientation='h',
        marker={
            'color': colors[::-1],
            'line': {'color': 'white', 'width': 2}
        },
        text=[f"<b>{s:.1f}</b>" for s in scores[::-1]],
        textposition='outside',
        textfont={'size': 13, 'color': COLORS['text_dark'], 'family': 'Arial'},
        hovertemplate="<b>%{y}</b><br>DDI Score: %{x:.1f}<br>Risk: Higher is worse<extra></extra>"
    ))

    fig.update_layout(
        title={
            'text': '<b>🔥 Top Risk Files</b>',
            'font': {'size': 18, 'color': COLORS['text_dark']},
            'x': 0.5
        },
        xaxis={
            'title': {'text': 'DDI Score (0-100)', 'font': {'size': 12, 'color': COLORS['text_medium']}},
            'range': [0, max(scores) * 1.25] if scores else [0, 100],
            'showgrid': True,
            'gridcolor': COLORS['grid'],
            'gridwidth': 1,
            'zeroline': False,
            'tickfont': {'size': 12, 'color': COLORS['text_dark']}
        },
        yaxis={
            'title': '',
            'tickfont': {'size': 12, 'color': COLORS['text_dark']}
        },
        height=420,
        margin={'l': 180, 'r': 80, 't': 70, 'b': 60},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#FAFBFC',
        showlegend=False
    )

    # Add risk level legend
    fig.add_annotation(
        text="<b>Risk Levels:</b> 🔴 Critical  🟠 High  🟡 Medium  🟢 Low",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font={'size': 12, 'color': COLORS['text_medium']}
    )

    return fig


# ============================================================
# 6. RADAR CHART - FIXED VISIBILITY & CONTRAST
# ============================================================

def render_ddi_radar_large(ddi: Dict) -> Optional[go.Figure]:
    """
    Horizontal bar chart for DDI components.
    REPLACED: Radar chart had positioning issues.
    Option B: Color per bar + score + risk label
    """
    if not PLOTLY_AVAILABLE or not ddi:
        return None

    # Get component scores
    decay = _safe_float(ddi.get('decay_rate_score'), 0)
    entropy = _safe_float(ddi.get('entropy_score'), 0)
    volatility = _safe_float(ddi.get('volatility_score'), 0)
    frequency = _safe_float(ddi.get('frequency_score'), 0)

    categories = ['Frequency', 'Volatility', 'Entropy', 'Decay Rate']
    values = [frequency, volatility, entropy, decay]

    # Color + label per bar based on score
    def get_bar_style(val):
        if val >= 75:
            return '#DC2626', 'CRITICAL'
        elif val >= 50:
            return '#D97706', 'HIGH'
        elif val >= 25:
            return '#CA8A04', 'MEDIUM'
        else:
            return '#16A34A', 'LOW'

    colors = [get_bar_style(v)[0] for v in values]
    risk_labels = [get_bar_style(v)[1] for v in values]

    # Build text labels: "60  HIGH"
    text_labels = [
        f"  {v:.0f}  {r}"
        for v, r in zip(values, risk_labels)
    ]

    fig = go.Figure()

    # Background bars (light gray - full 100)
    fig.add_trace(go.Bar(
        y=categories,
        x=[100] * len(categories),
        orientation='h',
        marker={'color': '#E2E8F0'},
        hoverinfo='skip',
        showlegend=False
    ))

    # Colored value bars
    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker={
            'color': colors,
            'line': {'color': 'white', 'width': 2}
        },
        text=text_labels,
        textposition='outside',
        textfont={
            'size': 13,
            'color': COLORS['text_dark'],
            'family': 'Arial Black'
        },
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Score: %{x:.1f}/100<br>"
            "<extra></extra>"
        ),
        showlegend=False
    ))

    fig.update_layout(
        barmode='overlay',
        title={
            'text': '<b>DDI Components</b>',
            'font': {
                'size': 16,
                'color': COLORS['text_dark']
            },
            'x': 0.5,
            'y': 0.98
        },
        height=320,
        margin={'l': 100, 'r': 120, 't': 50, 'b': 40},
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        xaxis={
            'range': [0, 130],
            'showgrid': True,
            'gridcolor': '#E2E8F0',
            'zeroline': False,
            'title': {
                'text': 'Score (0-100)',
                'font': {
                    'size': 12,
                    'color': COLORS['text_medium']
                }
            },
            'tickfont': {
                'size': 11,
                'color': COLORS['text_dark']
            }
        },
        yaxis={
            'tickfont': {
                'size': 13,
                'color': COLORS['text_dark'],
                'family': 'Arial'
            }
        },
        showlegend=False
    )

    # Add risk level legend at bottom
    fig.add_annotation(
        text=(
            "<b>Risk:</b>  "
            "<span style='color:#16A34A'>■ LOW (&lt;25)</span>  "
            "<span style='color:#CA8A04'>■ MEDIUM (25-50)</span>  "
            "<span style='color:#D97706'>■ HIGH (50-75)</span>  "
            "<span style='color:#DC2626'>■ CRITICAL (&gt;75)</span>"
        ),
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font={'size': 11, 'color': COLORS['text_medium']},
        align='center'
    )

    return fig

# ============================================================
# 7. QUALITY BAR CHART - FIXED TEXT CONTRAST
# ============================================================

def render_quality_bar_chart(metrics: Dict, ddi: Dict) -> Optional[go.Figure]:
    """
    Colorful horizontal bar chart for quality metrics.
    FIXED: Better text contrast, visible labels
    """
    if not PLOTLY_AVAILABLE:
        return None

    # Calculate normalized scores (all 0-100, higher is better)
    complexity_raw = _safe_float(metrics.get('cyclomatic_complexity'), 0)
    simplicity_score = max(0, min(100, 100 - (complexity_raw * 4)))

    mi_score = _safe_float(metrics.get('maintainability_index'), 0)

    doc_raw = _safe_float(metrics.get('docstring_coverage', metrics.get('comment_density', 0)), 0)
    doc_score = min(100, doc_raw * 100 if doc_raw < 1 else doc_raw)

    ddi_raw = _safe_float(ddi.get('ddi_score'), 0)
    stability_score = max(0, 100 - ddi_raw)

    labels = ['Simplicity', 'Maintainability', 'Documentation', 'Stability']
    icons = ['🎯', '🛠️', '📚', '🔒']
    values = [simplicity_score, mi_score, doc_score, stability_score]

    # Color based on score - DISTINCT COLORS
    colors = []
    for v in values:
        if v >= 70:
            colors.append('#059669')
        elif v >= 50:
            colors.append('#2563EB')
        elif v >= 30:
            colors.append('#D97706')
        else:
            colors.append('#DC2626')

    fig = go.Figure()

    # Background bars first (light gray)
    fig.add_trace(go.Bar(
        y=[f"{icons[i]} {labels[i]}" for i in range(len(labels)-1, -1, -1)],
        x=[100] * 4,
        orientation='h',
        marker={'color': '#E2E8F0'},
        hoverinfo='skip',
        showlegend=False
    ))

    fig.add_trace(go.Bar(
        y=[f"{icons[i]} {labels[i]}" for i in range(len(labels)-1, -1, -1)],
        x=values[::-1],
        orientation='h',
        marker={'color': colors[::-1], 'line': {'color': 'white', 'width': 2}},
        text=[f"<b>{v:.0f}</b>" for v in values[::-1]],
        textposition='outside',
        textfont={'size': 13, 'color': COLORS['text_dark'], 'family': 'Arial Black'},
        hovertemplate="<b>%{y}</b><br>Score: %{x:.0f}/100<extra></extra>",
        showlegend=False
    ))


    
    # Add score labels for ALL values - especially 0 ones
    for i, (label, val, color) in enumerate(
        zip(labels[::-1], values[::-1], colors[::-1])
    ):
        if val < 15:  # Very small bars - show label outside
            fig.add_annotation(
                x=val + 3,
                y=i,
                text=f"<b>{val:.0f}</b>",
                showarrow=False,
                font={
                    'size': 14,
                    'color': color,
                    'family': 'Arial Black'
                },
                xanchor='left'
            )

    fig.update_layout(
        barmode='overlay',
        height=340,
        margin={'l': 140, 'r': 50, 't': 60, 'b': 50},
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        xaxis={
            'range': [0, 110],
            'showgrid': True,
            'gridcolor': '#E2E8F0',
            'zeroline': False,
            'title': {'text': 'Score (0-100)', 'font': {'size': 13, 'color': COLORS['text_medium']}},
            'tickfont': {'size': 12, 'color': COLORS['text_dark']}
        },
        yaxis={
            'tickfont': {'size': 14, 'color': COLORS['text_dark'], 'family': 'Arial'}
        },
        showlegend=False,
        title={
            'text': '<b>Quality Profile</b>',
            'font': {'size': 18, 'color': COLORS['text_dark']},
            'x': 0.5,
            'y': 0.95
        }
    )

    return fig


# ============================================================
# 8. TREND DASHBOARD - FIXED CONTRAST & LABELS
# ============================================================

def render_trend_dashboard(history: List[Dict]) -> None:
    """
    Complete trend dashboard with vibrant, clear charts.
    FIXED: Better axis labels, legend visibility, line contrast
    """
    if not PLOTLY_AVAILABLE or len(history) < 2:
        st.warning("Not enough data for trends.")
        return

    df = pd.DataFrame(history)
    df['run_at'] = pd.to_datetime(df['run_at'])
    df = df.sort_values('run_at')

    # Calculate improvements
    first_health = df.iloc[0]['overall_health_score']
    last_health = df.iloc[-1]['overall_health_score']
    health_change = last_health - first_health

    first_ddi = df.iloc[0]['avg_ddi_score']
    last_ddi = df.iloc[-1]['avg_ddi_score']
    ddi_change = last_ddi - first_ddi

    # Summary cards
    col1, col2, col3 = st.columns(3)

    with col1:
        change_color = COLORS['success'] if health_change >= 0 else COLORS['danger']
        arrow = "📈" if health_change >= 0 else "📉"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {change_color}15 0%, {change_color}25 100%); 
                    padding: 20px; border-radius: 12px; text-align: center;
                    border: 2px solid {change_color}40;">
            <p style="color: {COLORS['text_dark']}; margin: 0; font-size: 0.9rem; font-weight: 600;">{arrow} Health Change</p>
            <h2 style="color: {change_color}; margin: 10px 0; font-size: 2rem;">
                {'+' if health_change >= 0 else ''}{health_change:.1f}
            </h2>
            <p style="color: {COLORS['text_medium']}; margin: 0; font-size: 0.85rem;">points since first scan</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        change_color = COLORS['success'] if ddi_change <= 0 else COLORS['danger']
        arrow = "📉" if ddi_change <= 0 else "📈"
        indicator = "✓" if ddi_change <= 0 else "⚠️"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {change_color}15 0%, {change_color}25 100%); 
                    padding: 20px; border-radius: 12px; text-align: center;
                    border: 2px solid {change_color}40;">
            <p style="color: {COLORS['text_dark']}; margin: 0; font-size: 0.9rem; font-weight: 600;">{arrow} DDI Change</p>
            <h2 style="color: {change_color}; margin: 10px 0; font-size: 2rem;">
                {'+' if ddi_change > 0 else ''}{ddi_change:.1f} {indicator}
            </h2>
            <p style="color: {COLORS['text_medium']}; margin: 0; font-size: 0.85rem;">decay index change</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {COLORS['primary']}15 0%, {COLORS['primary']}25 100%); 
                    padding: 20px; border-radius: 12px; text-align: center;
                    border: 2px solid {COLORS['primary']}40;">
            <p style="color: {COLORS['text_dark']}; margin: 0; font-size: 0.9rem; font-weight: 600;">📊 Analysis History</p>
            <h2 style="color: {COLORS['primary']}; margin: 10px 0; font-size: 2rem;">{len(history)}</h2>
            <p style="color: {COLORS['text_medium']}; margin: 0; font-size: 0.85rem;">scans performed</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main trend chart - FIXED VISIBILITY
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )

    # Health Score line - BRIGHT GREEN, THICK LINE
    fig.add_trace(
        go.Scatter(
            x=df['run_at'],
            y=df['overall_health_score'],
            name="Health Score",
            line={'color': '#059669', 'width': 4},
            mode='lines+markers',
            marker={'size': 12, 'color': '#059669', 'line': {'width': 2, 'color': 'white'}},
            fill='tozeroy',
            fillcolor='rgba(5, 150, 105, 0.15)',
            hovertemplate="<b>Health Score</b><br>Date: %{x|%b %d, %Y}<br>Score: %{y:.1f}/100<extra></extra>"
        ),
        secondary_y=False
    )

    # DDI Score line - BRIGHT RED, DISTINCT STYLE
    fig.add_trace(
        go.Scatter(
            x=df['run_at'],
            y=df['avg_ddi_score'],
            name="Decay Index",
            line={'color': '#DC2626', 'width': 4, 'dash': 'dash'},
            mode='lines+markers',
            marker={'size': 12, 'color': '#DC2626', 'symbol': 'diamond', 'line': {'width': 2, 'color': 'white'}},
            hovertemplate="<b>Decay Index</b><br>Date: %{x|%b %d, %Y}<br>Score: %{y:.1f}<extra></extra>"
        ),
        secondary_y=True
    )

    # Add target zone
    fig.add_hrect(
        y0=75, y1=100,
        fillcolor="rgba(5, 150, 105, 0.1)",
        layer="below",
        line_width=0,
        secondary_y=False,
        annotation_text="🎯 Target Zone",
        annotation_position="top left",
        annotation_font={'size': 13, 'color': '#059669', 'family': 'Arial'}
    )

    fig.update_layout(
        title={
            'text': '<b>📊 Health vs Decay Over Time</b>',
            'font': {'size': 22, 'color': COLORS['text_dark'], 'family': 'Arial'},
            'x': 0.5
        },
        height=500,
        margin={'l': 70, 'r': 70, 't': 100, 'b': 80},
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FAFBFC',
        hovermode='x unified',
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'center',
            'x': 0.5,
            'font': {'size': 15, 'color': COLORS['text_dark'], 'family': 'Arial'},
            'bgcolor': 'rgba(255,255,255,0.95)',
            'bordercolor': '#CBD5E1',
            'borderwidth': 2
        }
    )

    # X-axis styling - FIXED VISIBILITY
    fig.update_xaxes(
        title_text="Date",
        title_font={'size': 14, 'color': COLORS['text_dark'], 'family': 'Arial'},
        showgrid=True,
        gridcolor='#E2E8F0',
        gridwidth=1,
        tickformat='%b %d',
        tickangle=-45,
        tickfont={'size': 13, 'color': COLORS['text_dark'], 'family': 'Arial'},
        linecolor='#94A3B8',
        linewidth=2
    )

    # Left Y-axis (Health) - GREEN LABEL
    fig.update_yaxes(
        title_text="Health Score (0-100)",
        title_font={'size': 14, 'color': '#059669', 'family': 'Arial'},
        showgrid=True,
        gridcolor='#E2E8F0',
        gridwidth=1,
        range=[0, 105],
        tickfont={'size': 13, 'color': COLORS['text_dark'], 'family': 'Arial'},
        linecolor='#059669',
        linewidth=2,
        secondary_y=False
    )

    # Right Y-axis (DDI) - RED LABEL
    fig.update_yaxes(
        title_text="Decay Index (0-100)",
        title_font={'size': 14, 'color': '#DC2626', 'family': 'Arial'},
        showgrid=False,
        range=[0, 105],
        tickfont={'size': 13, 'color': COLORS['text_dark'], 'family': 'Arial'},
        linecolor='#DC2626',
        linewidth=2,
        secondary_y=True
    )

    st.plotly_chart(fig, width='stretch', config=CHART_CONFIG)

    # Additional mini charts - FIXED STYLING
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if 'avg_complexity' in df.columns:
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=df['run_at'],
                y=df['avg_complexity'],
                name="Complexity",
                fill='tozeroy',
                fillcolor='rgba(217, 119, 6, 0.2)',
                line={'color': '#D97706', 'width': 4},
                mode='lines+markers',
                marker={'size': 10, 'color': '#D97706', 'line': {'width': 2, 'color': 'white'}}
            ))
            
            fig_comp.update_layout(
                title={'text': '<b>📈 Complexity Trend</b>', 
                       'font': {'size': 18, 'color': COLORS['text_dark'], 'family': 'Arial'}, 
                       'x': 0.5},
                height=320,
                margin={'l': 60, 'r': 40, 't': 70, 'b': 60},
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FAFBFC',
                showlegend=False
            )
            fig_comp.update_xaxes(
                showgrid=True, 
                gridcolor='#E2E8F0', 
                tickformat='%b %d', 
                tickangle=-45,
                tickfont={'size': 12, 'color': COLORS['text_dark']},
                title_text='Date',
                title_font={'size': 13, 'color': COLORS['text_medium']}
            )
            fig_comp.update_yaxes(
                showgrid=True, 
                gridcolor='#E2E8F0', 
                title_text='Avg Complexity',
                title_font={'size': 13, 'color': '#D97706'},
                tickfont={'size': 12, 'color': COLORS['text_dark']}
            )
            
            st.plotly_chart(fig_comp, width='stretch', config=CHART_CONFIG)

    with col2:
        if 'avg_maintainability_index' in df.columns:
            fig_mi = go.Figure()
            fig_mi.add_trace(go.Scatter(
                x=df['run_at'],
                y=df['avg_maintainability_index'],
                name="Maintainability",
                fill='tozeroy',
                fillcolor='rgba(37, 99, 235, 0.2)',
                line={'color': '#2563EB', 'width': 4},
                mode='lines+markers',
                marker={'size': 10, 'color': '#2563EB', 'line': {'width': 2, 'color': 'white'}}
            ))
            
            fig_mi.update_layout(
                title={'text': '<b>🛠️ Maintainability Trend</b>', 
                       'font': {'size': 18, 'color': COLORS['text_dark'], 'family': 'Arial'}, 
                       'x': 0.5},
                height=320,
                margin={'l': 60, 'r': 40, 't': 70, 'b': 60},
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FAFBFC',
                showlegend=False
            )
            fig_mi.update_xaxes(
                showgrid=True, 
                gridcolor='#E2E8F0', 
                tickformat='%b %d', 
                tickangle=-45,
                tickfont={'size': 12, 'color': COLORS['text_dark']},
                title_text='Date',
                title_font={'size': 13, 'color': COLORS['text_medium']}
            )
            fig_mi.update_yaxes(
                showgrid=True, 
                gridcolor='#E2E8F0', 
                range=[0, 100], 
                title_text='MI Score',
                title_font={'size': 13, 'color': '#2563EB'},
                tickfont={'size': 12, 'color': COLORS['text_dark']}
            )
            
            st.plotly_chart(fig_mi, width='stretch', config=CHART_CONFIG)


# ============================================================
# 9. FILE TABLE - Enhanced
# ============================================================

def render_rich_file_table(files: List[Dict]) -> None:
    """
    Rich file table with colorful risk indicators.
    """
    if not files:
        st.info("📭 No files to display.")
        return

    data = []
    for f in files:
        file_info = f.get('file', {}) or {}
        metrics = f.get('metrics', {}) or {}
        ddi = f.get('ddi', {}) or {}
        
        risk_level = str(ddi.get('risk_level', 'low')).lower()
        risk_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(risk_level, '⚪')
        
        data.append({
            "Risk": risk_emoji,
            "File": file_info.get('filename', 'Unknown'),
            "DDI Score": _safe_float(ddi.get('ddi_score'), 0),
            "Complexity": _safe_int(metrics.get('cyclomatic_complexity'), 0),
            "Maintainability": _safe_float(metrics.get('maintainability_index'), 0),
            "SLOC": _safe_int(metrics.get('sloc'), 0),
            "Status": risk_level.title()
        })

    df = pd.DataFrame(data)

    st.dataframe(
        df,
        column_config={
            "Risk": st.column_config.TextColumn("⚠️", width="small"),
            "File": st.column_config.TextColumn("📄 Filename", width="medium"),
            "DDI Score": st.column_config.ProgressColumn(
                "☢️ Decay Index",
                help="0-100. Lower is better.",
                format="%.1f",
                min_value=0,
                max_value=100,
            ),
            "Complexity": st.column_config.NumberColumn(
                "🔄 Complexity",
                help="Cyclomatic complexity. Lower is better.",
                format="%d"
            ),
            "Maintainability": st.column_config.ProgressColumn(
                "🛠️ Maintainability",
                help="0-100. Higher is better.",
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "SLOC": st.column_config.NumberColumn(
                "📝 Lines",
                format="%d"
            ),
            "Status": st.column_config.TextColumn("📊 Status", width="small"),
        },
        width='stretch',
        hide_index=True,
        height=420
    )


# ============================================================
# 10. FILE DEEP DIVE PANEL - FIXED FILENAME VISIBILITY
# ============================================================

def render_file_deep_dive_panel(file_info: Dict, metrics: Dict, ddi: Dict) -> None:
    """
    Comprehensive file analysis with colorful charts.
    FIXED: Better filename contrast and visibility
    """
    filename = file_info.get('filename', 'Unknown')
    risk_level = str(ddi.get('risk_level', 'low')).lower()
    risk_color = _get_risk_color(risk_level)

    # Header - FIXED CONTRAST: Dark text on light background
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%); 
                padding: 24px; border-radius: 12px; margin-bottom: 20px; 
                border-left: 6px solid {risk_color};
                border: 2px solid #E2E8F0;">
        <h2 style="margin: 0 0 12px 0; color: #0F172A; font-size: 1.5rem;">📄 {filename}</h2>
        <p style="color: #334155; margin: 0; font-size: 0.95rem;">
            📁 <code style="background: #E2E8F0; padding: 4px 8px; border-radius: 4px; color: #1E293B;">{file_info.get('relative_path', 'Unknown path')}</code> 
            &nbsp;&nbsp;
            <span style="background: {risk_color}; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">
                {risk_level.upper()} RISK
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Get raw MI value to check if negative
    raw_mi = metrics.get('maintainability_index', 0)
    mi_is_negative = (raw_mi is not None and float(raw_mi) <= 0)

    metrics_data = [
        ("☢️ DDI Score", _safe_float(ddi.get('ddi_score'), 0), False),
        ("🔄 Complexity", _safe_int(metrics.get('cyclomatic_complexity'), 0), False),
        ("🛠️ Maintainability", _safe_float(metrics.get('maintainability_index'), 0), True),
        ("📝 Lines of Code", _safe_int(metrics.get('sloc'), 0), None),
    ]

    for col, (label, value, higher_is_better) in zip(
        [col1, col2, col3, col4], metrics_data
    ):
        with col:
            # Determine color
            if higher_is_better is None:
                color = COLORS['info']
            elif higher_is_better:
                # Special case: MI = 0 means very poor (negative clamped)
                if label == "🛠️ Maintainability" and mi_is_negative:
                    color = COLORS['danger']
                else:
                    color = (COLORS['success'] if value >= 65
                            else COLORS['warning'] if value >= 45
                            else COLORS['danger'])
            else:
                if label == "☢️ DDI Score":
                    color = (COLORS['success'] if value < 25
                            else COLORS['warning'] if value < 50
                            else COLORS['danger'])
                else:
                    color = (COLORS['success'] if value < 10
                            else COLORS['warning'] if value < 20
                            else COLORS['danger'])

            # Format display value
            display_val = (
                f"{value:.1f}" if isinstance(value, float) else str(value)
            )

            # FIXED: Add warning indicator for MI = 0 (Option A)
            warning_badge = ""
            warning_note = ""
            if label == "🛠️ Maintainability" and mi_is_negative:
                warning_badge = " ⚠️"
                warning_note = (
                    "<p style='color: #991B1B; font-size: 0.75rem; "
                    "margin: 4px 0 0 0;'>Very Poor</p>"
                )

            st.markdown(f"""
            <div style="background: #FFFFFF; padding: 18px; border-radius: 12px;
                        text-align: center; border: 2px solid #E2E8F0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <p style="color: {COLORS['text_medium']}; margin: 0 0 8px 0;
                        font-size: 0.9rem; font-weight: 500;">
                    {label}{warning_badge}
                </p>
                <p style="color: {color}; margin: 0; font-size: 2rem;
                        font-weight: bold;">
                    {display_val}
                </p>
                {warning_note}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### 🎯 Risk Breakdown")
        fig = render_ddi_radar_large(ddi)
        if fig:
            st.plotly_chart(fig, width='stretch', config=CHART_CONFIG)

    with col2:
        st.markdown(f"#### 📊 Quality Profile")
        fig = render_quality_bar_chart(metrics, ddi)
        if fig:
            st.plotly_chart(fig, width='stretch', config=CHART_CONFIG)

    # Detailed metrics expander
    with st.expander("📋 View All Metrics", expanded=False):
        detail_cols = st.columns(3)
        
        with detail_cols[0]:
            st.markdown(f"**📏 Size Metrics**")
            st.markdown(f"""
            - Total Lines: **{_safe_int(metrics.get('loc'), 0)}**
            - Source Lines: **{_safe_int(metrics.get('sloc'), 0)}**
            - Blank Lines: **{_safe_int(metrics.get('blank_lines'), 0)}**
            - Comments: **{_safe_int(metrics.get('comment_lines'), 0)}**
            """)
        
        with detail_cols[1]:
            st.markdown(f"**🏗️ Structure**")
            st.markdown(f"""
            - Functions: **{_safe_int(metrics.get('function_count'), 0)}**
            - Classes: **{_safe_int(metrics.get('class_count'), 0)}**
            - Imports: **{_safe_int(metrics.get('import_count'), 0)}**
            """)
        
        with detail_cols[2]:
            st.markdown(f"**⚠️ Risk Components**")
            st.markdown(f"""
            - Decay Rate: **{_safe_float(ddi.get('decay_rate_score'), 0):.1f}**
            - Entropy: **{_safe_float(ddi.get('entropy_score'), 0):.1f}**
            - Volatility: **{_safe_float(ddi.get('volatility_score'), 0):.1f}**
            - Frequency: **{_safe_float(ddi.get('frequency_score'), 0):.1f}**
            """)


# ============================================================
# 11. RECOMMENDATIONS PANEL - FIXED CONTRAST
# ============================================================

def render_recommendations_panel(recs: List[Dict], max_items: int = 20) -> None:
    """
    Colorful, actionable recommendations list.
    FIXED: Better text contrast for all severity levels
    """
    if not recs:
        st.markdown("""
        <div style="background: #D1FAE5; padding: 25px; border-radius: 12px; text-align: center; border: 2px solid #A7F3D0;">
            <h3 style="color: #065F46; margin: 0;">✅ No Issues Found!</h3>
            <p style="color: #065F46; margin: 10px 0 0 0; font-weight: 500;">Your code is in great shape.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_recs = sorted(
        recs,
        key=lambda x: severity_order.get(str(x.get('severity', 'medium')).lower(), 2)
    )

    for i, r in enumerate(sorted_recs[:max_items]):
        severity = str(r.get('severity', 'medium')).lower()
        
        # FIXED: All text colors now have 7:1+ contrast ratio
        styles = {
            'critical': {
                'bg': '#FEE2E2', 'border': '#EF4444', 'icon': '🔴', 
                'label': 'CRITICAL', 'text': '#7F1D1D', 'badge_bg': '#EF4444'
            },
            'high': {
                'bg': '#FFEDD5', 'border': '#F97316', 'icon': '🟠', 
                'label': 'HIGH', 'text': '#7C2D12', 'badge_bg': '#F97316'
            },
            'medium': {
                'bg': '#FEF3C7', 'border': '#D97706', 'icon': '🟡', 
                'label': 'MEDIUM', 'text': '#78350F', 'badge_bg': '#D97706'
            },
            'low': {
                'bg': '#D1FAE5', 'border': '#10B981', 'icon': '🟢', 
                'label': 'LOW', 'text': '#065F46', 'badge_bg': '#10B981'
            }
        }
        style = styles.get(severity, styles['medium'])
        
        with st.expander(f"{style['icon']} [{style['label']}] {r.get('title', 'Recommendation')}", expanded=(severity == 'critical')):
            st.markdown(f"""
            <div style="background: {style['bg']}; padding: 18px; border-radius: 10px; 
                        border-left: 5px solid {style['border']}; margin-bottom: 12px;">
                <p style="margin: 0; color: {style['text']}; font-size: 1rem; line-height: 1.5; font-weight: 500;">
                    {r.get('message', 'No details available.')}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if r.get('action'):
                st.markdown(f"**💡 Suggested Action:** {r.get('action')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if r.get('file_path'):
                    st.code(r.get('file_path'), language=None)
            with col2:
                if r.get('line_start'):
                    st.caption(f"📍 Line: **{r.get('line_start')}**")
            
            if r.get('metric_name') and r.get('metric_value') is not None:
                threshold = r.get('threshold', 'N/A')
                st.caption(f"📊 **{r.get('metric_name')}**: {r.get('metric_value')} (threshold: {threshold})")

# ============================================================
# 12. TREND PREDICTION CHART
# ============================================================

def render_trend_prediction_chart(trend_result: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Visual chart showing trend prediction
    """
    if not PLOTLY_AVAILABLE:
        return None
    
    if not trend_result.get('has_sufficient_data'):
        return None
    
    raw_scores = trend_result.get('raw_scores', [])
    timestamps = trend_result.get('timestamps_days', [])
    
    if len(raw_scores) < 2:
        return None
    
    current_ddi = trend_result.get('current_ddi', 0)
    slope = trend_result.get('slope', 0)
    
    # Create figure
    fig = go.Figure()
    
    # Historical data points
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=raw_scores,
        mode='lines+markers',
        name='Historical DDI',
        line={'color': '#2563EB', 'width': 3},
        marker={'size': 10, 'color': '#2563EB'}
    ))
    
    # Prediction line (next 30 days)
    last_day = timestamps[-1] if timestamps else 0
    future_days = [last_day, last_day + 30]
    future_scores = [current_ddi, trend_result.get('predicted_30d', current_ddi)]
    
    prediction_color = '#059669' if slope <= 0 else '#DC2626'
    
    fig.add_trace(go.Scatter(
        x=future_days,
        y=future_scores,
        mode='lines+markers',
        name='Predicted',
        line={'color': prediction_color, 'width': 3, 'dash': 'dash'},
        marker={'size': 10, 'color': prediction_color, 'symbol': 'diamond'}
    ))
    
    # Critical threshold line
    fig.add_hline(
        y=75, 
        line_dash="dot", 
        line_color="#DC2626",
        annotation_text="Critical (75)",
        annotation_position="right"
    )
    
    # Warning threshold line
    fig.add_hline(
        y=50, 
        line_dash="dot", 
        line_color="#D97706",
        annotation_text="High (50)",
        annotation_position="right"
    )
    
    fig.update_layout(
        title={
            'text': '<b>DDI Trend & 30-Day Prediction</b>',
            'font': {'size': 18, 'color': '#0F172A'}
        },
        xaxis={
            'title': 'Days',
            'titlefont': {'color': '#334155'},
            'tickfont': {'color': '#334155'}
        },
        yaxis={
            'title': 'DDI Score',
            'range': [0, 100],
            'titlefont': {'color': '#334155'},
            'tickfont': {'color': '#334155'}
        },
        height=350,
        margin={'l': 60, 'r': 40, 't': 60, 'b': 50},
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FAFBFC',
        legend={'orientation': 'h', 'y': -0.15},
        showlegend=True
    )
    
    return fig

# ============================================================
# LEGACY SUPPORT FUNCTIONS
# ============================================================

def render_metric_row(metrics: Dict[str, Any], columns: int = 4) -> None:
    """Legacy support"""
    cols = st.columns(columns)
    items = list(metrics.items())
    for i, (label, value) in enumerate(items):
        with cols[i % columns]:
            if isinstance(value, dict):
                st.metric(label=label, value=value.get('value'), delta=value.get('delta'))
            else:
                st.metric(label=label, value=value)


def render_progress_row(current: Dict, previous: Optional[Dict] = None) -> None:
    """Legacy support"""
    render_progress_cards(current, previous)


def render_health_gauge(score: float) -> Optional[go.Figure]:
    """Legacy support"""
    return render_health_gauge_large(score, "unknown")


def render_ddi_fingerprint(components: Dict[str, float], title: str = "Risk Fingerprint") -> Optional[go.Figure]:
    """Legacy support"""
    return render_ddi_radar_large(components)


def render_trend_story(history: List[Dict]) -> Optional[go.Figure]:
    """Legacy support - returns None, use render_trend_dashboard instead"""
    return None


def render_file_deep_dive(file_info: Dict, metrics: Dict, ddi: Dict) -> None:
    """Legacy support"""
    render_file_deep_dive_panel(file_info, metrics, ddi)


def render_recommendations_list(recs: List[Dict], max_items: int = 10) -> None:
    """Legacy support"""
    render_recommendations_panel(recs, max_items)
    
