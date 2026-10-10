import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api/client';
import { NavTab, Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { MobileNav } from './components/layout/MobileNav';
import { OverviewPage } from './pages/OverviewPage';
import { ActivityLogsPage } from './pages/ActivityLogsPage';
import { AlertsPage } from './pages/AlertsPage';
import { ImportSimulationPage } from './pages/ImportSimulationPage';
import { DetectionRulesPage } from './pages/DetectionRulesPage';
import { AuditReportsPage } from './pages/AuditReportsPage';
import { ProjectGuidePage } from './pages/ProjectGuidePage';
import { AlertBanner } from './components/ui/AlertBanner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

function SentinelApp() {
  const queryClient = useQueryClient();
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [actorFilter, setActorFilter] = useState('');
  const [seedNotice, setSeedNotice] = useState<string | null>(null);

  // Bootstrap session query
  const { data: sessionInfo, refetch: refetchSession } = useQuery({
    queryKey: ['sessionInfo'],
    queryFn: () => api.bootstrapSession(),
    staleTime: 60000,
  });

  // Reset Session Mutation
  const resetSessionMutation = useMutation({
    mutationFn: () => api.resetSession(),
    onSuccess: () => {
      queryClient.clear();
      refetchSession();
      setSeedNotice('Workspace reset. You are now working in a clean, isolated guest session.');
      setCurrentTab('overview');
    },
  });

  // Seed Demo Data Mutation
  const seedDemoMutation = useMutation({
    mutationFn: () => api.seedSampleData(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      refetchSession();
      setSeedNotice(data.message);
    },
  });

  const handleSelectTab = (tab: NavTab) => {
    setCurrentTab(tab);
  };

  const handleSelectAlert = (alertId: string) => {
    setSelectedAlertId(alertId);
    setCurrentTab('alerts');
  };

  const handleFilterActor = (actor: string) => {
    setActorFilter(actor);
    setCurrentTab('alerts');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 font-sans">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block h-full flex-shrink-0">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={handleSelectTab}
          sessionInfo={sessionInfo}
          onResetSession={() => resetSessionMutation.mutate()}
          onSeedSampleData={() => seedDemoMutation.mutate()}
          isSeeding={seedDemoMutation.isPending}
        />
      </div>

      {/* Mobile Drawer */}
      <MobileNav
        isOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        currentTab={currentTab}
        onSelectTab={handleSelectTab}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Header
          currentTab={currentTab}
          onOpenMobileMenu={() => setMobileNavOpen(true)}
          onNavigateTab={handleSelectTab}
          onSeedDemo={() => seedDemoMutation.mutate()}
          isSeeding={seedDemoMutation.isPending}
        />

        {/* Global Notification Banner */}
        {seedNotice && (
          <div className="px-4 sm:px-6 pt-4 max-w-7xl mx-auto w-full">
            <AlertBanner
              type="success"
              title="Demo Workspace Update"
              onDismiss={() => setSeedNotice(null)}
            >
              {seedNotice}
            </AlertBanner>
          </div>
        )}

        {/* Active View Container */}
        <main className="flex-1 overflow-y-auto">
          {currentTab === 'overview' && (
            <OverviewPage
              onNavigateTab={handleSelectTab}
              onSelectAlertId={handleSelectAlert}
              onFilterActor={handleFilterActor}
            />
          )}
          {currentTab === 'logs' && (
            <ActivityLogsPage
              onNavigateTab={handleSelectTab}
              onSelectAlertId={handleSelectAlert}
              initialActorFilter={actorFilter}
            />
          )}
          {currentTab === 'alerts' && (
            <AlertsPage
              onNavigateTab={handleSelectTab}
              selectedAlertIdProp={selectedAlertId}
              actorFilterProp={actorFilter}
            />
          )}
          {currentTab === 'import' && (
            <ImportSimulationPage
              onNavigateTab={handleSelectTab}
              onSeedSampleData={() => seedDemoMutation.mutate()}
              isSeeding={seedDemoMutation.isPending}
            />
          )}
          {currentTab === 'rules' && (
            <DetectionRulesPage onNavigateTab={handleSelectTab} />
          )}
          {currentTab === 'reports' && <AuditReportsPage />}
          {currentTab === 'guide' && (
            <ProjectGuidePage
              onNavigateTab={handleSelectTab}
              onSeedDemo={() => seedDemoMutation.mutate()}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SentinelApp />
    </QueryClientProvider>
  );
}
