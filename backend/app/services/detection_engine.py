import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models import ActivityEvent, Alert, AlertEventLink, RuleConfig, AnalysisRun


def parse_time_str(time_str: str) -> Tuple[int, int]:
    parts = time_str.strip().split(":")
    return int(parts[0]), int(parts[1])


def is_outside_business_hours(
    dt: datetime,
    start_str: str,
    end_str: str,
    tz_name: str = "UTC"
) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    try:
        target_tz = pytz.timezone(tz_name)
    except Exception:
        target_tz = pytz.UTC

    local_dt = dt.astimezone(target_tz)
    event_time_min = local_dt.hour * 60 + local_dt.minute

    s_h, s_m = parse_time_str(start_str)
    e_h, e_m = parse_time_str(end_str)
    start_min = s_h * 60 + s_m
    end_min = e_h * 60 + e_m

    if start_min <= end_min:
        # Standard daytime schedule, e.g. 08:00 - 18:00
        return event_time_min < start_min or event_time_min > end_min
    else:
        # Overnight schedule, e.g. 20:00 - 04:00
        # Inside if >= 20:00 or <= 04:00
        # Outside if 04:00 < event_time < 20:00
        return end_min < event_time_min < start_min


class AlertCandidate:
    def __init__(
        self,
        rule_code: str,
        rule_version: int,
        severity: str,
        trigger_time: datetime,
        actor: str,
        target: str,
        source_ip: str,
        reason: str,
        evidence: Dict[str, Any],
        recommended_action: str,
        dedup_key: str,
        event_ids: List[str],
    ):
        self.rule_code = rule_code
        self.rule_version = rule_version
        self.severity = severity
        self.trigger_time = trigger_time
        self.actor = actor
        self.target = target
        self.source_ip = source_ip
        self.reason = reason
        self.evidence = evidence
        self.recommended_action = recommended_action
        self.dedup_key = dedup_key
        self.event_ids = event_ids


