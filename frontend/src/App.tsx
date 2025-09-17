import React, { useState } from 'react';
import { WorkflowProvider, useWorkflow } from './contexts/WorkflowContext';
import TestConfiguration from './components/TestConfiguration';
import WorkflowProgress from './components/WorkflowProgress';
import ResultsDashboard from './components/ResultsDashboard';

type AppView = 'configuration' | 'progress' | 'results';

function AppContent() {
  const [currentView, setCurrentView] = useState<AppView>('configuration');
  const { state } = useWorkflow();

  // Auto-navigate based on workflow state
  React.useEffect(() => {
    if (state.currentWorkflow) {
      if (state.currentWorkflow.status === 'completed' || state.currentWorkflow.status === 'failed') {
        setCurrentView('results');
      } else if (state.currentWorkflow.status === 'running' || state.currentWorkflow.status === 'initializing') {
        setCurrentView('progress');
      }
    }
  }, [state.currentWorkflow]);

  const handleBackToConfig = () => {
    setCurrentView('configuration');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'configuration':
        return <TestConfiguration />;
      case 'progress':
        return <WorkflowProgress onBack={handleBackToConfig} />;
      case 'results':
        return <ResultsDashboard onBack={handleBackToConfig} />;
      default:
        return <TestConfiguration />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {renderCurrentView()}
    </div>
  );
}

function App() {
  return (
    <WorkflowProvider>
      <AppContent />
    </WorkflowProvider>
  );
}

export default App;
