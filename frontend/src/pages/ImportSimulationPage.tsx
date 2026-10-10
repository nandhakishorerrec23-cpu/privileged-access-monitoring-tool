import React, { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  UploadCloud,
  FileSpreadsheet,
  FileCode,
  AlertCircle,
  CheckCircle,
  Play,
  RotateCcw,
  Sparkles,
  Download,
  Terminal,
  ShieldCheck,
  Info,
  Clock,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import { ImportPreviewResponse, ImportCommitResponse, ManualSimulateResponse } from '../types';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import { NavTab } from '../components/layout/Sidebar';

interface ImportSimulationPageProps {
  onNavigateTab: (tab: NavTab) => void;
  onSeedSampleData: () => void;
  isSeeding?: boolean;
}

const NORMALIZED_ACTIONS = [
  'login',
  'logout',
  'create_user',
  'create_admin',
  'change_privilege',
  'delete_user',
  'reset_password',
  'reset_admin_password',
  'disable_account',
  'enable_account',
  'clear_logs',
  'disable_security',
  'export_sensitive',
  'update_config',
  'execute_command',
];

export const ImportSimulationPage: React.FC<ImportSimulationPageProps> = ({
  onNavigateTab,
  onSeedSampleData,
  isSeeding = false,
}) => {
  const queryClient = useQueryClient();
  const [activeSubTab, setActiveSubTab] = useState<'upload' | 'simulate'>('upload');

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [commitResult, setCommitResult] = useState<ImportCommitResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Manual Simulation Form State
  const [simTimestamp, setSimTimestamp] = useState(new Date().toISOString());
  const [simActor, setSimActor] = useState('alex_admin');
  const [simAction, setSimAction] = useState('create_admin');
  const [simTarget, setSimTarget] = useState('jordan_analyst');
  const [simStatus, setSimStatus] = useState<'success' | 'failed'>('success');
  const [simIp, setSimIp] = useState('192.0.2.45');
  const [simActorRole, setSimActorRole] = useState('admin');
  const [simTargetRole, setSimTargetRole] = useState('admin');
  const [simPrevRole, setSimPrevRole] = useState('');
  const [simCommand, setSimCommand] = useState('iamctl create-admin --user jordan_analyst');
  const [simApproved, setSimApproved] = useState<'none' | 'true' | 'false'>('true');
  const [simApprovalRef, setSimApprovalRef] = useState('TKT-SEC-2026');
  const [simDetails, setSimDetails] = useState('Manual verification simulation');
  const [simResult, setSimResult] = useState<ManualSimulateResponse | null>(null);

  // Preview Mutation
  const previewMutation = useMutation({
    mutationFn: (file: File) => api.previewUpload(file),
    onSuccess: (data) => {
      setPreviewData(data);
      setCommitResult(null);
    },
  });

  // Commit Mutation
  const commitMutation = useMutation({
    mutationFn: (file: File) => api.commitUpload(file),
    onSuccess: (data) => {
      setCommitResult(data);
      setPreviewData(null);
      setSelectedFile(null);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  // Simulate Mutation
  const simulateMutation = useMutation({
    mutationFn: (payload: Record<string, any>) => api.simulateEvent(payload),
    onSuccess: (data) => {
      setSimResult(data);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    setCommitResult(null);
    previewMutation.mutate(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleCommit = () => {
    if (!selectedFile) return;
    commitMutation.mutate(selectedFile);
  };

  const handleSimulateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let approvedVal: boolean | null = null;
    if (simApproved === 'true') approvedVal = true;
    if (simApproved === 'false') approvedVal = false;

    simulateMutation.mutate({
      timestamp: simTimestamp,
      actor: simActor,
      action: simAction,
      target: simTarget,
      status: simStatus,
      source_ip: simIp,
      actor_role: simActorRole || null,
      target_role: simTargetRole || null,
      previous_role: simPrevRole || null,
      command: simCommand || null,
      approved: approvedVal,
      approval_reference: simApprovalRef || null,
      details: simDetails || null,
    });
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Log Ingestion &amp; Simulation</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Validate canonical schema, prevent duplicate fingerprints, and run explainable detection pipeline
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={onSeedSampleData}
            isLoading={isSeeding}
            icon={<Sparkles className="w-4 h-4" />}
          >
            Load 95+ Synthetic Demo Events
          </Button>
        </div>
      </div>

      {/* Mode Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-4 text-xs font-semibold">
        <button
          onClick={() => setActiveSubTab('upload')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-all ${
            activeSubTab === 'upload'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          <span>Bulk File Import (CSV / JSON)</span>
        </button>
        <button
          onClick={() => setActiveSubTab('simulate')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-all ${
            activeSubTab === 'simulate'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Terminal className="w-4 h-4" />
          <span>Manual Event Simulator</span>
        </button>
      </div>

      {/* Tab 1: File Upload */}
      {activeSubTab === 'upload' && (
        <div className="space-y-6">
          {/* Success Banner */}
          {commitResult && (
            <AlertBanner type="success" title="Atomic Ingestion Completed Successfully">
              {commitResult.message}
              <div className="mt-2 flex items-center gap-3">
                <Button variant="outline" size="sm" onClick={() => onNavigateTab('logs')}>
                  Inspect Activity Logs &rarr;
                </Button>
                <Button variant="outline" size="sm" onClick={() => onNavigateTab('alerts')}>
                  View Generated Alerts &rarr;
                </Button>
              </div>
            </AlertBanner>
          )}

          {/* Upload Dropzone */}
          <Card>
            <CardHeader
              title="Upload Normalized Administrative Logs"
              subtitle="Drag and drop canonical CSV or JSON logs (UTF-8, max 5 MB, max 10,000 rows)"
              action={
                <div className="flex items-center gap-2 text-xs">
                  <a
                    href="/api/v1/ingest/samples/download/csv"
                    className="inline-flex items-center gap-1 text-brand-600 hover:underline font-medium"
                    download
                  >
                    <Download className="w-3.5 h-3.5" /> Sample CSV
                  </a>
                  <span className="text-slate-300">&bull;</span>
                  <a
                    href="/api/v1/ingest/samples/download/json"
                    className="inline-flex items-center gap-1 text-brand-600 hover:underline font-medium"
                    download
                  >
                    <Download className="w-3.5 h-3.5" /> Sample JSON
                  </a>
                  <span className="text-slate-300">&bull;</span>
                  <a
                    href="/api/v1/ingest/samples/download/invalid-csv"
                    className="inline-flex items-center gap-1 text-rose-600 hover:underline font-medium"
                    download
                  >
                    <Download className="w-3.5 h-3.5" /> Test Invalid CSV
                  </a>
                </div>
              }
            />
            <CardBody>
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                  dragActive
                    ? 'border-brand-500 bg-brand-50/50'
                    : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.json"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileChange(e.target.files[0]);
                    }
                  }}
                />
                <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto mb-3 text-brand-600 border border-slate-200">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-slate-800 text-sm">
                  {selectedFile ? selectedFile.name : 'Select or drop administrative log file here'}
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Supports .csv and .json formatted according to the Sentinel canonical event schema
                </p>
              </div>
            </CardBody>
          </Card>

          {/* Preview Processing Spinner */}
          {previewMutation.isPending && (
            <div className="p-8 text-center text-slate-500 text-xs">
              <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Parsing file, validating timestamps, IP addresses, and evaluating duplicate fingerprints...
            </div>
          )}

          {/* Preview Error (e.g. Malformed file or size exceeded) */}
          {previewMutation.isError && (
            <AlertBanner type="error" title="File Ingestion Validation Failed">
              {previewMutation.error.message}
            </AlertBanner>
          )}

          {/* Validation Preview Card */}
          {previewData && (
            <Card className="border-slate-200">
              <CardHeader
                title={
                  <div className="flex items-center gap-2">
                    <span>Validation Preview: {previewData.filename}</span>
                    <Badge variant={previewData.error_count > 0 ? 'failed' : 'success'} size="sm">
                      {previewData.error_count > 0 ? 'Validation Errors' : 'Batch Validated'}
                    </Badge>
                  </div>
                }
                subtitle={`Format: ${previewData.file_format.toUpperCase()} • Total rows examined: ${previewData.total_rows}`}
                action={
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={previewData.error_count > 0}
                    isLoading={commitMutation.isPending}
                    onClick={handleCommit}
                    icon={<Play className="w-3.5 h-3.5" />}
                  >
                    Commit Batch ({previewData.new_rows_count} New Events)
                  </Button>
                }
              />
              <CardBody className="space-y-4">
                {/* Metrics Breakdown */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block">Total Records</span>
                    <span className="text-base font-bold text-slate-900 font-mono">
                      {previewData.total_rows}
                    </span>
                  </div>
                  <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                    <span className="text-emerald-700 block">Valid New Events</span>
                    <span className="text-base font-bold text-emerald-800 font-mono">
                      {previewData.new_rows_count}
                    </span>
                  </div>
                  <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <span className="text-amber-700 block">Duplicates Detected</span>
                    <span className="text-base font-bold text-amber-800 font-mono">
                      {previewData.duplicate_count}
                    </span>
                  </div>
                  <div className="p-3 bg-rose-50 rounded-lg border border-rose-200">
                    <span className="text-rose-700 block">Validation Errors</span>
                    <span className="text-base font-bold text-rose-800 font-mono">
                      {previewData.error_count}
                    </span>
                  </div>
                </div>

                {/* Atomic Rejection Warning if errors exist */}
                {previewData.error_count > 0 && (
                  <AlertBanner
                    type="error"
                    title={`Atomic Rollback Safeguard Triggered (${previewData.error_count} Error Rows)`}
                  >
                    Sentinel enforces atomic batch imports. Because invalid schema rows were detected,
                    the batch cannot be partially saved to the database. Fix the errors below and re-upload.
                  </AlertBanner>
                )}

                {/* Validation Error Rows Table */}
                {previewData.errors.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-slate-900 text-xs mb-2">
                      Row-by-Row Schema Diagnostics
                    </h4>
                    <div className="border border-rose-200 rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-rose-50/80 text-rose-800 font-semibold border-b border-rose-200">
                          <tr>
                            <th className="px-3 py-2">Row #</th>
                            <th className="px-3 py-2">Invalid Field</th>
                            <th className="px-3 py-2">Validation Failure Explanation</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-rose-100 font-mono text-slate-700">
                          {previewData.errors.map((err, idx) => (
                            <tr key={idx} className="hover:bg-rose-50/40">
                              <td className="px-3 py-2 font-bold text-rose-700">{err.row_number}</td>
                              <td className="px-3 py-2 text-rose-900">{err.field || 'General'}</td>
                              <td className="px-3 py-2 font-sans text-rose-800">{err.message}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Sample Parsed Rows */}
                {previewData.sample_preview.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-slate-900 text-xs mb-2">
                      Parsed Event Preview (First {previewData.sample_preview.length} Rows)
                    </h4>
                    <div className="border border-slate-200 rounded-lg overflow-x-auto">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                          <tr>
                            <th className="px-3 py-2">Timestamp</th>
                            <th className="px-3 py-2">Actor</th>
                            <th className="px-3 py-2">Action</th>
                            <th className="px-3 py-2">Target</th>
                            <th className="px-3 py-2">Status</th>
                            <th className="px-3 py-2">IP</th>
                            <th className="px-3 py-2">Approved</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {previewData.sample_preview.map((row, i) => (
                            <tr key={i} className="hover:bg-slate-50">
                              <td className="px-3 py-2 text-slate-500 whitespace-nowrap">
                                {String(row.timestamp).slice(0, 19)}
                              </td>
                              <td className="px-3 py-2 font-semibold text-slate-800">{row.actor}</td>
                              <td className="px-3 py-2 text-teal-700">{row.action}</td>
                              <td className="px-3 py-2 text-slate-700">{row.target}</td>
                              <td className="px-3 py-2">{row.status}</td>
                              <td className="px-3 py-2 text-slate-500">{row.source_ip}</td>
                              <td className="px-3 py-2">
                                {row.approved === true
                                  ? 'true'
                                  : row.approved === false
                                  ? 'false'
                                  : 'None'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>
          )}
        </div>
      )}

      {/* Tab 2: Manual Event Simulator */}
      {activeSubTab === 'simulate' && (
        <div className="space-y-6">
          {simResult && (
            <AlertBanner
              type={simResult.alerts_generated > 0 ? 'warning' : 'info'}
              title={`Simulation Outcome: ${simResult.alerts_generated} Alert(s) Generated`}
            >
              {simResult.message}
              <div className="mt-2 flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => onNavigateTab('logs')}>
                  Inspect in Activity Logs &rarr;
                </Button>
                {simResult.alerts_generated > 0 && (
                  <Button variant="outline" size="sm" onClick={() => onNavigateTab('alerts')}>
                    Investigate Generated Alert &rarr;
                  </Button>
                )}
              </div>
            </AlertBanner>
          )}

          <Card>
            <CardHeader
              title="Manual Privileged Activity Simulator"
              subtitle="Inject test events directly through the full canonical schema, persistence, and detection pipeline"
            />
            <CardBody>
              <form onSubmit={handleSimulateSubmit} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Timestamp */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Timestamp (ISO 8601 with TZ) *
                    </label>
                    <input
                      type="text"
                      value={simTimestamp}
                      onChange={(e) => setSimTimestamp(e.target.value)}
                      required
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  {/* Actor */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">Actor Identity *</label>
                    <input
                      type="text"
                      value={simActor}
                      onChange={(e) => setSimActor(e.target.value)}
                      required
                      placeholder="e.g. alex_admin"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  {/* Action */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Normalized Action *
                    </label>
                    <select
                      value={simAction}
                      onChange={(e) => setSimAction(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      {NORMALIZED_ACTIONS.map((a) => (
                        <option key={a} value={a}>
                          {a}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Target */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Target Resource/Account *
                    </label>
                    <input
                      type="text"
                      value={simTarget}
                      onChange={(e) => setSimTarget(e.target.value)}
                      required
                      placeholder="e.g. root or firewall"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  {/* Status */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Execution Status *
                    </label>
                    <select
                      value={simStatus}
                      onChange={(e) => setSimStatus(e.target.value as any)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="success">success</option>
                      <option value="failed">failed</option>
                    </select>
                  </div>

                  {/* Source IP */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Origin IPv4 / IPv6 *
                    </label>
                    <input
                      type="text"
                      value={simIp}
                      onChange={(e) => setSimIp(e.target.value)}
                      required
                      placeholder="e.g. 198.51.100.22"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  {/* Actor Role */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Actor Role (Optional)
                    </label>
                    <input
                      type="text"
                      value={simActorRole}
                      onChange={(e) => setSimActorRole(e.target.value)}
                      placeholder="e.g. admin"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  {/* Target Role */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Target Role (Optional)
                    </label>
                    <input
                      type="text"
                      value={simTargetRole}
                      onChange={(e) => setSimTargetRole(e.target.value)}
                      placeholder="e.g. superuser"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  {/* Previous Role */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Previous Role (Optional)
                    </label>
                    <input
                      type="text"
                      value={simPrevRole}
                      onChange={(e) => setSimPrevRole(e.target.value)}
                      placeholder="e.g. analyst"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  {/* Approved */}
                  <div>
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Approval Evidence State
                    </label>
                    <select
                      value={simApproved}
                      onChange={(e) => setSimApproved(e.target.value as any)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="none">Unknown / Omitted (None)</option>
                      <option value="true">Approved (true)</option>
                      <option value="false">Explicitly Denied (false)</option>
                    </select>
                  </div>

                  {/* Approval Reference */}
                  <div className="lg:col-span-2">
                    <label className="text-slate-600 block mb-1 font-semibold">
                      Approval Ticket Reference
                    </label>
                    <input
                      type="text"
                      value={simApprovalRef}
                      onChange={(e) => setSimApprovalRef(e.target.value)}
                      placeholder="e.g. CHG-2026-901"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>

                {/* Command text */}
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">
                    Command Executed (Untrusted Text)
                  </label>
                  <input
                    type="text"
                    value={simCommand}
                    onChange={(e) => setSimCommand(e.target.value)}
                    placeholder="e.g. usermod -aG sudo jordan"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                {/* Details */}
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">
                    Supplemental Details
                  </label>
                  <input
                    type="text"
                    value={simDetails}
                    onChange={(e) => setSimDetails(e.target.value)}
                    placeholder="e.g. On-call scheduled upgrade session"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-sans focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <Button
                    type="submit"
                    variant="primary"
                    size="md"
                    isLoading={simulateMutation.isPending}
                    icon={<Play className="w-4 h-4" />}
                  >
                    Simulate &amp; Run Detection
                  </Button>
                </div>
              </form>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
};