def evaluate_rules_for_events(
    events: List[ActivityEvent],
    rule_configs: Dict[str, RuleConfig],
) -> List[AlertCandidate]:
    candidates: List[AlertCandidate] = []

    # Ensure all timestamps are UTC-aware
    for e in events:
        if e.timestamp and e.timestamp.tzinfo is None:
            e.timestamp = e.timestamp.replace(tzinfo=timezone.utc)
    
    # Sort events by timestamp ascending for deterministic time-series correlation
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    # 1. Single-event and direct transition rules (R01 - R08, R10)
    for event in sorted_events:
        is_success = (event.status.lower() == "success")

        # R01: Administrator account created
        rc1 = rule_configs.get("R01")
        if rc1 and rc1.is_enabled and is_success and event.action == "create_admin":
            candidates.append(AlertCandidate(
                rule_code="R01",
                rule_version=rc1.version,
                severity=rc1.severity,
                trigger_time=event.timestamp,
                actor=event.actor,
                target=event.target,
                source_ip=event.source_ip,
                reason=f"Administrator account '{event.target}' was successfully created by '{event.actor}'.",
                evidence={
                    "event_id": event.id,
                    "action": event.action,
                    "target_role": event.target_role,
                    "source_ip": event.source_ip,
                    "details": event.details,
                    "command": event.command,
                },
                recommended_action="Verify creation against authorized change management tickets and confirm administrative identity onboarding.",
                dedup_key=f"R01:{event.fingerprint}",
                event_ids=[event.id],
            ))

        # R02: Privilege escalation
        rc2 = rule_configs.get("R02")
        if rc2 and rc2.is_enabled and is_success and event.action == "change_privilege":
            r2_cfg = json.loads(rc2.config_json or "{}")
            elevated_roles = set(r.lower() for r in r2_cfg.get("elevated_roles", [
                "admin", "root", "superuser", "administrator", "global_admin"
            ]))

            prev_role = (event.previous_role or "").strip().lower()
            target_role = (event.target_role or "").strip().lower()

            # Check if role details are missing
            if not prev_role or not target_role:
                candidates.append(AlertCandidate(
                    rule_code="R02",
                    rule_version=rc2.version,
                    severity="High",
                    trigger_time=event.timestamp,
                    actor=event.actor,
                    target=event.target,
                    source_ip=event.source_ip,
                    reason=f"Privilege change requires review: Role transition details (previous_role/target_role) were omitted for target '{event.target}'.",
                    evidence={
                        "event_id": event.id,
                        "action": event.action,
                        "actor": event.actor,
                        "previous_role": event.previous_role,
                        "target_role": event.target_role,
                        "source_ip": event.source_ip,
                        "details": event.details,
                    },
                    recommended_action="Inspect identity management logs to confirm previous and granted roles; verify ticket justification.",
                    dedup_key=f"R02:missing_roles:{event.fingerprint}",
                    event_ids=[event.id],
                ))
            else:
                # Both roles provided
                target_is_elevated = any(target_role == er or target_role.endswith(er) for er in elevated_roles)
                prev_is_elevated = any(prev_role == er or prev_role.endswith(er) for er in elevated_roles)

                # Check for explicit downgrade: from elevated to non-elevated -> NOT escalation!
                if prev_is_elevated and not target_is_elevated:
                    pass  # Explicit downgrade, no alert
                elif target_is_elevated and (not prev_is_elevated or prev_role != target_role):
                    # True escalation
                    candidates.append(AlertCandidate(
                        rule_code="R02",
                        rule_version=rc2.version,
                        severity=rc2.severity,  # Critical
                        trigger_time=event.timestamp,
                        actor=event.actor,
                        target=event.target,
                        source_ip=event.source_ip,
                        reason=f"Privilege escalation detected: Target '{event.target}' elevated from role '{event.previous_role}' to '{event.target_role}' by '{event.actor}'.",
                        evidence={
                            "event_id": event.id,
                            "action": event.action,
                            "previous_role": event.previous_role,
                            "target_role": event.target_role,
                            "source_ip": event.source_ip,
                            "details": event.details,
                            "command": event.command,
                        },
                        recommended_action="Immediately validate privilege elevation approval in PAM/ticketing system; revoke access if unapproved.",
                        dedup_key=f"R02:escalated:{event.fingerprint}",
                        event_ids=[event.id],
                    ))

        # R03: Audit logs cleared
        rc3 = rule_configs.get("R03")
        if rc3 and rc3.is_enabled and is_success and event.action == "clear_logs":
            candidates.append(AlertCandidate(
                rule_code="R03",
                rule_version=rc3.version,
                severity=rc3.severity,
                trigger_time=event.timestamp,
                actor=event.actor,
                target=event.target,
                source_ip=event.source_ip,
                reason=f"Audit or security logs cleared by actor '{event.actor}' on resource '{event.target}'.",
                evidence={
                    "event_id": event.id,
                    "action": event.action,
                    "command": event.command,
                    "source_ip": event.source_ip,
                    "details": event.details,
                },
                recommended_action="Isolate origin IP, initiate security incident triage, and recover log streams from secondary/immutable storage.",
                dedup_key=f"R03:{event.fingerprint}",
                event_ids=[event.id],
            ))

        # R04: Security monitoring disabled
        rc4 = rule_configs.get("R04")
        if rc4 and rc4.is_enabled and is_success and event.action == "disable_security":
            candidates.append(AlertCandidate(
                rule_code="R04",
                rule_version=rc4.version,
                severity=rc4.severity,
                trigger_time=event.timestamp,
                actor=event.actor,
                target=event.target,
                source_ip=event.source_ip,
                reason=f"Security monitoring or telemetry controls disabled by '{event.actor}' on '{event.target}'.",
                evidence={
                    "event_id": event.id,
                    "action": event.action,
                    "command": event.command,
                    "source_ip": event.source_ip,
                    "details": event.details,
                },
                recommended_action="Immediately re-enable monitoring agents and check endpoint for unauthorized process activity or tampering.",
                dedup_key=f"R04:{event.fingerprint}",
                event_ids=[event.id],
            ))

        # R05: Account deleted
        rc5 = rule_configs.get("R05")
        if rc5 and rc5.is_enabled and is_success and event.action == "delete_user":
            candidates.append(AlertCandidate(
                rule_code="R05",
                rule_version=rc5.version,
                severity=rc5.severity,
                trigger_time=event.timestamp,
                actor=event.actor,
                target=event.target,
                source_ip=event.source_ip,
                reason=f"Account '{event.target}' was deleted by administrative user '{event.actor}'.",
                evidence={
                    "event_id": event.id,
                    "action": event.action,
                    "source_ip": event.source_ip,
                    "details": event.details,
                },
                recommended_action="Validate account offboarding request with IAM/HR directory and audit recent actions by deleted account.",
                dedup_key=f"R05:{event.fingerprint}",
                event_ids=[event.id],
            ))

        # R06: Administrator password reset
        rc6 = rule_configs.get("R06")
        if rc6 and rc6.is_enabled and is_success and event.action == "reset_admin_password":
            candidates.append(AlertCandidate(
                rule_code="R06",
                rule_version=rc6.version,
                severity=rc6.severity,
                trigger_time=event.timestamp,
                actor=event.actor,
                target=event.target,
                source_ip=event.source_ip,
                reason=f"Privileged administrator password reset performed by '{event.actor}' targeting '{event.target}'.",
                evidence={
                    "event_id": event.id,
                    "action": event.action,
                    "source_ip": event.source_ip,
                    "details": event.details,
                },
                recommended_action="Confirm identity with account owner out-of-band and verify multi-factor authentication enrollment.",
                dedup_key=f"R06:{event.fingerprint}",
                event_ids=[event.id],
            ))

        # R07: Sensitive data export
        rc7 = rule_configs.get("R07")
        if rc7 and rc7.is_enabled and is_success and event.action == "export_sensitive":
            candidates.append(AlertCandidate(
                rule_code="R07",
                rule_version=rc7.version,
                severity=rc7.severity,
                trigger_time=event.timestamp,
                actor=event.actor,
                target=event.target,
                source_ip=event.source_ip,
                reason=f"Sensitive or bulk data export executed by privileged account '{event.actor}' from '{event.target}'.",
                evidence={
                    "event_id": event.id,
                    "action": event.action,
                    "command": event.command,
                    "source_ip": event.source_ip,
                    "details": event.details,
                },
                recommended_action="Review data classification, volume exported, and DLP egress authorization reference.",
                dedup_key=f"R07:{event.fingerprint}",
                event_ids=[event.id],
            ))

        # R08: After-hours administrative activity
        rc8 = rule_configs.get("R08")
        if rc8 and rc8.is_enabled and is_success and event.action not in ("login", "logout"):
            r8_cfg = json.loads(rc8.config_json or "{}")
            b_start = r8_cfg.get("business_start", "08:00")
            b_end = r8_cfg.get("business_end", "18:00")
            tz_name = r8_cfg.get("timezone", "UTC")

            if is_outside_business_hours(event.timestamp, b_start, b_end, tz_name):
                candidates.append(AlertCandidate(
                    rule_code="R08",
                    rule_version=rc8.version,
                    severity=rc8.severity,
                    trigger_time=event.timestamp,
                    actor=event.actor,
                    target=event.target,
                    source_ip=event.source_ip,
                    reason=f"Administrative action '{event.action}' was executed outside standard business hours ({b_start}–{b_end} {tz_name}) by '{event.actor}'.",
                    evidence={
                        "event_id": event.id,
                        "action": event.action,
                        "event_time_utc": event.timestamp.isoformat(),
                        "configured_business_hours": f"{b_start} - {b_end} {tz_name}",
                        "source_ip": event.source_ip,
                        "details": event.details,
                    },
                    recommended_action="Cross-reference on-call schedule and emergency change authorization window.",
                    dedup_key=f"R08:{event.fingerprint}",
                    event_ids=[event.id],
                ))

        # R10: Explicitly unapproved privilege operation
        rc10 = rule_configs.get("R10")
        if rc10 and rc10.is_enabled and is_success and event.action in ("create_admin", "change_privilege") and event.approved is False:
            candidates.append(AlertCandidate(
                rule_code="R10",
                rule_version=rc10.version,
                severity=rc10.severity,
                trigger_time=event.timestamp,
                actor=event.actor,
                target=event.target,
                source_ip=event.source_ip,
                reason=f"Privileged operation '{event.action}' was executed despite log evidence explicitly denoting lack of approval (approved=false).",
                evidence={
                    "event_id": event.id,
                    "action": event.action,
                    "approved": event.approved,
                    "approval_reference": event.approval_reference,
                    "source_ip": event.source_ip,
                    "details": event.details,
                },
                recommended_action="Immediately revoke granted permissions, contact security operations, and flag for emergency compliance audit.",
                dedup_key=f"R10:{event.fingerprint}",
                event_ids=[event.id],
            ))

    # 2. Time-window correlation rule: R09 (Repeated failed logins)
    rc9 = rule_configs.get("R09")
    if rc9 and rc9.is_enabled:
        r9_cfg = json.loads(rc9.config_json or "{}")
        threshold = int(r9_cfg.get("threshold", 5))
        window_minutes = int(r9_cfg.get("window_minutes", 10))
        suppression_window_minutes = int(r9_cfg.get("suppression_window_minutes", 10))
        window_delta = timedelta(minutes=window_minutes)
        suppression_delta = timedelta(minutes=suppression_window_minutes)

        # Filter only failed login events
        failed_logins = [e for e in sorted_events if e.action == "login" and e.status.lower() == "failed"]
        
        # Group by (actor, source_ip)
        actor_ip_groups: Dict[Tuple[str, str], List[ActivityEvent]] = {}
        for fl in failed_logins:
            key = (fl.actor, fl.source_ip)
            if key not in actor_ip_groups:
                actor_ip_groups[key] = []
            actor_ip_groups[key].append(fl)

        for (actor, ip), grp_events in actor_ip_groups.items():
            if len(grp_events) < threshold:
                continue

            # Sliding window with alert suppression
            last_alert_time: Optional[datetime] = None
            active_alert_event_ids: List[str] = []

            for i in range(len(grp_events)):
                curr_event = grp_events[i]
                
                # Check previous events within rolling window ending at curr_event.timestamp
                window_start = curr_event.timestamp - window_delta
                events_in_window = [e for e in grp_events[:i+1] if e.timestamp >= window_start]

                if len(events_in_window) >= threshold:
                    # Check if suppressed by recent alert for this actor/ip
                    if last_alert_time is not None and (curr_event.timestamp - last_alert_time) < suppression_delta:
                        # Correlate event into ongoing burst
                        if candidates and candidates[-1].rule_code == "R09" and candidates[-1].actor == actor:
                            if curr_event.id not in candidates[-1].event_ids:
                                candidates[-1].event_ids.append(curr_event.id)
                        continue

                    # Trigger a new alert
                    trigger_time = curr_event.timestamp
                    earliest_event = events_in_window[0]
                    dedup_key = f"R09:{actor}:{ip}:{earliest_event.timestamp.isoformat()}"
                    
                    candidate = AlertCandidate(
                        rule_code="R09",
                        rule_version=rc9.version,
                        severity=rc9.severity,
                        trigger_time=trigger_time,
                        actor=actor,
                        target=curr_event.target,
                        source_ip=ip,
                        reason=f"Detected burst of {len(events_in_window)} failed login attempts for actor '{actor}' from IP '{ip}' within rolling {window_minutes}-minute window.",
                        evidence={
                            "failure_count": len(events_in_window),
                            "window_minutes": window_minutes,
                            "first_failure_time": earliest_event.timestamp.isoformat(),
                            "trigger_failure_time": trigger_time.isoformat(),
                            "source_ip": ip,
                            "actor": actor,
                            "event_ids": [e.id for e in events_in_window],
                        },
                        recommended_action="Implement temporary authentication backoff/rate limiting, inspect for credential stuffing, and notify user.",
                        dedup_key=dedup_key,
                        event_ids=[e.id for e in events_in_window],
                    )
                    candidates.append(candidate)
                    last_alert_time = trigger_time

    return candidates


