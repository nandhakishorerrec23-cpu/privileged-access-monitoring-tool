import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Filter,
  Download,
  RotateCcw,
  ArrowUpDown,
  ExternalLink,
  ShieldAlert,
  Terminal,
  Calendar,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  User,
  Server,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import { ActivityEvent } from '../types';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Drawer } from '../components/ui/Drawer';
import { NavTab } from '../components/layout/Sidebar';

const ACTIONS_LIST = [
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

interface ActivityLogsPageProps {
  onNavigateTab: (tab: NavTab) => void;
  onSelectAlertId?: (alertId: string) => void;
  initialActorFilter?: string;
}

export const ActivityLogsPage: React.FC<ActivityLogsPageProps> = ({
  onNavigateTab,
  onSelectAlertId,
  initialActorFilter = '',
}) => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAction, setSelectedAction] = useState('');
  const [selectedActor, setSelectedActor] = useState(initialActorFilter);
  const [selectedStatus, setSelectedStatus] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Selected event for detail drawer
  const [selectedEvent, setSelectedEvent] = useState<ActivityEvent | null>(null);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: [
      'events',
      page,
      pageSize,
      searchTerm,
      selectedAction,
      selectedActor,
      selectedStatus,
      sortBy,
      sortOrder,
    ],
    queryFn: () =>
      api.getEvents({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
        action: selectedAction || undefined,
        actor: selectedActor || undefined,
        status: selectedStatus || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedAction('');
    setSelectedActor('');
    setSelectedStatus('');
    setPage(1);
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleExportCSV = () => {
    const q = new URLSearchParams();
    if (searchTerm) q.set('search', searchTerm);
    if (selectedAction) q.set('action', selectedAction);
    if (selectedActor) q.set('actor', selectedActor);
    if (selectedStatus) q.set('status', selectedStatus);
    window.open(`/api/v1/events/export?${q.toString()}`, '_blank');
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header & Export */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Activity Logs</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Canonical immutable audit trail of all administrative events
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleExportCSV}
          icon={<Download className="w-4 h-4" />}
        >
          Export Filtered CSV
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardBody className="p-4 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Search Input */}
            <div className="lg:col-span-2 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search actor, target, IP, command..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white transition-all"
              />
            </div>

            {/* Action Filter */}
            <div>
              <select
                value={selectedAction}
                onChange={(e) => {
                  setSelectedAction(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white transition-all text-slate-700"
              >
                <option value="">All Actions ({ACTIONS_LIST.length})</option>
                {ACTIONS_LIST.map((act) => (
                  <option key={act} value={act}>
                    {act}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={selectedStatus}
                onChange={(e) => {
                  setSelectedStatus(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white transition-all text-slate-700"
              >
                <option value="">All Statuses</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* Clear Button */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                icon={<RotateCcw className="w-3.5 h-3.5" />}
                className="w-full text-xs text-slate-600"
              >
                Reset Filters
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Events Table Card */}
      <Card>
        <CardBody className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th
                    onClick={() => handleSort('timestamp')}
                    className="px-4 py-3 cursor-pointer hover:bg-slate-100/70 select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Timestamp (UTC)</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('actor')}
                    className="px-4 py-3 cursor-pointer hover:bg-slate-100/70 select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Actor</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('action')}
                    className="px-4 py-3 cursor-pointer hover:bg-slate-100/70 select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Action</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th className="px-4 py-3">Target</th>
                  <th
                    onClick={() => handleSort('status')}
                    className="px-4 py-3 cursor-pointer hover:bg-slate-100/70 select-none text-center"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Status</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th className="px-4 py-3">Source IP</th>
                  <th className="px-4 py-3 text-center">Alerts</th>
                  <th className="px-4 py-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-slate-400 font-sans">
                      <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                      Loading activity events...
                    </td>
                  </tr>
                ) : !data || data.items.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-slate-400 font-sans">
                      No activity logs match the selected search criteria.
                    </td>
                  </tr>
                ) : (
                  data.items.map((event) => (
                    <tr
                      key={event.id}
                      onClick={() => setSelectedEvent(event)}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                        {new Date(event.timestamp).toISOString().replace('T', ' ').slice(0, 19)}
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900">
                        {event.actor}
                        {event.actor_role && (
                          <span className="text-[10px] font-sans text-slate-400 font-normal ml-1">
                            ({event.actor_role})
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-brand-700 font-semibold">{event.action}</td>
                      <td className="px-4 py-3 text-slate-700 font-sans truncate max-w-[150px]">
                        {event.target}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge
                          variant={event.status.toLowerCase() === 'success' ? 'success' : 'failed'}
                          size="sm"
                        >
                          {event.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{event.source_ip}</td>
                      <td className="px-4 py-3 text-center">
                        {event.alert_ids && event.alert_ids.length > 0 ? (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 text-[11px] font-bold">
                            <ShieldAlert className="w-3 h-3 text-rose-600" />
                            {event.alert_ids.length}
                          </span>
                        ) : (
                          <span className="text-slate-300">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right font-sans">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedEvent(event);
                          }}
                          className="text-brand-600 hover:text-brand-700 font-medium hover:underline text-xs"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          {data && (
            <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
              <div>
                Showing{' '}
                <span className="font-semibold text-slate-900">
                  {data.items.length === 0 ? 0 : (data.page - 1) * data.page_size + 1}
                </span>{' '}
                to{' '}
                <span className="font-semibold text-slate-900">
                  {Math.min(data.page * data.page_size, data.total)}
                </span>{' '}
                of <span className="font-semibold text-slate-900">{data.total}</span> events
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={data.page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  icon={<ChevronLeft className="w-3.5 h-3.5" />}
                >
                  Prev
                </Button>
                <span className="font-mono px-2">
                  {data.page} / {data.total_pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={data.page >= data.total_pages}
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

      {/* Event Details Drawer */}
      <Drawer
        isOpen={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={
          <div className="flex items-center gap-2">
            <span>Event Detail</span>
            <span className="font-mono text-xs text-slate-400 font-normal">
              {selectedEvent?.id}
            </span>
          </div>
        }
        subtitle="Canonical attributes and associated security triggers"
      >
        {selectedEvent && (
          <div className="space-y-6">
            {/* Associated Alerts Banner */}
            {selectedEvent.alert_ids && selectedEvent.alert_ids.length > 0 && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg">
                <div className="flex items-center gap-2 text-rose-800 font-semibold text-xs mb-2">
                  <ShieldAlert className="w-4 h-4 text-rose-600" />
                  <span>Associated with {selectedEvent.alert_ids.length} Security Alert(s)</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedEvent.alert_ids.map((aid) => (
                    <button
                      key={aid}
                      onClick={() => {
                        setSelectedEvent(null);
                        if (onSelectAlertId) onSelectAlertId(aid);
                        onNavigateTab('alerts');
                      }}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white border border-rose-300 rounded font-mono text-xs text-rose-700 hover:bg-rose-100 transition-colors shadow-xs"
                    >
                      <span>{aid}</span>
                      <ExternalLink className="w-3 h-3 text-rose-500" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Core Fields Grid */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-slate-400 block mb-1">Timestamp (UTC)</span>
                <span className="font-mono font-semibold text-slate-800">
                  {selectedEvent.timestamp}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-slate-400 block mb-1">Execution Status</span>
                <Badge
                  variant={selectedEvent.status.toLowerCase() === 'success' ? 'success' : 'failed'}
                  size="sm"
                >
                  {selectedEvent.status}
                </Badge>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-slate-400 block mb-1">Actor Identity</span>
                <span className="font-mono font-semibold text-slate-900 block">
                  {selectedEvent.actor}
                </span>
                <span className="text-[11px] text-slate-500 font-sans">
                  Role: {selectedEvent.actor_role || 'Not specified'}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-slate-400 block mb-1">Target Resource</span>
                <span className="font-mono font-semibold text-slate-900 block">
                  {selectedEvent.target}
                </span>
                <span className="text-[11px] text-slate-500 font-sans">
                  Role: {selectedEvent.target_role || 'Not specified'}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-slate-400 block mb-1">Action Name</span>
                <span className="font-mono font-bold text-teal-700">
                  {selectedEvent.action}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-slate-400 block mb-1">Origin IP Address</span>
                <span className="font-mono font-semibold text-slate-800">
                  {selectedEvent.source_ip}
                </span>
              </div>
            </div>

            {/* Role Transition Comparison (If applicable) */}
            {(selectedEvent.previous_role || selectedEvent.target_role) && (
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-xs text-slate-500 block mb-2 font-semibold">
                  Role Transition Metadata
                </span>
                <div className="flex items-center gap-3 text-xs font-mono">
                  <div className="px-2.5 py-1 bg-white border border-slate-200 rounded text-slate-700">
                    Previous: <strong>{selectedEvent.previous_role || 'None'}</strong>
                  </div>
                  <span className="text-slate-400">&rarr;</span>
                  <div className="px-2.5 py-1 bg-white border border-slate-200 rounded text-brand-700 font-bold">
                    Target: <strong>{selectedEvent.target_role || 'None'}</strong>
                  </div>
                </div>
              </div>
            )}

            {/* Approval Governance */}
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1 text-xs">
              <span className="text-slate-500 block font-semibold">Approval State Evidence</span>
              <div className="flex items-center gap-2">
                <span className="text-slate-600">Approved:</span>
                {selectedEvent.approved === true ? (
                  <Badge variant="success" size="sm">
                    Explicitly Approved (true)
                  </Badge>
                ) : selectedEvent.approved === false ? (
                  <Badge variant="failed" size="sm">
                    Explicitly Denied (false)
                  </Badge>
                ) : (
                  <Badge variant="neutral" size="sm">
                    Unknown / Not Logged (None)
                  </Badge>
                )}
              </div>
              {selectedEvent.approval_reference && (
                <div className="text-slate-500 mt-1">
                  Reference: <span className="font-mono font-semibold text-slate-800">{selectedEvent.approval_reference}</span>
                </div>
              )}
            </div>

            {/* Command Text (Untrusted display) */}
            {selectedEvent.command && (
              <div>
                <span className="text-xs font-semibold text-slate-700 block mb-1.5 flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-slate-500" />
                  <span>Recorded Command Text (Untrusted Text)</span>
                </span>
                <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-xs overflow-x-auto whitespace-pre-wrap selection:bg-teal-500">
                  {selectedEvent.command}
                </pre>
              </div>
            )}

            {/* Details & Fingerprint */}
            {selectedEvent.details && (
              <div>
                <span className="text-xs font-semibold text-slate-700 block mb-1">
                  Supplemental Event Details
                </span>
                <p className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 leading-relaxed">
                  {selectedEvent.details}
                </p>
              </div>
            )}

            <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-400 font-mono break-all">
              Canonical SHA-256 Fingerprint: {selectedEvent.fingerprint}
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};
