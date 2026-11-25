"""
Report Generator for SQA-AI
US8: Export report (TXT/JSON/HTML/PDF optional)

This version adds:
- Full trend table (analysis history)
- Delta vs previous scan
- Recommendation evidence: metric_name/value/threshold
- Recommendation location: function/class/line range (when available)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


@dataclass
class ReportConfig:
    title: str = "SQA-AI Analysis Report"
    max_recommendations: int = 50
    max_files: int = 200
    max_trend_rows: int = 50


class ReportGenerator:
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()

    def generate(
        self,
        output_path: str,
        project_name: str,
        project_path: str,
        summary: Dict[str, Any],
        files: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        format: str = "html",
        trends: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        fmt = format.lower()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        trends = trends or []

        if fmt == "txt":
            return self._txt(output_path, project_name, project_path, summary, files, recommendations, trends)
        if fmt == "json":
            return self._json(output_path, project_name, project_path, summary, files, recommendations, trends)
        if fmt == "html":
            return self._html(output_path, project_name, project_path, summary, files, recommendations, trends)
        if fmt == "pdf":
            if not PDF_AVAILABLE:
                html_path = output_path.replace(".pdf", ".html")
                return self._html(html_path, project_name, project_path, summary, files, recommendations, trends)
            return self._pdf(output_path, project_name, project_path, summary, files, recommendations, trends)

        raise ValueError(f"Unsupported format: {format}")

    def _location(self, rec: Dict[str, Any]) -> str:
        parts = []
        if rec.get("function_name"):
            parts.append(f"Function: {rec['function_name']}")
        if rec.get("class_name"):
            parts.append(f"Class: {rec['class_name']}")
        if rec.get("line_start"):
            if rec.get("line_end") and rec["line_end"] != rec["line_start"]:
                parts.append(f"Lines {rec['line_start']}-{rec['line_end']}")
            else:
                parts.append(f"Line {rec['line_start']}")
        return " | ".join(parts) if parts else "File-level"

    def _evidence(self, rec: Dict[str, Any]) -> str:
        mn = rec.get("metric_name")
        mv = rec.get("metric_value")
        th = rec.get("threshold")
        if mn is None and mv is None and th is None:
            return ""
        return f"{mn} = {mv} (threshold: {th})"

    def _trend_table_rows(self, trends: List[Dict[str, Any]]) -> List[List[str]]:
        rows = [["Run Date", "Health", "Avg DDI", "Avg MI", "Avg CC", "Files", "SLOC"]]
        # trends may arrive newest->oldest; show newest first but limit
        for t in trends[: self.config.max_trend_rows]:
            rows.append([
                str(t.get("run_at", ""))[:19],
                f"{float(t.get('overall_health_score', 0) or 0):.0f}",
                f"{float(t.get('avg_ddi_score', 0) or 0):.1f}",
                f"{float(t.get('avg_maintainability_index', 0) or 0):.1f}",
                f"{float(t.get('avg_complexity', 0) or 0):.1f}",
                str(t.get("total_files", 0)),
                str(t.get("total_sloc", 0)),
            ])
        return rows

    def _txt(self, out: str, name: str, path: str, summary: Dict, files: List[Dict], recs: List[Dict], trends: List[Dict]) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delta = summary.get("delta_vs_previous", {}) or {}

        lines = []
        lines.append("=" * 72)
        lines.append(self.config.title)
        lines.append("=" * 72)
        lines.append(f"Project: {name}")
        lines.append(f"Path: {path}")
        lines.append(f"Generated: {ts}")
        lines.append("")

        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 72)
        lines.append(f"Health Score: {summary.get('health_score', 0):.0f}/100 ({str(summary.get('status','')).upper()})")
        lines.append(f"Avg DDI: {float(summary.get('avg_ddi',0) or 0):.1f} | Avg MI: {float(summary.get('avg_mi',0) or 0):.1f} | Avg CC: {float(summary.get('avg_cc',0) or 0):.1f}")
        lines.append(f"Files: {summary.get('files_analyzed', 0)} | SLOC: {summary.get('total_sloc', 0)}")
        lines.append("")

        if delta:
            lines.append("CHANGE VS PREVIOUS SCAN")
            lines.append("-" * 72)
            lines.append(f"Previous run: {delta.get('run_at_prev','N/A')}")
            lines.append(f"Δ Health: {delta.get('health_score',0):+.1f}")
            lines.append(f"Δ Avg DDI: {delta.get('avg_ddi',0):+.2f} (negative is improvement)")
            lines.append(f"Δ Avg MI: {delta.get('avg_mi',0):+.2f}")
            lines.append(f"Δ Avg CC: {delta.get('avg_cc',0):+.2f}")
            lines.append("")

        lines.append("FULL TREND TABLE (latest scans)")
        lines.append("-" * 72)
        table = self._trend_table_rows(trends)
        for r in table:
            lines.append(" | ".join(r))
        lines.append("")

        lines.append("TOP RECOMMENDATIONS")
        lines.append("-" * 72)
        recs_sorted = sorted(recs, key=lambda x: float(x.get("priority_score", 0) or 0), reverse=True)
        for i, r in enumerate(recs_sorted[: self.config.max_recommendations], 1):
            sev = str(r.get("severity", "medium")).upper()
            fp = r.get("file_path") or r.get("relative_path") or r.get("filename") or "unknown"
            loc = self._location(r)
            ev = self._evidence(r)
            lines.append(f"{i}. [{sev}] {r.get('title','')}")
            lines.append(f"   File: {fp}")
            lines.append(f"   Location: {loc}")
            if ev:
                lines.append(f"   Trigger: {ev}")
            lines.append(f"   Issue: {r.get('message','')}")
            lines.append(f"   Action: {r.get('action','')}")
            lines.append("")

        Path(out).write_text("\n".join(lines), encoding="utf-8")
        return out

    def _json(self, out: str, name: str, path: str, summary: Dict, files: List[Dict], recs: List[Dict], trends: List[Dict]) -> str:
        payload = {
            "metadata": {"generated_at": datetime.now().isoformat(), "title": self.config.title},
            "project": {"name": name, "path": path},
            "summary": summary,
            "trends": trends[: self.config.max_trend_rows],
            "files": files[: self.config.max_files],
            "recommendations": recs[: self.config.max_recommendations],
        }
        Path(out).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return out

    def _html(self, out: str, name: str, path: str, summary: Dict, files: List[Dict], recs: List[Dict], trends: List[Dict]) -> str:
        delta = summary.get("delta_vs_previous", {}) or {}
        recs_sorted = sorted(recs, key=lambda x: float(x.get("priority_score", 0) or 0), reverse=True)

        trend_rows = self._trend_table_rows(trends)

        html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{self.config.title} - {name}</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;background:#f6f7fb;color:#111;margin:0}}
.container{{max-width:1100px;margin:0 auto;padding:24px}}
.header{{background:#1f2937;color:#fff;padding:18px;border-radius:10px}}
.card{{background:#fff;margin-top:16px;border-radius:10px;border:1px solid #e5e7eb}}
.card h2{{margin:0;padding:14px 18px;border-bottom:1px solid #e5e7eb}}
.card .body{{padding:16px 18px}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left;font-size:13px}}
th{{background:#f9fafb}}
.rec{{padding:10px;border-left:4px solid #e5e7eb;background:#fafafa;margin-bottom:12px}}
.small{{color:#555;font-size:12px}}
code{{background:#eee;padding:2px 6px;border-radius:6px}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{self.config.title}</h1>
    <div><b>{name}</b></div>
    <div class="small">{path}</div>
  </div>

  <div class="card"><h2>Executive Summary</h2><div class="body">
    <div><b>Health:</b> {float(summary.get('health_score',0) or 0):.0f}/100 ({str(summary.get('status','')).upper()})</div>
    <div class="small">
      Avg DDI: {float(summary.get('avg_ddi',0) or 0):.1f} |
      Avg MI: {float(summary.get('avg_mi',0) or 0):.1f} |
      Avg CC: {float(summary.get('avg_cc',0) or 0):.1f} |
      Files: {summary.get('files_analyzed',0)} |
      SLOC: {summary.get('total_sloc',0)}
    </div>
  </div></div>
"""

        if delta:
            html += f"""
  <div class="card"><h2>Change vs Previous Scan</h2><div class="body">
    <div class="small">Previous run: {delta.get('run_at_prev','N/A')}</div>
    <ul>
      <li>Δ Health: {delta.get('health_score',0):+.1f}</li>
      <li>Δ Avg DDI: {delta.get('avg_ddi',0):+.2f} (negative is improvement)</li>
      <li>Δ Avg MI: {delta.get('avg_mi',0):+.2f}</li>
      <li>Δ Avg CC: {delta.get('avg_cc',0):+.2f}</li>
    </ul>
  </div></div>
"""

        html += """
  <div class="card"><h2>Full Trend Table</h2><div class="body">
    <table>
"""
        # trend table
        html += "<tr>" + "".join(f"<th>{h}</th>" for h in trend_rows[0]) + "</tr>"
        for row in trend_rows[1:]:
            html += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        html += """
    </table>
  </div></div>
"""

        html += """
  <div class="card"><h2>Top Recommendations (with evidence)</h2><div class="body">
"""
        for r in recs_sorted[: self.config.max_recommendations]:
            sev = str(r.get("severity", "medium")).upper()
            fp = r.get("file_path") or r.get("relative_path") or r.get("filename") or "unknown"
            loc = self._location(r)
            ev = self._evidence(r)

            html += f"""
    <div class="rec">
      <div><b>[{sev}] {r.get('title','')}</b></div>
      <div class="small">File: <code>{fp}</code> | Location: <code>{loc}</code></div>
"""
            if ev:
                html += f"""      <div class="small">Trigger: <code>{ev}</code></div>"""
            html += f"""
      <div style="margin-top:6px">{r.get('message','')}</div>
      <div style="margin-top:6px"><b>Action:</b> {r.get('action','')}</div>
    </div>
"""
        html += """
  </div></div>
</div></body></html>
"""
        Path(out).write_text(html, encoding="utf-8")
        return out

    def _pdf(self, out: str, name: str, path: str, summary: Dict, files: List[Dict], recs: List[Dict], trends: List[Dict]) -> str:
        doc = SimpleDocTemplate(out, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(self.config.title, styles["Title"]))
        story.append(Paragraph(f"<b>Project:</b> {name}", styles["Normal"]))
        story.append(Paragraph(f"<b>Path:</b> {path}", styles["Normal"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Trend Table", styles["Heading2"]))
        rows = self._trend_table_rows(trends)
        table = Table(rows, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
        ]))
        story.append(table)
        doc.build(story)
        return out
    
    