import csv
import html
import io
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models import ActivityEvent, Alert, RuleConfig, AlertReviewHistory, Workspace
from app.schemas.report import ReportFilterParams, AuditReportJSON, ReportSummary


def sanitize_csv_cell(val: Any) -> str:
    """
    Neutralizes CSV formula injection attacks by prepending an apostrophe (')
    if the cell text starts with '=', '+', '-', '@', tab, or carriage return.
    """
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


def build_audit_dataset(
    db: Session,
    workspace_id: str,
    filters: ReportFilterParams,
) -> Dict[str, Any]:
    # Query workspace
    ws = db.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
    
    # Query rules
    rules_stmt = select(RuleConfig).where(RuleConfig.workspace_id == workspace_id)
    rules = db.execute(rules_stmt).scalars().all()

    # Query events
    event_conds = [ActivityEvent.workspace_id == workspace_id]
    if filters.date_from:
        event_conds.append(ActivityEvent.timestamp >= filters.date_from)
    if filters.date_to:
        event_conds.append(ActivityEvent.timestamp <= filters.date_to)
    if filters.actor:
        event_conds.append(ActivityEvent.actor == filters.actor)

    events_stmt = select(ActivityEvent).where(and_(*event_conds)).order_by(ActivityEvent.timestamp.desc())
    events = db.execute(events_stmt).scalars().all()

    # Query alerts
    alert_conds = [Alert.workspace_id == workspace_id]
    if filters.date_from:
        alert_conds.append(Alert.trigger_time >= filters.date_from)
    if filters.date_to:
        alert_conds.append(Alert.trigger_time <= filters.date_to)
    if filters.severity:
        alert_conds.append(Alert.severity == filters.severity)
    if filters.review_status:
        alert_conds.append(Alert.review_status == filters.review_status)
    if filters.rule_code:
        alert_conds.append(Alert.rule_code == filters.rule_code)
    if filters.actor:
        alert_conds.append(Alert.actor == filters.actor)

    alerts_stmt = select(Alert).where(and_(*alert_conds)).order_by(Alert.trigger_time.desc())
    alerts = db.execute(alerts_stmt).scalars().all()

    # Compute summary
    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    rev_counts = {"Open": 0, "Investigating": 0, "Resolved": 0, "False Positive": 0}

    for a in alerts:
        sev_counts[a.severity] = sev_counts.get(a.severity, 0) + 1
        rev_counts[a.review_status] = rev_counts.get(a.review_status, 0) + 1

    summary = ReportSummary(
        total_events_in_scope=len(events),
        total_alerts_in_scope=len(alerts),
        critical_alerts=sev_counts["Critical"],
        high_alerts=sev_counts["High"],
        medium_alerts=sev_counts["Medium"],
        low_alerts=sev_counts["Low"],
        open_alerts=rev_counts["Open"],
        investigating_alerts=rev_counts["Investigating"],
        resolved_alerts=rev_counts["Resolved"],
        false_positives=rev_counts["False Positive"],
    )

    return {
        "workspace": ws,
        "rules": rules,
        "events": events,
        "alerts": alerts,
        "summary": summary,
        "filters": filters,
    }


