import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  ShieldAlert,
  Search,
  Filter,
  CheckCircle,
  Clock,
  User,
  ArrowUpDown,
  History,
  FileCode,
  AlertCircle,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Send,
  Info,
} from 'lucide-react';
import { api } from '../api/client';
import { Alert, AlertDetail } from '../types';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Drawer } from '../components/ui/Drawer';
import { NavTab } from '../components/layout/Sidebar';

interface AlertsPageProps {
  onNavigateTab: (tab: NavTab) => void;
  selectedAlertIdProp?: string | null;
  actorFilterProp?: string;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({
  onNavigateTab,
  selectedAlertIdProp,
  actorFilterProp = '',
}) => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [selectedRule, setSelectedRule] = useState('');
  const [selectedReviewStatus, setSelectedReviewStatus] = useState('');
  const [selectedActor, setSelectedActor] = useState(actorFilterProp);
  const [activeOnly, setActiveOnly] = useState<boolean | undefined>(undefined);
  const [sortBy, setSortBy] = useState('trigger_time');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Currently opened alert in investigation drawer
  const [activeAlertId, setActiveAlertId] = useState<string | null>(selectedAlertIdProp || null);

  // Review form state
  const [newReviewStatus, setNewReviewStatus] = useState<'Open' | 'Investigating' | 'Resolved' | 'False Positive'>('Open');
  const [analystNote, setAnalystNote] = useState('');
  const [analystName, setAnalystName] = useState('Security Analyst');
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState('');

  useEffect(() => {
    if (selectedAlertIdProp) {
      setActiveAlertId(selectedAlertIdProp);
    }
  }, [selectedAlertIdProp]);

