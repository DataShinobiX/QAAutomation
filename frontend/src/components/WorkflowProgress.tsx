import React from 'react';
import { CheckCircle, Clock, AlertCircle, Loader, ArrowLeft } from 'lucide-react';
import { useWorkflow } from '../contexts/WorkflowContext';

interface WorkflowProgressProps {
  onBack: () => void;
}

const WorkflowProgress: React.FC<WorkflowProgressProps> = ({ onBack }) => {
  const { state } = useWorkflow();
  const { currentWorkflow } = state;

  if (!currentWorkflow) {
    return null;
  }

  const getStatusIcon = () => {
    switch (currentWorkflow.status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      case 'running':
      case 'initializing':
        return <Loader className="w-6 h-6 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (currentWorkflow.status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'running':
      case 'initializing':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatDuration = (startTime: string) => {
    const start = new Date(startTime);
    const now = new Date();
    const diffMs = now.getTime() - start.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(diffSeconds / 60);
    const seconds = diffSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Configuration
          </button>
          
          <div className="text-sm text-gray-500">
            Workflow ID: {currentWorkflow.workflow_id}
          </div>
        </div>

        {/* Status Overview */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            {getStatusIcon()}
          </div>
          
          <h2 className={`text-2xl font-bold mb-2 ${getStatusColor()}`}>
            {currentWorkflow.status.charAt(0).toUpperCase() + currentWorkflow.status.slice(1)}
          </h2>
          
          <p className="text-gray-600 mb-4">{currentWorkflow.current_step}</p>
          
          <div className="text-sm text-gray-500">
            Duration: {formatDuration(currentWorkflow.start_time)}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(currentWorkflow.progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-primary-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${currentWorkflow.progress}%` }}
            />
          </div>
        </div>

        {/* Workflow Steps */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Workflow Steps</h3>
          
          {getWorkflowSteps(currentWorkflow.progress).map((step, index) => (
            <div key={index} className="flex items-center space-x-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${step.completed ? 'bg-green-100 text-green-600' : step.active ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
                {step.completed ? (
                  <CheckCircle className="w-4 h-4" />
                ) : step.active ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  index + 1
                )}
              </div>
              
              <div className="flex-1">
                <p className={`font-medium ${step.completed ? 'text-green-600' : step.active ? 'text-blue-600' : 'text-gray-400'}`}>
                  {step.name}
                </p>
                <p className="text-sm text-gray-500">{step.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Service Health Indicator */}
        {state.serviceHealth && (
          <div className="mt-8 p-4 bg-gray-50 rounded-md">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Service Health</h4>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${state.serviceHealth.summary.healthy_services === state.serviceHealth.summary.total_services ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="text-sm text-gray-600">
                {state.serviceHealth.summary.healthy_services}/{state.serviceHealth.summary.total_services} services healthy
              </span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {(currentWorkflow.status === 'completed' || currentWorkflow.status === 'failed') && (
          <div className="mt-8 flex justify-center space-x-4">
            <button
              onClick={onBack}
              className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Start New Test
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

function getWorkflowSteps(progress: number) {
  const steps = [
    { name: 'Service Health Check', description: 'Validating all microservices', threshold: 10 },
    { name: 'Authentication', description: 'Logging into website if credentials provided', threshold: 20 },
    { name: 'Website Analysis', description: 'Analyzing DOM structure and performance', threshold: 40 },
    { name: 'Screenshot Capture', description: 'Taking multi-viewport screenshots', threshold: 50 },
    { name: 'Figma Analysis', description: 'Processing design files and components', threshold: 60 },
    { name: 'AI Processing', description: 'Generating intelligent test mappings', threshold: 70 },
    { name: 'Test Generation', description: 'Creating comprehensive test suites', threshold: 90 },
    { name: 'Test Execution', description: 'Running browser automation tests', threshold: 100 },
  ];

  return steps.map((step, index) => ({
    ...step,
    completed: progress > step.threshold,
    active: progress <= step.threshold && (index === 0 || progress > steps[index - 1].threshold),
  }));
}

export default WorkflowProgress;