def generate_alerts_csv(db: Session, workspace_id: str, filters: ReportFilterParams) -> str:
    data = build_audit_dataset(db, workspace_id, filters)
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "Alert ID",
        "Trigger Time (UTC)",
        "Rule Code",
        "Rule Version",
        "Severity",
        "Actor",
        "Target",
        "Source IP",
        "Reason",
        "Review Status",
        "Active Detection",
        "Deactivation Reason",
        "Recommended Action",
    ]
    writer.writerow(headers)

    for a in data["alerts"]:
        row = [
            sanitize_csv_cell(a.id),
            sanitize_csv_cell(a.trigger_time.isoformat() if a.trigger_time else ""),
            sanitize_csv_cell(a.rule_code),
            sanitize_csv_cell(a.rule_version),
            sanitize_csv_cell(a.severity),
            sanitize_csv_cell(a.actor),
            sanitize_csv_cell(a.target),
            sanitize_csv_cell(a.source_ip),
            sanitize_csv_cell(a.reason),
            sanitize_csv_cell(a.review_status),
            sanitize_csv_cell("Yes" if a.is_active else "No"),
            sanitize_csv_cell(a.deactivation_reason or ""),
            sanitize_csv_cell(a.recommended_action),
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_events_csv(db: Session, workspace_id: str, filters: ReportFilterParams) -> str:
    data = build_audit_dataset(db, workspace_id, filters)
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "timestamp",
        "actor",
        "action",
        "target",
        "status",
        "source_ip",
        "actor_role",
        "target_role",
        "previous_role",
        "approved",
        "approval_reference",
        "command",
        "details",
        "event_id",
        "fingerprint",
    ]
    writer.writerow(headers)

    for e in data["events"]:
        row = [
            sanitize_csv_cell(e.timestamp.isoformat() if e.timestamp else ""),
            sanitize_csv_cell(e.actor),
            sanitize_csv_cell(e.action),
            sanitize_csv_cell(e.target),
            sanitize_csv_cell(e.status),
            sanitize_csv_cell(e.source_ip),
            sanitize_csv_cell(e.actor_role or ""),
            sanitize_csv_cell(e.target_role or ""),
            sanitize_csv_cell(e.previous_role or ""),
            sanitize_csv_cell("None" if e.approved is None else str(e.approved).lower()),
            sanitize_csv_cell(e.approval_reference or ""),
            sanitize_csv_cell(e.command or ""),
            sanitize_csv_cell(e.details or ""),
            sanitize_csv_cell(e.id),
            sanitize_csv_cell(e.fingerprint),
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_audit_json(db: Session, workspace_id: str, filters: ReportFilterParams) -> Dict[str, Any]:
    data = build_audit_dataset(db, workspace_id, filters)
    now = datetime.now(timezone.utc)
    report_id = f"REP-JSON-{str(uuid.uuid4())[:8].upper()}"

    serialized_rules = []
    for r in data["rules"]:
        serialized_rules.append({
            "rule_code": r.rule_code,
            "name": r.name,
            "severity": r.severity,
            "is_enabled": r.is_enabled,
            "version": r.version,
            "config": json.loads(r.config_json or "{}"),
        })

    serialized_alerts = []
    for a in data["alerts"]:
        # Get reviews
        reviews = []
        for rev in a.reviews:
            reviews.append({
                "previous_status": rev.previous_status,
                "new_status": rev.new_status,
                "note": rev.note,
                "author": rev.author,
                "timestamp": rev.created_at.isoformat() if rev.created_at else None,
            })
        
        serialized_alerts.append({
            "id": a.id,
            "rule_code": a.rule_code,
            "rule_version": a.rule_version,
            "severity": a.severity,
            "trigger_time": a.trigger_time.isoformat() if a.trigger_time else None,
            "actor": a.actor,
            "target": a.target,
            "source_ip": a.source_ip,
            "reason": a.reason,
            "evidence": json.loads(a.evidence_json or "{}"),
            "recommended_action": a.recommended_action,
            "review_status": a.review_status,
            "is_active": a.is_active,
            "deactivation_reason": a.deactivation_reason,
            "reviews": reviews,
        })

    serialized_events_sample = []
    for e in data["events"][:50]:
        serialized_events_sample.append({
            "id": e.id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "actor": e.actor,
            "action": e.action,
            "target": e.target,
            "status": e.status,
            "source_ip": e.source_ip,
            "approved": e.approved,
            "details": e.details,
        })

    return {
        "title": "Sentinel — Privileged Access Monitoring Audit Report",
        "report_id": report_id,
        "generated_at": now.isoformat(),
        "timezone": "UTC",
        "workspace_id": workspace_id,
        "filters_applied": filters.model_dump(exclude_none=True),
        "summary": data["summary"].model_dump(),
        "rules_in_force": serialized_rules,
        "alerts": serialized_alerts,
        "events_sample": serialized_events_sample,
        "disclaimer": (
            "NOTICE: Detections generated by Sentinel represent deterministic security heuristics and indicators of potential risk. "
            "Rule matches do not constitute definitive proof of malicious intent or unauthorized compromise. "
            "Security analysts must validate evidence against organizational change authorizations, ticket systems, and host forensics."
        ),
    }


def generate_printable_html_report(db: Session, workspace_id: str, filters: ReportFilterParams) -> str:
    data = build_audit_dataset(db, workspace_id, filters)
    now = datetime.now(timezone.utc)
    report_id = f"REP-SEC-{str(uuid.uuid4())[:8].upper()}"
    sumry = data["summary"]

    # Build alerts HTML rows
    alert_rows = []
    for a in data["alerts"]:
        sev_color = {
            "Critical": "#dc2626",
            "High": "#ea580c",
            "Medium": "#2563eb",
            "Low": "#475569",
        }.get(a.severity, "#475569")

        status_badge = {
            "Open": "#fef3c7; color: #92400e",
            "Investigating": "#e0f2fe; color: #075985",
            "Resolved": "#dcfce7; color: #166534",
            "False Positive": "#f1f5f9; color: #475569",
        }.get(a.review_status, "#f1f5f9; color: #475569")

        # review notes
        notes_html = ""
        if a.reviews:
            notes_items = "".join(
                f"<div style='font-size: 11px; margin-top: 4px; padding: 4px; background: #f8fafc; border-left: 2px solid #0d9488;'><strong>{html.escape(rev.author)}</strong> ({rev.new_status}): {html.escape(rev.note)}</div>"
                for rev in a.reviews
            )
            notes_html = f"<div style='margin-top: 6px;'>{notes_items}</div>"

        evidence_parsed = json.loads(a.evidence_json or "{}")
        evidence_snippet = json.dumps(evidence_parsed, indent=2)

        alert_rows.append(f"""
        <tr style="border-bottom: 1px solid #e2e8f0; font-size: 12px;">
            <td style="padding: 8px; vertical-align: top; font-family: monospace;">{html.escape(a.id)}</td>
            <td style="padding: 8px; vertical-align: top;">
                <span style="font-weight: 600; color: {sev_color};">[{html.escape(a.severity)}]</span> {html.escape(a.rule_code)} (v{a.rule_version})
            </td>
            <td style="padding: 8px; vertical-align: top; white-space: nowrap;">{html.escape(a.trigger_time.strftime('%Y-%m-%d %H:%M:%S UTC') if a.trigger_time else '')}</td>
            <td style="padding: 8px; vertical-align: top;"><strong>{html.escape(a.actor)}</strong> &rarr; {html.escape(a.target)}<br/><span style="color:#64748b; font-size: 11px;">{html.escape(a.source_ip)}</span></td>
            <td style="padding: 8px; vertical-align: top;">
                <div>{html.escape(a.reason)}</div>
                <div style="margin-top: 4px; color: #475569; font-size: 11px;"><strong>Action:</strong> {html.escape(a.recommended_action)}</div>
                <details style="margin-top: 4px; font-size: 11px;">
                    <summary style="cursor: pointer; color: #0d9488;">View Evidence JSON</summary>
                    <pre style="background: #f1f5f9; padding: 6px; border-radius: 4px; overflow-x: auto; margin-top: 4px;">{html.escape(evidence_snippet)}</pre>
                </details>
                {notes_html}
            </td>
            <td style="padding: 8px; vertical-align: top; white-space: nowrap;">
                <span style="background: {status_badge}; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 11px;">{html.escape(a.review_status)}</span>
                {"" if a.is_active else "<br/><span style='color: #94a3b8; font-size: 10px;'>(Inactive detection)</span>"}
            </td>
        </tr>
        """)

    alerts_table_html = "".join(alert_rows) if alert_rows else "<tr><td colspan='6' style='padding: 16px; text-align: center; color: #64748b;'>No alerts found in scope.</td></tr>"

    # Rules table
    rule_rows = []
    for r in data["rules"]:
        rule_rows.append(f"""
        <tr style="border-bottom: 1px solid #f1f5f9; font-size: 12px;">
            <td style="padding: 6px 8px; font-weight: 600;">{html.escape(r.rule_code)}</td>
            <td style="padding: 6px 8px;">{html.escape(r.name)}</td>
            <td style="padding: 6px 8px;">{html.escape(r.severity)}</td>
            <td style="padding: 6px 8px;">{'<span style="color: #16a34a;">Enabled</span>' if r.is_enabled else '<span style="color: #94a3b8;">Disabled</span>'}</td>
            <td style="padding: 6px 8px; color: #64748b; font-family: monospace; font-size: 11px;">{html.escape(r.config_json or "{}")}</td>
            <td style="padding: 6px 8px;">v{r.version}</td>
        </tr>
        """)
    rules_table_html = "".join(rule_rows)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel Security Audit Report - {report_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            background: #ffffff;
            margin: 0;
            padding: 32px;
            font-size: 13px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0d9488;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .title-block h1 {{
            margin: 0 0 4px 0;
            font-size: 24px;
            color: #0f172a;
        }}
        .title-block .subtitle {{
            margin: 0;
            color: #475569;
            font-size: 14px;
        }}
        .meta-block {{
            text-align: right;
            font-size: 12px;
            color: #64748b;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .summary-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            text-align: center;
        }}
        .summary-card .num {{
            font-size: 22px;
            font-weight: 700;
            color: #0f172a;
        }}
        .summary-card .label {{
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
        }}
        th {{
            background: #f1f5f9;
            text-align: left;
            padding: 8px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #475569;
            border-bottom: 1px solid #cbd5e1;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            margin: 24px 0 12px 0;
            color: #0f172a;
            border-left: 4px solid #0d9488;
            padding-left: 8px;
        }}
        .disclaimer-box {{
            background: #fffbeb;
            border: 1px solid #fef3c7;
            border-left: 4px solid #d97706;
            padding: 12px 16px;
            border-radius: 4px;
            font-size: 12px;
            color: #92400e;
            margin-top: 32px;
        }}
        .action-bar {{
            margin-bottom: 24px;
            text-align: right;
        }}
        .print-btn {{
            background: #0d9488;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
        }}
        @media print {{
            .action-bar {{ display: none; }}
            body {{ padding: 0; }}
            details {{ display: block !important; }}
            summary {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="action-bar">
        <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
    </div>

    <div class="header">
        <div class="title-block">
            <h1>Sentinel</h1>
            <p class="subtitle">Privileged Access Monitoring Tool &bull; Security Audit Report</p>
        </div>
        <div class="meta-block">
            <div><strong>Report ID:</strong> {report_id}</div>
            <div><strong>Generated:</strong> {now.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
            <div><strong>Workspace ID:</strong> {html.escape(workspace_id[:8])}...</div>
        </div>
    </div>

    <div class="summary-grid">
        <div class="summary-card">
            <div class="num">{sumry.total_events_in_scope}</div>
            <div class="label">Events in Scope</div>
        </div>
        <div class="summary-card">
            <div class="num" style="color: #dc2626;">{sumry.critical_alerts}</div>
            <div class="label">Critical Alerts</div>
        </div>
        <div class="summary-card">
            <div class="num" style="color: #ea580c;">{sumry.high_alerts}</div>
            <div class="label">High Risk Alerts</div>
        </div>
        <div class="summary-card">
            <div class="num" style="color: #0284c7;">{sumry.open_alerts + sumry.investigating_alerts}</div>
            <div class="label">Open / In Review</div>
        </div>
    </div>

    <div class="section-title">Security Alerts &amp; Evidence Log</div>
    <table>
        <thead>
            <tr>
                <th>Alert ID</th>
                <th>Severity &amp; Rule</th>
                <th>Trigger Time</th>
                <th>Actor / Target / IP</th>
                <th>Detection Reason &amp; Recommendations</th>
                <th>Review Status</th>
            </tr>
        </thead>
        <tbody>
            {alerts_table_html}
        </tbody>
    </table>

    <div class="section-title">Detection Rules in Force</div>
    <table>
        <thead>
            <tr>
                <th>Code</th>
                <th>Rule Name</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Active Configuration</th>
                <th>Version</th>
            </tr>
        </thead>
        <tbody>
            {rules_table_html}
        </tbody>
    </table>

    <div class="disclaimer-box">
        <strong>Investigation &amp; Legal Disclaimer:</strong><br/>
        This audit report was automatically compiled by Sentinel Privileged Access Monitoring Engine.
        Rule triggers indicate statistical or policy deviations and potential operational risks; they do not constitute definitive legal proof of compromise.
        Corroborating log evidence, change tickets, and human security analyst reviews must be considered before pursuing adverse actions.
    </div>
</body>
</html>
"""
    return html_doc
