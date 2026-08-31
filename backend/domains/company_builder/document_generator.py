"""
Output Document Generator

Converts stage results into readable HTML documents that can be
printed/saved as PDF by the browser's print function.
No LaTeX, no separate service needed.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any
from domains.company_builder.delegation_models import DelegationGraph, OutputDocument

logger = logging.getLogger(__name__)


STAGE_DISPLAY_NAMES = {
    "REQUIREMENTS_DISCOVERY": "Requirements Discovery",
    "FEASIBILITY_ANALYSIS": "Feasibility Analysis Report",
    "GROWTH_STRATEGY": "Growth Strategy",
    "BRAND_IDENTITY": "Brand Identity Guide",
    "LOGO_CREATION": "Logo Design Brief",
    "POSTER_CREATION": "Promotional Poster Brief",
    "WEBSITE_CREATION": "Website Development Spec",
    "PITCH_DECK_CREATION": "Investor Pitch Deck",
}


def _simple_markdown_to_html(text: str) -> str:
    """Converts basic markdown (headings, bold, lists) to HTML for the report."""
    if not text:
        return ""
    
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Headings
    text = re.sub(r'^###\s+(.+)$', r'<h3 style="font-size:18px;font-weight:700;color:#1a1a2e;margin:24px 0 12px;border-bottom:2px solid #eee;padding-bottom:6px;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.+)$', r'<h2 style="font-size:22px;font-weight:700;color:#1a1a2e;margin:28px 0 16px;border-bottom:2px solid #ddd;padding-bottom:8px;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.+)$', r'<h1 style="font-size:26px;font-weight:800;color:#111;margin:32px 0 20px;border-bottom:3px solid #6366f1;padding-bottom:10px;">\1</h1>', text, flags=re.MULTILINE)
    
    # Bold / Italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    
    # Lists
    text = re.sub(r'^-\s+(.+)$', r'<li style="margin-left:24px;margin-bottom:6px;">\1</li>', text, flags=re.MULTILINE)
    
    # Paragraphs (split by double newline)
    html = ""
    for p in text.split('\n\n'):
        p = p.strip()
        if not p: continue
        if p.startswith('<h') or p.startswith('<li'):
            if p.startswith('<li'):
                html += f'<ul style="margin-bottom:16px;">{p}</ul>'
            else:
                html += p
        else:
            p = p.replace('\n', '<br/>')
            html += f'<p style="margin-bottom:16px;line-height:1.7;">{p}</p>'
            
    return html


def generate_html_document(
    workflow_id: str,
    stage: str,
    prompt: str,
    delegation_graph: DelegationGraph,
    company_name: str = "Your Company",
    agent_output: str = ""
) -> OutputDocument:
    """
    Generates a professional HTML document for any pipeline stage.
    The HTML is browser-printable as PDF.
    """
    stage_title = STAGE_DISPLAY_NAMES.get(stage, stage.replace("_", " ").title())
    date_str = datetime.now().strftime("%B %d, %Y")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # Build team sections
    team_sections_html = ""
    for team in delegation_graph.teams:
        member_rows = ""
        for m in team.members:
            status_badge = f"""<span style="
                background:{team.team_color}22;
                color:{team.team_color};
                border:1px solid {team.team_color}66;
                padding:2px 10px;
                border-radius:20px;
                font-size:11px;
                font-weight:600;
            ">{m.status}</span>"""

            member_rows += f"""
            <div style="
                display:flex;
                align-items:flex-start;
                gap:16px;
                padding:16px;
                border-left:3px solid {team.team_color};
                margin-bottom:12px;
                background:#fafbff;
                border-radius:0 8px 8px 0;
            ">
                <div style="
                    width:44px;height:44px;
                    border-radius:50%;
                    background:linear-gradient(135deg,{team.team_color},{team.team_color}88);
                    display:flex;align-items:center;justify-content:center;
                    color:white;font-weight:700;font-size:18px;
                    flex-shrink:0;
                ">{m.member_name[0]}</div>
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                        <div>
                            <strong style="font-size:14px;color:#1a1a2e;">{m.member_name}</strong>
                            <span style="color:#888;font-size:12px;margin-left:8px;">· {m.member_role}</span>
                        </div>
                        {status_badge}
                    </div>
                    <div style="font-size:13px;font-weight:600;color:#333;margin-bottom:4px;">📋 {m.task_title}</div>
                    <div style="font-size:12px;color:#555;margin-bottom:6px;">{m.task_description}</div>
                    <div style="font-size:11px;color:{team.team_color};font-weight:600;">
                        📦 Expected Output: {m.expected_output}
                    </div>
                </div>
            </div>"""

        team_sections_html += f"""
        <div style="margin-bottom:32px;page-break-inside:avoid;">
            <div style="
                display:flex;align-items:center;gap:12px;
                padding:12px 20px;
                background:linear-gradient(135deg,{team.team_color}18,{team.team_color}05);
                border-left:5px solid {team.team_color};
                border-radius:0 8px 8px 0;
                margin-bottom:16px;
            ">
                <div style="
                    width:42px;height:42px;border-radius:50%;
                    background:{team.team_color};
                    display:flex;align-items:center;justify-content:center;
                    color:white;font-weight:700;font-size:14px;
                ">{team.team_name[:2]}</div>
                <div>
                    <div style="font-size:16px;font-weight:700;color:#1a1a2e;">{team.team_name} TEAM</div>
                    <div style="font-size:12px;color:#666;">{team.manager_name} · {team.manager_role}</div>
                    <div style="font-size:11px;color:#888;margin-top:2px;font-style:italic;">{team.objective}</div>
                </div>
            </div>
            {member_rows}
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{stage_title} — {company_name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    font-family:'Inter',sans-serif;
    background:#fff;
    color:#1a1a2e;
    line-height:1.6;
    padding:0;
  }}
  @media print {{
    .no-print {{ display:none !important; }}
    body {{ padding:0; }}
    .page {{ padding:32px; }}
  }}
  .page {{ max-width:900px; margin:0 auto; padding:48px 32px; }}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div style="
    display:flex;align-items:flex-start;justify-content:space-between;
    padding-bottom:24px;
    border-bottom:2px solid #f0f0f0;
    margin-bottom:32px;
  ">
    <div>
      <div style="
        display:inline-block;
        background:linear-gradient(135deg,#5e81f4,#8b5cf6);
        color:white;
        padding:4px 14px;
        border-radius:20px;
        font-size:11px;
        font-weight:600;
        letter-spacing:1px;
        margin-bottom:8px;
      ">MYCEL AUTONOMOUS COMPANY BUILDER</div>
      <h1 style="font-size:28px;font-weight:700;color:#1a1a2e;margin-bottom:4px;">{stage_title}</h1>
      <div style="font-size:14px;color:#666;">{company_name}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:13px;color:#888;">{date_str}</div>
      <div style="font-size:11px;color:#aaa;margin-top:4px;">Generated {generated_at}</div>
      <div style="
        margin-top:8px;
        background:#f0f4ff;
        border:1px solid #c7d2fe;
        color:#4f46e5;
        padding:4px 12px;
        border-radius:8px;
        font-size:11px;
        font-weight:600;
      ">WORKFLOW: {workflow_id[:16]}...</div>
    </div>
  </div>

  <!-- User Prompt -->
  <div style="
    background:#f8f9ff;
    border-left:4px solid #5e81f4;
    padding:16px 20px;
    border-radius:0 8px 8px 0;
    margin-bottom:32px;
  ">
    <div style="font-size:11px;font-weight:600;color:#5e81f4;letter-spacing:1px;margin-bottom:6px;">📝 USER BRIEF</div>
    <div style="font-size:14px;color:#333;font-style:italic;">{prompt}</div>
  </div>

  <!-- Summary Stats -->
  <div style="
    display:grid;grid-template-columns:repeat(3,1fr);gap:16px;
    margin-bottom:48px;
  ">
    <div style="
      padding:16px;border-radius:12px;
      background:linear-gradient(135deg,#5e81f422,#5e81f408);
      border:1px solid #5e81f433;
      text-align:center;
    ">
      <div style="font-size:28px;font-weight:700;color:#5e81f4;">{len(delegation_graph.teams)}</div>
      <div style="font-size:12px;color:#666;margin-top:2px;">Teams Engaged</div>
    </div>
    <div style="
      padding:16px;border-radius:12px;
      background:linear-gradient(135deg,#2ec4b622,#2ec4b608);
      border:1px solid #2ec4b633;
      text-align:center;
    ">
      <div style="font-size:28px;font-weight:700;color:#2ec4b6;">{delegation_graph.total_members_assigned}</div>
      <div style="font-size:12px;color:#666;margin-top:2px;">Members Assigned</div>
    </div>
    <div style="
      padding:16px;border-radius:12px;
      background:linear-gradient(135deg,#f4a26122,#f4a26108);
      border:1px solid #f4a26133;
      text-align:center;
    ">
      <div style="font-size:28px;font-weight:700;color:#f4a261;">{delegation_graph.total_tasks}</div>
      <div style="font-size:12px;color:#666;margin-top:2px;">Tasks Created</div>
    </div>
  </div>

  <!-- Agent Output Section -->
  <div style="margin-bottom:64px;">
    <h2 style="font-size:22px;font-weight:700;color:#1a1a2e;margin-bottom:24px;border-bottom:2px solid #e0e0e0;padding-bottom:8px;">
      ✨ Final Delivered Result
    </h2>
    <div style="font-size:15px;color:#333;line-height:1.8;">
      {_simple_markdown_to_html(agent_output)}
    </div>
  </div>

  <!-- Team Delegations -->
  <h2 style="font-size:22px;font-weight:700;color:#1a1a2e;margin-bottom:20px;border-bottom:2px solid #e0e0e0;padding-bottom:8px;page-break-before:always;">
    🏢 Team Delegation Breakdown
  </h2>
  {team_sections_html}

  <!-- Footer -->
  <div style="
    margin-top:48px;
    padding-top:24px;
    border-top:1px solid #f0f0f0;
    display:flex;
    align-items:center;
    justify-content:space-between;
  ">
    <div style="font-size:11px;color:#bbb;">
      Mycel Autonomous Company Builder · Powered by AI
    </div>
    <div class="no-print" style="display:flex;gap:12px;">
      <button onclick="window.print()" style="
        background:#5e81f4;color:white;
        border:none;border-radius:8px;
        padding:10px 24px;
        font-size:13px;font-weight:600;
        cursor:pointer;
        font-family:'Inter',sans-serif;
      ">🖨️ Save as PDF</button>
    </div>
    <div style="font-size:11px;color:#bbb;">Confidential — Internal Use</div>
  </div>

</div>
</body>
</html>"""

    return OutputDocument(
        workflow_id=workflow_id,
        stage=stage,
        title=f"{stage_title} — {company_name}",
        format="html",
        content_html=html,
    )