def run_detection_pipeline(
    db: Session,
    workspace_id: str,
    trigger_type: str = "ingest",
) -> AnalysisRun:
    """
    Run detection engine for the workspace.
    - Idempotent and deterministic.
    - Re-evaluates all workspace events against current active rules.
    - Preserves existing analyst review status and notes for matched alerts.
    - Deactivates (is_active=False) alerts whose rules are disabled or no longer match.
    """
    # Load all rules for workspace
    rules_stmt = select(RuleConfig).where(RuleConfig.workspace_id == workspace_id)
    rule_configs = {rc.rule_code: rc for rc in db.execute(rules_stmt).scalars().all()}

    # Load all events for workspace
    events_stmt = select(ActivityEvent).where(ActivityEvent.workspace_id == workspace_id)
    events = db.execute(events_stmt).scalars().all()

    # Load existing alerts for workspace
    existing_alerts_stmt = select(Alert).where(Alert.workspace_id == workspace_id)
    existing_alerts = {a.dedup_key: a for a in db.execute(existing_alerts_stmt).scalars().all()}

    # Generate current candidates
    candidates = evaluate_rules_for_events(events, rule_configs)
    
    current_dedup_keys = set()
    alerts_created_count = 0
    now = datetime.now(timezone.utc)

    for cand in candidates:
        current_dedup_keys.add(cand.dedup_key)
        
        if cand.dedup_key in existing_alerts:
            # Alert already exists. Update version & activate if deactivated, but preserve review status and notes!
            existing = existing_alerts[cand.dedup_key]
            existing.rule_version = cand.rule_version
            existing.severity = cand.severity
            existing.reason = cand.reason
            existing.evidence_json = json.dumps(cand.evidence)
            existing.recommended_action = cand.recommended_action
            if not existing.is_active:
                existing.is_active = True
                existing.deactivation_reason = None
            
            # Ensure links exist
            linked_ids = {link.event_id for link in existing.event_links}
            for eid in cand.event_ids:
                if eid not in linked_ids:
                    db.add(AlertEventLink(alert_id=existing.id, event_id=eid))
        else:
            # Create new Alert
            alert_id = f"ALT-{str(uuid.uuid4())[:8].upper()}"
            new_alert = Alert(
                id=alert_id,
                workspace_id=workspace_id,
                rule_code=cand.rule_code,
                rule_version=cand.rule_version,
                severity=cand.severity,
                trigger_time=cand.trigger_time,
                actor=cand.actor,
                target=cand.target,
                source_ip=cand.source_ip,
                reason=cand.reason,
                evidence_json=json.dumps(cand.evidence),
                recommended_action=cand.recommended_action,
                review_status="Open",
                is_active=True,
                deactivation_reason=None,
                dedup_key=cand.dedup_key,
                created_at=now,
                updated_at=now,
            )
            db.add(new_alert)
            db.flush()

            for eid in cand.event_ids:
                db.add(AlertEventLink(alert_id=new_alert.id, event_id=eid))
            
            existing_alerts[cand.dedup_key] = new_alert
            alerts_created_count += 1

    # Deactivate alerts that no longer match the active rules
    alerts_deactivated_count = 0
    for dedup_key, alert in existing_alerts.items():
        if dedup_key not in current_dedup_keys and alert.is_active:
            alert.is_active = False
            alert.deactivation_reason = f"Rule condition no longer matches active detection criteria (Reanalysis on {now.strftime('%Y-%m-%d %H:%M:%S UTC')})."
            alerts_deactivated_count += 1

    # Record analysis run
    run = AnalysisRun(
        workspace_id=workspace_id,
        trigger_type=trigger_type,
        events_analyzed=len(events),
        alerts_created=alerts_created_count,
        alerts_deactivated=alerts_deactivated_count,
        created_at=now,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return run
