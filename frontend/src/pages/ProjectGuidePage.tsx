import React from 'react';
import {
  BookOpen,
  ShieldAlert,
  Server,
  Layers,
  CheckCircle,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Lock,
  Workflow,
  Download,
} from 'lucide-react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { NavTab } from '../components/layout/Sidebar';

interface ProjectGuidePageProps {
  onNavigateTab: (tab: NavTab) => void;
  onSeedDemo: () => void;
}

export const ProjectGuidePage: React.FC<ProjectGuidePageProps> = ({
  onNavigateTab,
  onSeedDemo,
}) => {
  const steps = [
    {
      number: '1',
      title: 'Initialize Isolated Guest Workspace',
      description:
        'When you access Sentinel, an isolated workspace session is bootstrapped with an opaque session identifier stored in an HttpOnly cookie and protected by CSRF token headers. All backend queries and mutations are strictly scoped to this workspace.',
      actionText: 'Session Active',
      action: null,
    },
    {
      number: '2',
      title: 'Seed 95+ Deterministic Synthetic Events',
      description:
        'Load the multi-day synthetic dataset containing normal administrative baseline activity, brute-force bursts, privilege escalations, audit clearing, monitoring sabotage, known downgrades, and after-hours modifications.',
      actionText: 'Load Demo Dataset',
      action: onSeedDemo,
    },
    {
      number: '3',
      title: 'Examine the Security Operations Dashboard',
      description:
        'Inspect database-backed metrics: Total Events, Active Alerts, Critical Risk Indicators, Open Investigations, and Distinct Administrators. Interact with the Activity Timeline and Severity Breakdown charts.',
      actionText: 'Go to Overview',
      action: () => onNavigateTab('overview'),
    },
    {
      number: '4',
      title: 'Inspect Activity Logs & Audit Trails',
      description:
        'Navigate to Activity Logs. Filter by action (e.g. create_admin or clear_logs), search by IP or command text, sort columns, and click any row to open the Event Detail drawer with linked alerts.',
      actionText: 'Open Activity Logs',
      action: () => onNavigateTab('logs'),
    },
    {
      number: '5',
      title: 'Conduct an Alert Investigation & SOC Triage',
      description:
        'Open Alerts & Investigations. Click on an alert (e.g. R02 Privilege Escalation or R03 Logs Cleared) to open the Dossier. Inspect JSON evidence and correlated events, update review status to "Investigating", add an analyst note, and observe the persistent audit history.',
      actionText: 'Open Alerts',
      action: () => onNavigateTab('alerts'),
    },
    {
      number: '6',
      title: 'Test Atomic Rollback & Validation Safeguards',
      description:
        'Go to Import & Simulation. Download the "Test Invalid CSV" sample and drop it into the upload box. Notice how the pre-commit validator flags exact row numbers and explains why the batch is atomically rejected without partial database commits.',
      actionText: 'Open Import & Simulation',
      action: () => onNavigateTab('import'),
    },
    {
      number: '7',
      title: 'Tune Rules & Run Idempotent Reanalysis',
      description:
        'In Detection Rules, edit the R08 business hours window or toggle a rule off. Click "Reanalyze Workspace Logs". Notice how matching alerts preserve analyst decisions while rules that no longer match are safely marked inactive with reasons.',
      actionText: 'Open Detection Rules',
      action: () => onNavigateTab('rules'),
    },
    {
      number: '8',
      title: 'Export Compliance Audit Reports & PDF',
      description:
        'In Audit Reports, filter the report period and click "Print / Save as PDF". View the cleanly styled executive audit report with legal disclaimers and verified formula-injection neutralization.',
      actionText: 'Open Audit Reports',
      action: () => onNavigateTab('reports'),
    },
  ];

  const rulesMatrix = [
    {
      code: 'R01',
      name: 'Administrator account created',
      severity: 'High',
      condition: 'status == "success" and action == "create_admin"',
      rationale: 'Privileged user expansion increases attack surface and requires change ticket verification.',
    },
    {
      code: 'R02',
      name: 'Privilege escalation',
      severity: 'Critical / High',
      condition: 'status == "success" and action == "change_privilege"',
      rationale:
        'Triggers Critical if role elevated to admin/root/superuser. Produces High review alert if role fields are omitted. Explicit downgrades are excluded.',
    },
    {
      code: 'R03',
      name: 'Audit logs cleared',
      severity: 'Critical',
      condition: 'status == "success" and action == "clear_logs"',
      rationale: 'Deliberate log wiping is an emergency indicator of defense evasion by compromised accounts.',
    },
    {
      code: 'R04',
      name: 'Security monitoring disabled',
      severity: 'Critical',
      condition: 'status == "success" and action == "disable_security"',
      rationale: 'Direct sabotage of telemetry or EDR agents to blind SOC monitoring.',
    },
    {
      code: 'R05',
      name: 'Account deleted',
      severity: 'High',
      condition: 'status == "success" and action == "delete_user"',
      rationale: 'Account deprovisioning must align with authorized HR/IAM lifecycle tickets.',
    },
    {
      code: 'R06',
      name: 'Administrator password reset',
      severity: 'High',
      condition: 'status == "success" and action == "reset_admin_password"',
      rationale: 'Privileged account takeover risk; requires out-of-band identity confirmation with owner.',
    },
    {
      code: 'R07',
      name: 'Sensitive data export',
      severity: 'High',
      condition: 'status == "success" and action == "export_sensitive"',
      rationale: 'Bulk data egress monitoring to prevent privileged data exfiltration.',
    },
    {
      code: 'R08',
      name: 'After-hours administrative activity',
      severity: 'Medium',
      condition: 'status == "success" outside configured hours (default 08:00–18:00 UTC)',
      rationale:
        'Flags modifications outside business hours while excluding routine logins/logouts. Handles configured timezones and overnight schedules.',
    },
    {
      code: 'R09',
      name: 'Repeated failed logins',
      severity: 'High',
      condition: '>= 5 failed logins for same actor and IP within rolling 10-minute window',
      rationale:
        'Detects credential stuffing or brute force attacks with alert suppression so ongoing bursts do not generate redundant alerts.',
    },
    {
      code: 'R10',
      name: 'Explicitly unapproved privilege operation',
      severity: 'Critical',
      condition: 'create_admin or change_privilege with approved == false',
      rationale:
        'Flags operations executed despite explicit authorization rejection. Missing approval data is treated as unknown, not unauthorized.',
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="neutral" size="sm">
            Problem Statement T2-PS4
          </Badge>
          <Badge variant="outline" size="sm">
            Cybersecurity Audit Tool
          </Badge>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
          Sentinel: Privileged Access Monitoring Tool
        </h1>
        <p className="text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
          Comprehensive full-stack architecture, explainable rule engine, ingestion safeguards, and
          demonstration walkthrough for administrative identity monitoring.
        </p>
      </div>

      {/* Abstract & Objectives Card */}
      <Card>
        <CardHeader
          title="Executive Project Abstract &amp; Objectives"
          subtitle="T2-PS4 Problem Statement Analysis"
        />
        <CardBody className="space-y-4 text-xs sm:text-sm text-slate-700 leading-relaxed">
          <p>
            <strong>The Problem:</strong> Administrator accounts possess elevated privileges enabling user creation,
            role modification, security agent management, and sensitive resource access. Without rigorous, continuous
            monitoring, insider threats or compromised administrative credentials can evade perimeter defenses,
            alter critical infrastructure, and erase forensic audit trails.
          </p>
          <p>
            <strong>The Sentinel Solution:</strong> Sentinel implements an end-to-end privileged access monitoring
            system that processes real and simulated administrative logs, enforces strict canonical schema validation,
            applies 10 predefined deterministic security heuristics, prevents duplicate ingestion using cryptographic
            fingerprints, maintains a full SOC analyst investigation and status audit trail, and exports tamper-resistant
            compliance reports.
          </p>
        </CardBody>
      </Card>

      {/* 5-Minute Demonstration Walkthrough */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-teal-600" />
              <span>5-Minute Interactive Demonstration Walkthrough</span>
            </h2>
            <p className="text-xs text-slate-500">
              Follow this sequence during your final project evaluation and live demonstration
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {steps.map((st) => (
            <Card key={st.number} className="hover:border-slate-300 transition-all">
              <CardBody className="p-4 sm:p-5 flex flex-col justify-between h-full">
                <div className="space-y-2">
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-brand-100 text-brand-800 font-bold text-xs flex items-center justify-center font-mono">
                      {st.number}
                    </span>
                    <h3 className="font-semibold text-slate-900 text-sm">{st.title}</h3>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed font-sans">{st.description}</p>
                </div>
                {st.action && (
                  <div className="pt-3 mt-3 border-t border-slate-100 flex justify-end">
                    <Button variant="outline" size="sm" onClick={st.action}>
                      {st.actionText} &rarr;
                    </Button>
                  </div>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      </div>

      {/* Detection Rules Matrix */}
      <div>
        <div className="mb-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-teal-600" />
            <span>Detection Rules Logic &amp; Heuristics Matrix</span>
          </h2>
          <p className="text-xs text-slate-500">
            Formal definitions of the 10 predefined detection heuristics implemented in the Python engine
          </p>
        </div>

        <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
              <tr>
                <th className="px-4 py-3">Rule</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Trigger Condition</th>
                <th className="px-4 py-3">Security Rationale &amp; Investigation Focus</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {rulesMatrix.map((r) => (
                <tr key={r.code} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-4 py-3 font-semibold text-slate-900 whitespace-nowrap">
                    <span className="font-mono text-teal-700">{r.code}</span> &bull; {r.name}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <Badge variant={r.severity.toLowerCase().includes('crit') ? 'critical' : r.severity.toLowerCase().includes('high') ? 'high' : 'medium'} size="sm">
                      {r.severity}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-700 text-[11px] bg-slate-50/50">
                    {r.condition}
                  </td>
                  <td className="px-4 py-3 text-slate-600 text-xs leading-relaxed">
                    {r.rationale}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Architecture & Security Controls */}
      <Card>
        <CardHeader
          title="Security, Privacy &amp; Public Demo Isolation Architecture"
          subtitle="Implementation safeguards and enterprise architectural decisions"
        />
        <CardBody className="space-y-4 text-xs sm:text-sm text-slate-700 leading-relaxed">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="font-semibold text-slate-900 text-xs flex items-center gap-1.5 mb-1.5">
                <Lock className="w-4 h-4 text-teal-600" />
                <span>Guest Session Isolation</span>
              </h4>
              <p className="text-xs text-slate-600 leading-normal">
                Every visitor receives a cryptographically random session identifier stored in an HttpOnly,
                SameSite=Lax cookie with CSRF token verification. All queries, mutations, and database records
                are strictly filtered by workspace ID.
              </p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="font-semibold text-slate-900 text-xs flex items-center gap-1.5 mb-1.5">
                <Cpu className="w-4 h-4 text-teal-600" />
                <span>Deterministic Detection Engine</span>
              </h4>
              <p className="text-xs text-slate-600 leading-normal">
                Rules are executed on the Python backend using sorted event timelines, rolling time windows, and
                fingerprint deduplication. Alerts are never hardcoded or simulated purely in frontend JavaScript.
              </p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="font-semibold text-slate-900 text-xs flex items-center gap-1.5 mb-1.5">
                <ShieldCheck className="w-4 h-4 text-teal-600" />
                <span>Export &amp; Command Safety</span>
              </h4>
              <p className="text-xs text-slate-600 leading-normal">
                Uploaded commands are strictly treated as untrusted text strings and never executed. All CSV
                exports prepend apostrophes to spreadsheet formula triggers (<code className="font-mono text-teal-700">=, +, -, @</code>)
                to protect analysts against CSV injection.
              </p>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