  // List alerts query
  const { data: alertsData, isLoading } = useQuery({
    queryKey: [
      'alerts',
      page,
      pageSize,
      selectedSeverity,
      selectedRule,
      selectedReviewStatus,
      selectedActor,
      activeOnly,
      sortBy,
      sortOrder,
    ],
    queryFn: () =>
      api.getAlerts({
        page,
        page_size: pageSize,
        severity: selectedSeverity || undefined,
        rule_code: selectedRule || undefined,
        review_status: selectedReviewStatus || undefined,
        actor: selectedActor || undefined,
        is_active: activeOnly,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  // Single alert detail query
  const {
    data: alertDetail,
    isLoading: isDetailLoading,
    isError: isDetailError,
    error: detailError,
    refetch: refetchDetail,
  } = useQuery({
    queryKey: ['alertDetail', activeAlertId],
    queryFn: () => (activeAlertId ? api.getAlertDetail(activeAlertId) : null),
    enabled: !!activeAlertId,
  });

  // Sync review form state when alert detail loads
  useEffect(() => {
    if (alertDetail) {
      setNewReviewStatus(alertDetail.review_status as any);
      setReviewSuccessMsg('');
    }
  }, [alertDetail]);

  // Review mutation
  const reviewMutation = useMutation({
    mutationFn: (vars: { id: string; status: string; note: string; author: string }) =>
      api.updateAlertReview(vars.id, {
        review_status: vars.status,
        note: vars.note,
        author: vars.author,
      }),
    onSuccess: (updatedAlert) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alertDetail', updatedAlert.id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setAnalystNote('');
      setReviewSuccessMsg('Review status and analyst note recorded into audit trail.');
    },
  });

  const handleSaveReview = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeAlertId || !analystNote.trim()) return;
    reviewMutation.mutate({
      id: activeAlertId,
      status: newReviewStatus,
      note: analystNote,
      author: analystName,
    });
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Alerts &amp; Investigations</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Rule-based detection heuristics, correlated evidence, and analyst decision tracking
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card>
        <CardBody className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Severity Filter */}
            <div>
              <select
                value={selectedSeverity}
                onChange={(e) => {
                  setSelectedSeverity(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-700"
              >
                <option value="">All Severities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>

            {/* Rule Filter */}
            <div>
              <select
                value={selectedRule}
                onChange={(e) => {
                  setSelectedRule(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-700"
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

            {/* Review Status */}
            <div>
              <select
                value={selectedReviewStatus}
                onChange={(e) => {
                  setSelectedReviewStatus(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-700"
              >
                <option value="">All Review Statuses</option>
                <option value="Open">Open</option>
                <option value="Investigating">Investigating</option>
                <option value="Resolved">Resolved</option>
                <option value="False Positive">False Positive</option>
              </select>
            </div>

            {/* Actor Filter */}
            <div>
              <input
                type="text"
                placeholder="Filter by actor..."
                value={selectedActor}
                onChange={(e) => {
                  setSelectedActor(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-700"
              />
            </div>

            {/* Reset */}
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedSeverity('');
                  setSelectedRule('');
                  setSelectedReviewStatus('');
                  setSelectedActor('');
                  setActiveOnly(undefined);
                  setPage(1);
                }}
                className="w-full text-xs text-slate-600"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Alerts Table */}
      <Card>
        <CardBody className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th
                    onClick={() => handleSort('trigger_time')}
                    className="px-4 py-3 cursor-pointer hover:bg-slate-100 select-none"
                  >
                    <div className="flex items-center gap-1">
                      <span>Trigger Time</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('severity')}
                    className="px-4 py-3 cursor-pointer hover:bg-slate-100 select-none"
                  >
                    <div className="flex items-center gap-1">
                      <span>Severity</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th className="px-4 py-3">Rule</th>
                  <th className="px-4 py-3">Actor &rarr; Target</th>
                  <th className="px-4 py-3">Detection Summary</th>
                  <th
                    onClick={() => handleSort('review_status')}
                    className="px-4 py-3 cursor-pointer hover:bg-slate-100 select-none text-center"
                  >
                    <div className="flex items-center justify-center gap-1">
                      <span>Review</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400 font-sans">
                      <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                      Loading alerts...
                    </td>
                  </tr>
                ) : !alertsData || alertsData.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400 font-sans">
                      No security alerts match the current filter criteria.
                    </td>
                  </tr>
                ) : (
                  alertsData.items.map((alert) => (
                    <tr
                      key={alert.id}
                      onClick={() => setActiveAlertId(alert.id)}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                        {new Date(alert.trigger_time).toISOString().replace('T', ' ').slice(0, 19)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={alert.severity.toLowerCase() as any}
                          size="sm"
                        >
                          {alert.severity}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900">
                        {alert.rule_code}
                        <span className="text-[10px] text-slate-400 font-sans ml-1">
                          v{alert.rule_version}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-800">
                        <strong>{alert.actor}</strong> &rarr; {alert.target}
                      </td>
                      <td className="px-4 py-3 text-slate-600 font-sans max-w-xs truncate">
                        {alert.reason}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge
                          variant={alert.review_status.toLowerCase() as any}
                          size="sm"
                        >
                          {alert.review_status}
                        </Badge>
                        {!alert.is_active && (
                          <span className="block text-[10px] text-slate-400 font-sans mt-0.5">
                            (Inactive)
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right font-sans">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveAlertId(alert.id);
                          }}
                          className="text-brand-600 hover:text-brand-700 font-medium hover:underline text-xs"
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {alertsData && (
            <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
              <div>
                Showing{' '}
                <span className="font-semibold text-slate-900">
                  {alertsData.items.length === 0 ? 0 : (alertsData.page - 1) * alertsData.page_size + 1}
                </span>{' '}
                to{' '}
                <span className="font-semibold text-slate-900">
                  {Math.min(alertsData.page * alertsData.page_size, alertsData.total)}
                </span>{' '}
                of <span className="font-semibold text-slate-900">{alertsData.total}</span> alerts
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={alertsData.page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  icon={<ChevronLeft className="w-3.5 h-3.5" />}
                >
                  Prev
                </Button>
                <span className="font-mono px-2">
                  {alertsData.page} / {alertsData.total_pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={alertsData.page >= alertsData.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                  icon={<ChevronRight className="w-3.5 h-3.5" />}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Investigation Slide-Over Drawer */}
      <Drawer
        isOpen={!!activeAlertId}
        onClose={() => setActiveAlertId(null)}
        title={
          <div className="flex items-center gap-2">
            <span>Investigation Dossier</span>
            <span className="font-mono text-xs text-slate-400 font-normal">
              {activeAlertId}
            </span>
          </div>
        }
        subtitle="Detection heuristics, evidence telemetry, and SOC review audit trail"
      >
        {isDetailLoading ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading alert details and correlated events...
          </div>
        ) : isDetailError || !alertDetail ? (
          <div className="p-8 text-center text-xs">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 text-rose-500" />
            <p className="font-semibold text-slate-800">Failed to load alert details</p>
            <p className="text-slate-500 mt-1 max-w-sm mx-auto">
              {(detailError as any)?.message || 'An unexpected error occurred while retrieving event telemetry.'}
            </p>
            <Button size="sm" variant="outline" className="mt-4" onClick={() => refetchDetail()}>
              Retry
            </Button>
          </div>
        ) : (
          <div className="space-y-6 text-xs">
            {/* Status & Severity Bar */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-slate-400 text-[11px] block uppercase font-semibold">
                  Rule &amp; Severity
                </span>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant={alertDetail.severity.toLowerCase() as any} size="md">
                    {alertDetail.severity}
                  </Badge>
                  <span className="font-mono font-bold text-slate-900 text-sm">
                    {alertDetail.rule_code}
                  </span>
                  <span className="text-slate-500 font-sans">
                    (Version {alertDetail.rule_version})
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-slate-400 text-[11px] block uppercase font-semibold">
                  Current Review Status
                </span>
                <div className="mt-1">
                  <Badge variant={alertDetail.review_status.toLowerCase() as any} size="md">
                    {alertDetail.review_status}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Inactive Alert Warning */}
            {!alertDetail.is_active && (
              <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5 text-amber-900">
                <Info className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold text-xs">Detection Inactive Following Reanalysis</h4>
                  <p className="text-[11px] text-amber-800 mt-0.5">
                    {alertDetail.deactivation_reason || 'Rule condition no longer matches active criteria.'}
                  </p>
                </div>
              </div>
            )}

            {/* Reason Statement */}
            <div>
              <span className="font-semibold text-slate-700 block mb-1">
                Detection Reasoning (Explainable Rule Heuristic)
              </span>
              <p className="p-3 bg-white border border-slate-200 rounded-lg text-slate-800 font-sans leading-relaxed text-xs shadow-xs">
                {alertDetail.reason}
              </p>
            </div>

            {/* Recommended Action */}
            <div className="p-3.5 bg-teal-50/60 border border-teal-200 rounded-xl">
              <span className="font-semibold text-teal-900 flex items-center gap-1.5 mb-1">
                <ShieldAlert className="w-4 h-4 text-teal-600" />
                <span>Recommended Investigation Procedure</span>
              </span>
              <p className="text-teal-800 font-sans leading-relaxed">
                {alertDetail.recommended_action}
              </p>
            </div>

            {/* Evidence Telemetry JSON */}
            <div>
              <span className="font-semibold text-slate-700 block mb-1.5 flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-slate-500" />
                <span>Extracted Evidence Telemetry</span>
              </span>
              <pre className="p-3 bg-slate-900 text-teal-400 rounded-lg font-mono text-[11px] overflow-x-auto whitespace-pre-wrap max-h-48">
                {JSON.stringify(alertDetail.parsed_evidence, null, 2)}
              </pre>
            </div>

            {/* Correlated Activity Events Table */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-700">
                  Correlated Ingested Event(s) ({alertDetail.correlated_events.length})
                </span>
                <span className="text-[11px] text-slate-400">Time-series correlation</span>
              </div>
              <div className="border border-slate-200 rounded-lg overflow-hidden divide-y divide-slate-100 bg-white">
                {alertDetail.correlated_events.map((evt) => (
                  <div key={evt.id} className="p-3 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center justify-between font-mono text-[11px] text-slate-500 mb-1">
                      <span>{evt.timestamp}</span>
                      <Badge variant={evt.status === 'success' ? 'success' : 'failed'} size="sm">
                        {evt.status}
                      </Badge>
                    </div>
                    <div className="font-mono text-xs">
                      <strong>{evt.actor}</strong> &bull; <span className="text-teal-700">{evt.action}</span> &bull; {evt.target}
                    </div>
                    {evt.command && (
                      <div className="mt-1 font-mono text-[10px] bg-slate-100 p-1.5 rounded text-slate-700 truncate">
                        {evt.command}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Triage & Status Update Form */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
              <h4 className="font-semibold text-slate-900 text-xs">
                Update Review Status &amp; Add Analyst Notes
              </h4>
              <form onSubmit={handleSaveReview} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-500 block mb-1 font-medium">New Status</label>
                    <select
                      value={newReviewStatus}
                      onChange={(e) => setNewReviewStatus(e.target.value as any)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg font-sans focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="Open">Open</option>
                      <option value="Investigating">Investigating</option>
                      <option value="Resolved">Resolved</option>
                      <option value="False Positive">False Positive</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-500 block mb-1 font-medium">Analyst Name</label>
                    <input
                      type="text"
                      value={analystName}
                      onChange={(e) => setAnalystName(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg font-sans focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-slate-500 block mb-1 font-medium">
                    Investigation Findings &amp; Rationale
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Enter verification notes, change management ticket ID, or justification..."
                    value={analystNote}
                    onChange={(e) => setAnalystNote(e.target.value)}
                    required
                    className="w-full p-2.5 bg-white border border-slate-300 rounded-lg font-sans focus:outline-none focus:ring-2 focus:ring-brand-500 text-xs"
                  />
                </div>

                {reviewSuccessMsg && (
                  <div className="text-emerald-700 bg-emerald-50 border border-emerald-200 p-2 rounded text-xs">
                    {reviewSuccessMsg}
                  </div>
                )}

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    size="sm"
                    variant="primary"
                    isLoading={reviewMutation.isPending}
                    icon={<Send className="w-3.5 h-3.5" />}
                  >
                    Save Review Decision
                  </Button>
                </div>
              </form>
            </div>

            {/* Review Audit Trail Timeline */}
            <div>
              <span className="font-semibold text-slate-700 block mb-2 flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-slate-500" />
                <span>Review History Audit Trail ({alertDetail.reviews.length})</span>
              </span>
              {alertDetail.reviews.length === 0 ? (
                <p className="text-slate-400 italic text-[11px] p-3 bg-white border border-slate-100 rounded-lg">
                  No review decisions logged yet. Submit a status change to initiate the audit trail.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {alertDetail.reviews.map((rev) => (
                    <div
                      key={rev.id}
                      className="p-3 bg-white border border-slate-200 rounded-lg space-y-1 shadow-xs"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-semibold text-slate-900 font-sans">
                          {rev.author}
                        </span>
                        <span className="font-mono text-slate-400">
                          {new Date(rev.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                        <span>Changed status:</span>
                        <Badge variant="neutral" size="sm">
                          {rev.previous_status}
                        </Badge>
                        <span>&rarr;</span>
                        <Badge variant={rev.new_status.toLowerCase() as any} size="sm">
                          {rev.new_status}
                        </Badge>
                      </div>
                      <p className="text-slate-700 font-sans mt-1 bg-slate-50 p-2 rounded text-xs border border-slate-100">
                        {rev.note}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};
