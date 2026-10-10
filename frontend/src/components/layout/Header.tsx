import React from 'react';
import { Menu, ShieldCheck, Download, RefreshCw, FileText } from 'lucide-react';
import { Button } from '../ui/Button';
import { NavTab } from './Sidebar';

interface HeaderProps {
  currentTab: NavTab;
  onOpenMobileMenu: () => void;
  onNavigateTab: (tab: NavTab) => void;
  onSeedDemo: () => void;
  isSeeding?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onOpenMobileMenu,
  onNavigateTab,
  onSeedDemo,
  isSeeding = false,
}) => {
  const titles: Record<NavTab, { title: string; subtitle: string }> = {
    overview: {
      title: 'Security Operations Overview',
      subtitle: 'Real-time telemetry, active alerts, and privileged access heuristics',
    },
    logs: {
      title: 'Activity Logs',
      subtitle: 'Searchable audit trail of administrative events and commands',
    },
    alerts: {
      title: 'Alerts & Investigations',
      subtitle: 'Explainable rule-based security alerts with analyst review workflows',
    },
    import: {
      title: 'Import & Simulation',
      subtitle: 'Bulk CSV/JSON file ingestion and manual event simulation pipeline',
    },
    rules: {
      title: 'Detection Rules Matrix',
      subtitle: 'R01 to R10 security heuristics, configurable thresholds, and reanalysis',
    },
    reports: {
      title: 'Audit Reports & Compliance',
      subtitle: 'Generate printable executive audit reports and sanitized dataset exports',
    },
    guide: {
      title: 'Project Guide & Demonstration',
      subtitle: 'Architecture, rule specifications, and 5-minute walkthrough guide',
    },
  };

  const info = titles[currentTab] || { title: 'Sentinel', subtitle: 'Privileged Access Monitoring' };

  return (
    <header className="bg-white border-b border-slate-200/80 px-4 sm:px-6 py-4 flex items-center justify-between gap-4 sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <span className="font-bold text-slate-800">Privileged Access Monitoring Tool</span>
            <span>/</span>
            <span className="text-slate-800 capitalize font-semibold">{currentTab}</span>
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-tight mt-0.5">
            {info.title}
          </h2>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onNavigateTab('reports')}
          icon={<FileText className="w-4 h-4 text-slate-500" />}
          className="hidden sm:inline-flex"
        >
          Export Report
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={onSeedDemo}
          isLoading={isSeeding}
          icon={<RefreshCw className="w-4 h-4" />}
        >
          Seed Demo
        </Button>
      </div>
    </header>
  );
};
