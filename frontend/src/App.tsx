import { useState } from 'react';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { SettingsPage } from './pages/SettingsPage';
import { usePipeline } from './hooks/usePipeline';

function App() {
  const [page, setPage] = useState<'dashboard' | 'settings'>('dashboard');
  const { state } = usePipeline();

  return (
    <Layout onPageChange={setPage} currentPage={page}>
      {page === 'dashboard' ? (
        <DashboardPage pipelineState={state} />
      ) : (
        <SettingsPage />
      )}
    </Layout>
  );
}

export default App;
