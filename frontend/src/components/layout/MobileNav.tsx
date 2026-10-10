import React from 'react';
import { X, ShieldAlert } from 'lucide-react';
import { NavTab } from './Sidebar';
import {
  LayoutDashboard,
  ScrollText,
  AlertTriangle,
  UploadCloud,
  Sliders,
  FileSpreadsheet,
  BookOpen,
} from 'lucide-react';

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({
  isOpen,
  onClose,
  currentTab,
  onSelectTab,
}) => {
  if (!isOpen) return null;

  const navItems = [
    { id: 'overview' as NavTab, label: 'Overview', icon: LayoutDashboard },
    { id: 'logs' as NavTab, label: 'Activity Logs', icon: ScrollText },
    { id: 'alerts' as NavTab, label: 'Alerts & Investigations', icon: AlertTriangle },
    { id: 'import' as NavTab, label: 'Import & Simulation', icon: UploadCloud },
    { id: 'rules' as NavTab, label: 'Detection Rules', icon: Sliders },
    { id: 'reports' as NavTab, label: 'Audit Reports', icon: FileSpreadsheet },
    { id: 'guide' as NavTab, label: 'Project Guide', icon: BookOpen },
  ];

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-y-0 left-0 w-72 bg-navy-900 text-slate-300 p-4 flex flex-col justify-between shadow-2xl">
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex-shrink-0 flex items-center justify-center text-white">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <span className="font-extrabold text-white text-sm leading-snug">
                Privileged Access Monitoring Tool
              </span>
            </div>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded">
              <X className="w-5 h-5" />
            </button>
          </div>

          <nav className="mt-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelectTab(item.id);
                    onClose();
                  }}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-brand-600 text-white' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="pt-4 border-t border-slate-800 text-xs text-slate-400">
          T2-PS4 &bull; Privileged Access Monitoring
        </div>
      </div>
    </div>
  );
};
