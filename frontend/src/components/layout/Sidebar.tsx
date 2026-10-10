import React from 'react';
import {
  ShieldAlert,
  LayoutDashboard,
  ScrollText,
  AlertTriangle,
  UploadCloud,
  Sliders,
  FileSpreadsheet,
  BookOpen,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { WorkspaceSessionInfo } from '../../types';

export type NavTab =
  | 'overview'
  | 'logs'
  | 'alerts'
  | 'import'
  | 'rules'
  | 'reports'
  | 'guide';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  sessionInfo?: WorkspaceSessionInfo | null;
  onResetSession: () => void;
  onSeedSampleData: () => void;
  isSeeding?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  sessionInfo,
  onResetSession,
  onSeedSampleData,
  isSeeding = false,
}) => {
  const navItems = [
    {
      id: 'overview' as NavTab,
      label: 'Overview',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: 'logs' as NavTab,
      label: 'Activity Logs',
      icon: ScrollText,
      badge: sessionInfo ? sessionInfo.events_count : null,
    },
    {
      id: 'alerts' as NavTab,
      label: 'Alerts & Investigations',
      icon: AlertTriangle,
      badge: sessionInfo && sessionInfo.unreviewed_alerts_count > 0 ? `${sessionInfo.unreviewed_alerts_count} new` : null,
      badgeVariant: 'danger',
    },
    {
      id: 'import' as NavTab,
      label: 'Import & Simulation',
      icon: UploadCloud,
      badge: null,
    },
    {
      id: 'rules' as NavTab,
      label: 'Detection Rules',
      icon: Sliders,
      badge: '10',
    },
    {
      id: 'reports' as NavTab,
      label: 'Audit Reports',
      icon: FileSpreadsheet,
      badge: null,
    },
    {
      id: 'guide' as NavTab,
      label: 'Project Guide',
      icon: BookOpen,
      badge: 'Docs',
    },
  ];

  return (
    <aside className="w-64 bg-navy-900 text-slate-300 flex flex-col h-full border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-brand-600 flex-shrink-0 flex items-center justify-center text-white shadow-md shadow-brand-900/40">
          <ShieldAlert className="w-5 h-5 text-white" />
        </div>
        <div className="min-w-0">
          <h1 className="font-extrabold text-white text-sm leading-snug tracking-tight">
            Privileged Access Monitoring Tool
          </h1>
          <p className="text-[10px] text-teal-400 font-medium tracking-normal mt-0.5">
            Security Operations &bull; T2-PS4
          </p>
        </div>
      </div>

      {/* Quick Action in Sidebar */}
      <div className="p-3">
        <button
          onClick={onSeedSampleData}
          disabled={isSeeding}
          className="w-full bg-slate-800 hover:bg-slate-700/80 active:bg-slate-700 text-teal-300 border border-teal-500/30 rounded-lg px-3 py-2 text-xs font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-60 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-teal-400" />
          <span>{isSeeding ? 'Seeding Events...' : 'Load 95+ Demo Events'}</span>
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-3 py-1.5">
          Monitoring &amp; Audit
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                isActive
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800/70 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5 truncate">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge !== null && item.badge !== undefined && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-semibold ${
                    item.badgeVariant === 'danger'
                      ? 'bg-rose-500 text-white'
                      : isActive
                      ? 'bg-brand-700 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Guest Workspace Session Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-navy-950/60">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="font-semibold text-slate-200 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Guest Workspace
          </span>
          <button
            onClick={onResetSession}
            title="Reset workspace session and get clean database"
            className="text-slate-400 hover:text-rose-400 p-1 hover:bg-slate-800 rounded transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-[11px] text-slate-400 leading-tight">
          Session ID: <span className="font-mono text-slate-300">{sessionInfo?.workspace_id.slice(0, 8)}...</span>
        </p>
        <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between">
          <span>T2-PS4 &bull; v1.0.0</span>
          <span className="text-teal-400">Isolated Store</span>
        </div>
      </div>
    </aside>
  );
};
