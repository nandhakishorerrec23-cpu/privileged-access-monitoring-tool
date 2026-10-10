import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sliders,
  CheckCircle2,
  XCircle,
  RotateCw,
  Edit2,
  Save,
  Clock,
  ShieldAlert,
  Info,
  Calendar,
  Layers,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import { RuleConfig, ReanalyzeResponse } from '../types';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { AlertBanner } from '../components/ui/AlertBanner';
import { NavTab } from '../components/layout/Sidebar';

interface DetectionRulesPageProps {
  onNavigateTab: (tab: NavTab) => void;
}

export const DetectionRulesPage: React.FC<DetectionRulesPageProps> = ({ onNavigateTab }) => {
  const queryClient = useQueryClient();
  const [editingRule, setEditingRule] = useState<RuleConfig | null>(null);
  const [reanalyzeResult, setReanalyzeResult] = useState<ReanalyzeResponse | null>(null);

  // Editable config state for modal
  const [ruleEnabled, setRuleEnabled] = useState(true);
  const [bStart, setBStart] = useState('08:00');
  const [bEnd, setBEnd] = useState('18:00');
  const [bTz, setBTz] = useState('UTC');
  const [r9Threshold, setR9Threshold] = useState(5);
  const [r9Window, setR9Window] = useState(10);
  const [r9Suppression, setR9Suppression] = useState(10);

  const { data: rules, isLoading } = useQuery({
    queryKey: ['rules'],
    queryFn: () => api.getRules(),
  });

  const updateRuleMutation = useMutation({
    mutationFn: (vars: { code: string; is_enabled: boolean; config: Record<string, any> }) =>
      api.updateRule(vars.code, { is_enabled: vars.is_enabled, config: vars.config }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setEditingRule(null);
    },
  });

  const reanalyzeMutation = useMutation({
    mutationFn: () => api.reanalyze(),
    onSuccess: (data) => {
      setReanalyzeResult(data);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  const openEditModal = (rule: RuleConfig) => {
    setEditingRule(rule);
    setRuleEnabled(rule.is_enabled);

    if (rule.rule_code === 'R08') {
      setBStart(rule.config.business_start || '08:00');
      setBEnd(rule.config.business_end || '18:00');
      setBTz(rule.config.timezone || 'UTC');
    } else if (rule.rule_code === 'R09') {
      setR9Threshold(rule.config.threshold || 5);
      setR9Window(rule.config.window_minutes || 10);
      setR9Suppression(rule.config.suppression_window_minutes || 10);
    }
  };

  const handleSaveConfig = () => {
    if (!editingRule) return;

    let cfg = { ...editingRule.config };
    if (editingRule.rule_code === 'R08') {
      cfg.business_start = bStart;
      cfg.business_end = bEnd;
      cfg.timezone = bTz;
    } else if (editingRule.rule_code === 'R09') {
      cfg.threshold = Number(r9Threshold);
      cfg.window_minutes = Number(r9Window);
      cfg.suppression_window_minutes = Number(r9Suppression);
    }

    updateRuleMutation.mutate({
      code: editingRule.rule_code,
      is_enabled: ruleEnabled,
      config: cfg,
    });
  };

  const toggleRuleDirect = (rule: RuleConfig) => {
    updateRuleMutation.mutate({
      code: rule.rule_code,
      is_enabled: !rule.is_enabled,
      config: rule.config,
    });
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Detection Rules Matrix</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Predefined explainable security heuristics (R01 through R10) with editable thresholds
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          isLoading={reanalyzeMutation.isPending}
          onClick={() => reanalyzeMutation.mutate()}
          icon={<RotateCw className="w-4 h-4" />}
        >
          Reanalyze Workspace Logs
        </Button>
      </div>

      {/* Reanalysis Results Banner */}
      {reanalyzeResult && (
        <AlertBanner type="success" title="Log Reanalysis Completed Successfully">
          {reanalyzeResult.message}
          <div className="mt-2 flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={() => onNavigateTab('alerts')}>
              View Active Alerts ({reanalyzeResult.total_active_alerts}) &rarr;
            </Button>
            <Button variant="outline" size="sm" onClick={() => onNavigateTab('overview')}>
              View Updated Dashboard &rarr;
            </Button>
          </div>
        </AlertBanner>
      )}

      {/* Philosophy Callout */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 leading-relaxed flex items-start gap-3">
        <Info className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-900 block mb-0.5">
            Deterministic Heuristic Principles &amp; Reanalysis Contract
          </strong>
          Sentinel detection rules provide transparent, explainable alerts. Alerts indicate potential risk
          requiring human verification rather than asserting definitive attack conviction. Reanalyzing logs
          re-evaluates all stored records against current thresholds, safely marking inactive alerts without
          losing historical analyst review decisions or notes.
        </div>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading ? (
          <div className="col-span-2 p-12 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading detection rules...
          </div>
        ) : (
          rules?.map((rule) => (
            <Card
              key={rule.rule_code}
              className={`transition-all ${
                !rule.is_enabled ? 'opacity-60 bg-slate-50/50' : 'bg-white'
              }`}
            >
              <CardBody className="p-5 space-y-3">
                {/* Header row */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-slate-900">
                      {rule.rule_code}
                    </span>
                    <Badge variant={rule.severity.toLowerCase() as any} size="sm">
                      {rule.severity}
                    </Badge>
                    <span className="text-[11px] font-mono text-slate-400 font-medium">
                      v{rule.version}
                    </span>
                  </div>

                  {/* Toggle button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleRuleDirect(rule)}
                      className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 ${
                        rule.is_enabled ? 'bg-brand-600' : 'bg-slate-300'
                      }`}
                      role="switch"
                      aria-checked={rule.is_enabled}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          rule.is_enabled ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* Title */}
                <h3 className="font-semibold text-slate-900 text-sm">{rule.name}</h3>

                {/* Description */}
                <p className="text-xs text-slate-600 leading-relaxed font-sans min-h-[38px]">
                  {rule.description}
                </p>

                {/* Specific Config Footnotes */}
                {rule.rule_code === 'R08' && (
                  <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-[11px] font-mono text-slate-600 flex items-center justify-between">
                    <span>
                      Window: <strong>{rule.config.business_start || '08:00'}</strong> &ndash;{' '}
                      <strong>{rule.config.business_end || '18:00'}</strong> ({rule.config.timezone || 'UTC'})
                    </span>
                    <button
                      onClick={() => openEditModal(rule)}
                      className="text-brand-600 hover:underline flex items-center gap-1 font-sans font-medium"
                    >
                      <Edit2 className="w-3 h-3" /> Edit
                    </button>
                  </div>
                )}

                {rule.rule_code === 'R09' && (
                  <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-[11px] font-mono text-slate-600 flex items-center justify-between">
                    <span>
                      Threshold: <strong>{rule.config.threshold || 5} failures</strong> in{' '}
                      <strong>{rule.config.window_minutes || 10}m</strong>
                    </span>
                    <button
                      onClick={() => openEditModal(rule)}
                      className="text-brand-600 hover:underline flex items-center gap-1 font-sans font-medium"
                    >
                      <Edit2 className="w-3 h-3" /> Edit
                    </button>
                  </div>
                )}

                {rule.rule_code === 'R02' && (
                  <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-[11px] font-mono text-slate-600">
                    Elevated: admin, root, superuser (downgrades excluded; missing roles &rarr; High alert)
                  </div>
                )}
              </CardBody>
            </Card>
          ))
        )}
      </div>

      {/* Edit Thresholds Modal */}
      <Modal
        isOpen={!!editingRule}
        onClose={() => setEditingRule(null)}
        title={
          <div className="flex items-center gap-2">
            <span>Configure Rule: {editingRule?.rule_code}</span>
            <Badge variant={editingRule?.severity.toLowerCase() as any} size="sm">
              {editingRule?.severity}
            </Badge>
          </div>
        }
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setEditingRule(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={updateRuleMutation.isPending}
              onClick={handleSaveConfig}
              icon={<Save className="w-4 h-4" />}
            >
              Save Configuration
            </Button>
          </div>
        }
      >
        {editingRule && (
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-800">Rule Enabled for Workspace</span>
              <input
                type="checkbox"
                checked={ruleEnabled}
                onChange={(e) => setRuleEnabled(e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded"
              />
            </div>

            {editingRule.rule_code === 'R08' && (
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-900">Configurable Business Hours Schedule</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-600 block mb-1">Business Start (HH:MM)</label>
                    <input
                      type="text"
                      value={bStart}
                      onChange={(e) => setBStart(e.target.value)}
                      placeholder="08:00"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-600 block mb-1">Business End (HH:MM)</label>
                    <input
                      type="text"
                      value={bEnd}
                      onChange={(e) => setBEnd(e.target.value)}
                      placeholder="18:00"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-slate-600 block mb-1">Timezone Name</label>
                  <select
                    value={bTz}
                    onChange={(e) => setBTz(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono"
                  >
                    <option value="UTC">UTC (Universal Time Coordinated)</option>
                    <option value="America/New_York">America/New_York (EST/EDT)</option>
                    <option value="America/Los_Angeles">America/Los_Angeles (PST/PDT)</option>
                    <option value="Europe/London">Europe/London (GMT/BST)</option>
                    <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                  </select>
                </div>
              </div>
            )}

            {editingRule.rule_code === 'R09' && (
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-900">Failed Login Correlation &amp; Burst Controls</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-slate-600 block mb-1">Threshold Failures</label>
                    <input
                      type="number"
                      min={2}
                      max={50}
                      value={r9Threshold}
                      onChange={(e) => setR9Threshold(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-600 block mb-1">Rolling Window (min)</label>
                    <input
                      type="number"
                      min={1}
                      max={120}
                      value={r9Window}
                      onChange={(e) => setR9Window(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-600 block mb-1">Burst Suppression (min)</label>
                    <input
                      type="number"
                      min={1}
                      max={120}
                      value={r9Suppression}
                      onChange={(e) => setR9Suppression(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
