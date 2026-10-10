import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ShieldAlert,
  AlertTriangle,
  ScrollText,
  Users,
  Clock,
  CheckCircle2,
  ChevronRight,
  TrendingUp,
  Activity,
  ArrowUpRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';
import { api } from '../api/client';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { NavTab } from '../components/layout/Sidebar';

interface OverviewPageProps {
  onNavigateTab: (tab: NavTab) => void;
  onSelectAlertId?: (alertId: string) => void;
  onFilterActor?: (actor: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  Critical: '#dc2626',
  High: '#d97706',
  Medium: '#2563eb',
  Low: '#64748b',
};

export const OverviewPage: React.FC<OverviewPageProps> = ({
  onNavigateTab,
  onSelectAlertId,
  onFilterActor,
}) => {
  const [dateFilter, setDateFilter] = useState<'all' | '7d' | '24h'>('all');

  const getDateParams = () => {
    if (dateFilter === '24h') {
      const d = new Date(Date.now() - 24 * 3600 * 1000);
      return { date_from: d.toISOString() };
    }
    if (dateFilter === '7d') {
      const d = new Date(Date.now() - 7 * 24 * 3600 * 1000);
      return { date_from: d.toISOString() };
    }
    return {};
  };

  const { data: dashboard, isLoading, error } = useQuery({
    queryKey: ['dashboard', dateFilter],
    queryFn: () => api.getDashboard(getDateParams()),
    refetchInterval: 10000,
  });

  const { data: recentAlertsData } = useQuery({
    queryKey: ['recentAlerts'],
    queryFn: () => api.getAlerts({ page: 1, page_size: 5, sort_by: 'trigger_time', sort_order: 'desc' }),
  });

  const { data: recentEventsData } = useQuery({
    queryKey: ['recentEvents'],
    queryFn: () => api.getEvents({ page: 1, page_size: 5, sort_by: 'timestamp', sort_order: 'desc' }),
  });

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-500 font-medium">Loading security telemetry dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="p-6">
        <Card className="border-rose-200 bg-rose-50/50">
          <CardBody className="text-rose-800 text-sm">
            Failed to load dashboard metrics: {(error as Error)?.message || 'Unknown error'}
          </CardBody>
        </Card>
      </div>
    );
  }

  const { metrics, severity_distribution, activity_timeline, top_flagged_actors } = dashboard;

  const pieData = severity_distribution
    .filter((s) => s.count > 0)
    .map((s) => ({
      name: s.severity,
      value: s.count,
      color: SEVERITY_COLORS[s.severity] || '#64748b',
    }));

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Privileged Telemetry Status</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Database-backed metrics across active workspace logs
          </p>
        </div>
        <div className="flex items-center gap-1.5 bg-white p-1 rounded-lg border border-slate-200 shadow-sm self-start sm:self-auto text-xs">
          {(['all', '7d', '24h'] as const).map((period) => (
            <button
              key={period}
              onClick={() => setDateFilter(period)}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                dateFilter === period
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {period === 'all' ? 'All Time' : period === '7d' ? 'Last 7 Days' : 'Last 24 Hours'}
            </button>
          ))}
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {/* Total Events */}
        <Card
          hoverable
          onClick={() => onNavigateTab('logs')}
          className="border-slate-200"
        >
          <CardBody className="p-4">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider">Total Events</span>
              <ScrollText className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold text-slate-900 font-mono">{metrics.total_events}</div>
            <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <span>View all logs</span>
              <ArrowUpRight className="w-3 h-3 text-slate-400" />
            </p>
          </CardBody>
        </Card>

        {/* Active Alerts */}
        <Card
          hoverable
          onClick={() => onNavigateTab('alerts')}
          className="border-slate-200"
        >
          <CardBody className="p-4">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider">Active Alerts</span>
              <AlertTriangle className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 font-mono">{metrics.total_active_alerts}</div>
            <p className="text-[11px] text-amber-700 font-medium mt-1">
              {metrics.critical_alerts} critical &bull; {metrics.high_alerts} high
            </p>
          </CardBody>
        </Card>

        {/* Critical Alerts */}
        <Card
          hoverable
          onClick={() => onNavigateTab('alerts')}
          className="border-rose-100 bg-rose-50/20"
        >
          <CardBody className="p-4">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-rose-700">Critical</span>
              <ShieldAlert className="w-4 h-4 text-rose-600" />
            </div>
            <div className="text-2xl font-bold text-rose-700 font-mono">{metrics.critical_alerts}</div>
            <p className="text-[11px] text-rose-600 font-medium mt-1">Immediate action</p>
          </CardBody>
        </Card>

        {/* Open Investigations */}
        <Card
          hoverable
          onClick={() => onNavigateTab('alerts')}
          className="border-slate-200"
        >
          <CardBody className="p-4">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider">In Triage</span>
              <Activity className="w-4 h-4 text-sky-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 font-mono">{metrics.open_investigations}</div>
            <p className="text-[11px] text-sky-700 font-medium mt-1">Open / Investigating</p>
          </CardBody>
        </Card>

        {/* Distinct Admins */}
        <Card
          hoverable
          onClick={() => onNavigateTab('logs')}
          className="border-slate-200"
        >
          <CardBody className="p-4">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider">Privileged Actors</span>
              <Users className="w-4 h-4 text-teal-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900 font-mono">{metrics.distinct_admins}</div>
            <p className="text-[11px] text-slate-500 mt-1">Distinct identities</p>
          </CardBody>
        </Card>

        {/* Active Rules */}
        <Card
          hoverable
          onClick={() => onNavigateTab('rules')}
          className="border-slate-200"
        >
          <CardBody className="p-4">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider">Detection Rules</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900 font-mono">
              {metrics.active_rules_count} <span className="text-xs text-slate-500 font-sans">/ {metrics.total_rules_count}</span>
            </div>
            <p className="text-[11px] text-emerald-700 font-medium mt-1">All heuristics active</p>
          </CardBody>
        </Card>
      </div>

      {/* Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Chart */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Activity &amp; Alert Telemetry Over Time"
            subtitle="Comparing total administrative events ingested vs triggered security alerts"
            action={
              <Badge variant="neutral" size="sm">
                Chronological UTC
              </Badge>
            }
          />
          <CardBody>
            {activity_timeline.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400 text-xs">
                No activity recorded in selected timeframe. Ingest sample logs to view timeline.
              </div>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={activity_timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: '#e2e8f0',
                        borderRadius: '8px',
                        fontSize: '12px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Bar dataKey="event_count" name="Total Events" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="alert_count" name="Alerts Triggered" fill="#0d9488" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Severity Distribution Donut */}
        <Card>
          <CardHeader
            title="Alert Severity Distribution"
            subtitle="Breakdown of active alerts by security impact level"
          />
          <CardBody>
            {metrics.total_active_alerts === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400 text-xs">
                Zero active alerts detected in workspace.
              </div>
            ) : (
              <div className="h-64 w-full flex flex-col items-center justify-center">
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={4}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val: number) => [`${val} alerts`, 'Count']}
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: '#e2e8f0',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="w-full grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-100 text-xs">
                  {severity_distribution.map((s) => (
                    <div key={s.severity} className="flex items-center justify-between px-2 py-0.5">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="w-2.5 h-2.5 rounded-full"
                          style={{ backgroundColor: SEVERITY_COLORS[s.severity] }}
                        />
                        <span className="text-slate-600 font-medium">{s.severity}</span>
                      </div>
                      <span className="font-mono font-bold text-slate-800">{s.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Tables Row: Top Flagged Actors & Recent Critical Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Flagged Actors */}
        <Card>
          <CardHeader
            title="Most Frequently Flagged Privileged Actors"
            subtitle="Accounts responsible for repeated or high-impact heuristic alerts"
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigateTab('alerts')}
              >
                All alerts &rarr;
              </Button>
            }
          />
          <CardBody className="p-0">
            {top_flagged_actors.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No flagged accounts found. Load sample data to examine actors.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Actor Identity</th>
                      <th className="px-4 py-3 text-center">Critical</th>
                      <th className="px-4 py-3 text-center">High</th>
                      <th className="px-4 py-3 text-center">Total Alerts</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {top_flagged_actors.map((actorItem) => (
                      <tr key={actorItem.actor} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-4 py-3 font-semibold text-slate-900 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-teal-500" />
                          <span>{actorItem.actor}</span>
                        </td>
                        <td className="px-4 py-3 text-center text-rose-600 font-bold">
                          {actorItem.critical_alerts}
                        </td>
                        <td className="px-4 py-3 text-center text-amber-600 font-semibold">
                          {actorItem.high_alerts}
                        </td>
                        <td className="px-4 py-3 text-center text-slate-900 font-bold">
                          {actorItem.total_alerts}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              if (onFilterActor) onFilterActor(actorItem.actor);
                              onNavigateTab('alerts');
                            }}
                            className="text-brand-600 hover:text-brand-700 font-sans font-medium text-xs hover:underline"
                          >
                            Filter Alerts
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Recent Critical & High Alerts */}
        <Card>
          <CardHeader
            title="Recent Critical &amp; High Security Alerts"
            subtitle="Latest trigger events requiring security analyst review"
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigateTab('alerts')}
              >
                View all &rarr;
              </Button>
            }
          />
          <CardBody className="p-0">
            {!recentAlertsData || recentAlertsData.items.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No alerts detected. Ingest synthetic events to view live alert feed.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {recentAlertsData.items.map((alert) => (
                  <div
                    key={alert.id}
                    onClick={() => {
                      if (onSelectAlertId) onSelectAlertId(alert.id);
                      onNavigateTab('alerts');
                    }}
                    className="p-4 hover:bg-slate-50 transition-colors cursor-pointer flex items-start justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            alert.severity.toLowerCase() as
                              | 'critical'
                              | 'high'
                              | 'medium'
                              | 'low'
                          }
                          size="sm"
                        >
                          {alert.severity}
                        </Badge>
                        <span className="font-mono text-xs font-semibold text-slate-700">
                          {alert.rule_code}
                        </span>
                        <Badge
                          variant={alert.review_status.toLowerCase() as any}
                          size="sm"
                        >
                          {alert.review_status}
                        </Badge>
                      </div>
                      <p className="text-xs font-medium text-slate-800 line-clamp-1">{alert.reason}</p>
                      <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                        <span>Actor: <strong>{alert.actor}</strong></span>
                        <span>&bull;</span>
                        <span>Target: <strong>{alert.target}</strong></span>
                        <span>&bull;</span>
                        <span>{new Date(alert.trigger_time).toLocaleTimeString()}</span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400 mt-1 flex-shrink-0" />
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
};
