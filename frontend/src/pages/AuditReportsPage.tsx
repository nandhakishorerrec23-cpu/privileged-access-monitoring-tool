import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileSpreadsheet,
  Printer,
  FileCode,
  Download,
  Filter,
  ShieldCheck,
  Calendar,
  AlertTriangle,
  RotateCcw,
  CheckCircle,
  ExternalLink,
  Info,
} from 'lucide-react';
import { api } from '../api/client';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const AuditReportsPage: React.FC = () => {
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [selectedReviewStatus, setSelectedReviewStatus] = useState('');
  const [selectedRule, setSelectedRule] = useState('');
  const [selectedActor, setSelectedActor] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const buildQueryParams = (format: string) => {
    const q = new URLSearchParams();
    q.set('format', format);
    if (selectedSeverity) q.set('severity', selectedSeverity);
    if (selectedReviewStatus) q.set('review_status', selectedReviewStatus);
    if (selectedRule) q.set('rule_code', selectedRule);
    if (selectedActor) q.set('actor', selectedActor);
    if (dateFrom) q.set('date_from', new Date(dateFrom).toISOString());
    if (dateTo) q.set('date_to', new Date(dateTo).toISOString());
    return q.toString();
  };

  const { data: preview, isLoading } = useQuery({
    queryKey: [
      'reportPreview',
      selectedSeverity,
      selectedReviewStatus,
      selectedRule,
      selectedActor,
      dateFrom,
      dateTo,
    ],
    queryFn: () =>
      api.getReportPreview({
        severity: selectedSeverity || undefined,
        review_status: selectedReviewStatus || undefined,
        rule_code: selectedRule || undefined,
        actor: selectedActor || undefined,
        date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        date_to: dateTo ? new Date(dateTo).toISOString() : undefined,
      }),
  });

  const handleDownload = (format: string) => {
    const qs = buildQueryParams(format);
    window.open(`/api/v1/reports/export?${qs}`, '_blank');
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Audit Reports &amp; Compliance</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Export signed audit evidence, sanitized spreadsheets, and executive printable documents
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => handleDownload('html')}
            icon={<Printer className="w-4 h-4" />}
          >
            Print / Save as PDF
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload('json')}
            icon={<FileCode className="w-4 h-4" />}
          >
            Audit JSON
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload('csv_alerts')}
            icon={<FileSpreadsheet className="w-4 h-4" />}
          >
            Alerts CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload('csv_events')}
            icon={<Download className="w-4 h-4" />}
          >
            Events CSV
          </Button>
        </div>
      </div>

      {/* Scope Filtering Card */}
      <Card>
        <CardHeader
          title="Reporting Scope &amp; Audit Filters"
          subtitle="Define temporal boundaries, rule parameters, and severity scopes for export generation"
        />
        <CardBody className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 text-xs">
            {/* Severity */}
            <div>
              <label className="text-slate-500 block mb-1 font-medium">Severity Scope</label>
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">All Severities</option>
                <option value="Critical">Critical Only</option>
                <option value="High">High Risk Only</option>
                <option value="Medium">Medium Only</option>
                <option value="Low">Low Only</option>
              </select>
            </div>

            {/* Review Status */}
            <div>
              <label className="text-slate-500 block mb-1 font-medium">Review Status</label>
              <select
                value={selectedReviewStatus}
                onChange={(e) => setSelectedReviewStatus(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">All Review Statuses</option>
                <option value="Open">Open</option>
                <option value="Investigating">Investigating</option>
                <option value="Resolved">Resolved</option>
                <option value="False Positive">False Positive</option>
              </select>
            </div>

            {/* Rule Code */}
            <div>
              <label className="text-slate-500 block mb-1 font-medium">Rule Heuristic</label>
              <select
                value={selectedRule}
                onChange={(e) => setSelectedRule(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">All Rules (R01 - R10)</option>
                <option value="R01">R01 — Administrator Created</option>
                <option value="R02">R02 — Privilege Escalation</option>
                <option value="R03">R03 — Logs Cleared</option>
                <option value="R04">R04 — Monitoring Disabled</option>
                <option value="R05">R05 — Account Deleted</option>
                <option value="R06">R06 — Admin Password Reset</option>
                <option value="R07">R07 — Sensitive Export</option>
                <option value="R08">R08 — After-Hours Activity</option>
                <option value="R09">R09 — Failed Login Burst</option>
                <option value="R10">R10 — Explicitly Unapproved</option>
              </select>
            </div>

            {/* Actor Filter */}
            <div>
              <label className="text-slate-500 block mb-1 font-medium">Actor Account</label>
              <input
                type="text"
                placeholder="All actors"
                value={selectedActor}
                onChange={(e) => setSelectedActor(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {/* Date From */}
            <div>
              <label className="text-slate-500 block mb-1 font-medium">Date Range From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="text-slate-500 block mb-1 font-medium">Date Range To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Scope Summary KPI Grid */}
      {preview && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-4 bg-white border border-slate-200 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Events in Scope
            </span>
            <span className="text-2xl font-bold text-slate-900 font-mono mt-1 block">
              {preview.summary.total_events_in_scope}
            </span>
          </div>
          <div className="p-4 bg-white border border-slate-200 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Alerts in Scope
            </span>
            <span className="text-2xl font-bold text-slate-900 font-mono mt-1 block">
              {preview.summary.total_alerts_in_scope}
            </span>
          </div>
          <div className="p-4 bg-rose-50/50 border border-rose-200 rounded-xl">
            <span className="text-[11px] font-semibold text-rose-700 uppercase tracking-wider block">
              Critical Alerts
            </span>
            <span className="text-2xl font-bold text-rose-700 font-mono mt-1 block">
              {preview.summary.critical_alerts}
            </span>
          </div>
          <div className="p-4 bg-amber-50/50 border border-amber-200 rounded-xl">
            <span className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider block">
              High Risk
            </span>
            <span className="text-2xl font-bold text-amber-700 font-mono mt-1 block">
              {preview.summary.high_alerts}
            </span>
          </div>
          <div className="p-4 bg-sky-50/50 border border-sky-200 rounded-xl">
            <span className="text-[11px] font-semibold text-sky-700 uppercase tracking-wider block">
              In Review
            </span>
            <span className="text-2xl font-bold text-sky-800 font-mono mt-1 block">
              {preview.summary.open_alerts + preview.summary.investigating_alerts}
            </span>
          </div>
        </div>
      )}

      {/* Security & Sanitization Callout */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 leading-relaxed flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-900 block mb-0.5">
            Export Security Guarantees &amp; Sanitization
          </strong>
          All CSV spreadsheet exports automatically neutralize CSV formula injection attacks (cells beginning with
          <code className="text-teal-700 font-mono px-1">=</code>,{' '}
          <code className="text-teal-700 font-mono px-1">+</code>,{' '}
          <code className="text-teal-700 font-mono px-1">-</code>, or{' '}
          <code className="text-teal-700 font-mono px-1">@</code> are escaped with a leading apostrophe).
          Printable HTML reports are sanitized against XSS attacks using strict HTML encoding and styled with clean
          print media queries for archival PDF generation.
        </div>
      </div>

      {/* Interactive JSON Report Preview */}
      <Card>
        <CardHeader
          title={
            <div className="flex items-center gap-2">
              <span>Audit Report Payload Preview</span>
              {preview && (
                <span className="font-mono text-xs font-semibold text-slate-500">
                  [{preview.report_id}]
                </span>
              )}
            </div>
          }
          subtitle="Real-time structured audit schema including rule versions and analyst history"
        />
        <CardBody className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Compiling audit dataset...
            </div>
          ) : preview ? (
            <pre className="p-4 bg-slate-950 text-slate-200 font-mono text-[11px] overflow-x-auto max-h-96 leading-relaxed selection:bg-teal-600">
              {JSON.stringify(preview, null, 2)}
            </pre>
          ) : (
            <div className="p-6 text-center text-slate-400 text-xs">No preview data available.</div>
          )}
        </CardBody>
      </Card>
    </div>
  );
};
