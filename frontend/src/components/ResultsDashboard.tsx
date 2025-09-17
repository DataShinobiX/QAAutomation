import React, { useState } from 'react';
import { 
  FileText, 
  Figma, 
  TestTube, 
  Server, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Download,
  ArrowLeft,
  Clock
} from 'lucide-react';
import { useWorkflow } from '../contexts/WorkflowContext';

interface ResultsDashboardProps {
  onBack: () => void;
}

type TabType = 'overview' | 'test-cases' | 'figma-comparison' | 'test-results' | 'services';

const ResultsDashboard: React.FC<ResultsDashboardProps> = ({ onBack }) => {
  const { state } = useWorkflow();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const { results } = state;

  if (!results) {
    return null;
  }

  const tabs = [
    { id: 'overview' as TabType, name: 'Overview', icon: FileText },
    { id: 'test-cases' as TabType, name: 'Test Cases', icon: TestTube },
    { id: 'figma-comparison' as TabType, name: 'Design Comparison', icon: Figma },
    { id: 'test-results' as TabType, name: 'Execution Results', icon: CheckCircle },
    { id: 'services' as TabType, name: 'Service Status', icon: Server },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab results={results} />;
      case 'test-cases':
        return <TestCasesTab results={results} />;
      case 'figma-comparison':
        return <FigmaComparisonTab results={results} />;
      case 'test-results':
        return <TestResultsTab results={results} />;
      case 'services':
        return <ServicesTab results={results} />;
      default:
        return <OverviewTab results={results} />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Test Results</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
              results.status === 'completed' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
            }`}>
              {results.status === 'completed' ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <XCircle className="w-4 h-4" />
              )}
              {results.status}
            </div>
            
            <button className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors">
              <Download className="w-4 h-4 mr-2" />
              Export Results
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

const OverviewTab: React.FC<{ results: any }> = ({ results }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">Execution Time</h3>
        <p className="text-2xl font-bold text-blue-600">{results.execution_time?.toFixed(1)}s</p>
      </div>
      
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="font-semibold text-green-900 mb-2">Services Used</h3>
        <p className="text-2xl font-bold text-green-600">
          {Object.values(results.service_statuses || {}).filter(Boolean).length}
        </p>
      </div>
      
      <div className="bg-purple-50 p-4 rounded-lg">
        <h3 className="font-semibold text-purple-900 mb-2">Analysis Type</h3>
        <p className="text-lg font-bold text-purple-600">
          {results.results?.figma_analysis ? 'Design + Web' : 'Web Only'}
        </p>
      </div>
    </div>

    {results.errors && results.errors.length > 0 && (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <h3 className="flex items-center text-red-800 font-medium mb-2">
          <AlertTriangle className="w-5 h-5 mr-2" />
          Errors Encountered
        </h3>
        <ul className="text-sm text-red-700 space-y-1">
          {results.errors.map((error: string, index: number) => (
            <li key={index}>• {error}</li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

const TestCasesTab: React.FC<{ results: any }> = ({ results }) => {
  const testData = results.results?.unified_tests?.data;
  
  if (!testData) {
    return (
      <div className="text-center py-8 text-gray-500">
        <TestTube className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No test cases generated</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {testData.test_categories && Object.entries(testData.test_categories).map(([category, tests]: [string, any]) => (
        <div key={category} className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 capitalize">
            {category.replace('_', ' ')} ({Array.isArray(tests) ? tests.length : 0})
          </h3>
          
          {Array.isArray(tests) && tests.map((test: any, index: number) => (
            <div key={index} className="bg-gray-50 p-3 rounded-md mb-3 last:mb-0">
              <h4 className="font-medium text-gray-900">{test.name || test.title}</h4>
              <p className="text-sm text-gray-600 mt-1">{test.description}</p>
              {test.steps && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-gray-700">Steps:</p>
                  <ul className="text-xs text-gray-600 mt-1 space-y-1">
                    {test.steps.slice(0, 3).map((step: string, stepIndex: number) => (
                      <li key={stepIndex}>• {step}</li>
                    ))}
                    {test.steps.length > 3 && <li>... and {test.steps.length - 3} more</li>}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

const FigmaComparisonTab: React.FC<{ results: any }> = ({ results }) => {
  const figmaData = results.results?.figma_analysis?.data;
  
  if (!figmaData) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Figma className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No Figma analysis available</p>
        <p className="text-sm mt-2">Provide a Figma file key to enable design comparison</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Design Components</h3>
          <p className="text-2xl font-bold text-blue-600">{figmaData.components_analyzed || 0}</p>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="font-semibold text-green-900 mb-2">Implementation Match</h3>
          <p className="text-2xl font-bold text-green-600">{figmaData.match_percentage || 0}%</p>
        </div>
      </div>

      {figmaData.comparison_details && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Comparison Details</h3>
          <pre className="bg-gray-100 p-4 rounded-md text-sm overflow-auto max-h-64">
            {JSON.stringify(figmaData.comparison_details, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

const TestResultsTab: React.FC<{ results: any }> = ({ results }) => {
  const executionData = results.results?.test_execution?.data;
  
  if (!executionData) {
    return (
      <div className="text-center py-8 text-gray-500">
        <TestTube className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No test execution results available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="font-semibold text-green-900 mb-2">Tests Passed</h3>
          <p className="text-2xl font-bold text-green-600">{executionData.passed || 0}</p>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg">
          <h3 className="font-semibold text-red-900 mb-2">Tests Failed</h3>
          <p className="text-2xl font-bold text-red-600">{executionData.failed || 0}</p>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Total Tests</h3>
          <p className="text-2xl font-bold text-blue-600">{executionData.total || 0}</p>
        </div>
      </div>

      {executionData.test_results && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Detailed Results</h3>
          <div className="space-y-3">
            {executionData.test_results.map((test: any, index: number) => (
              <div key={index} className={`border rounded-lg p-4 ${test.passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-gray-900">{test.name}</h4>
                  {test.passed ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{test.description}</p>
                {test.execution_time && (
                  <div className="flex items-center mt-2 text-xs text-gray-500">
                    <Clock className="w-3 h-3 mr-1" />
                    {test.execution_time}ms
                  </div>
                )}
                {test.error && (
                  <p className="text-sm text-red-600 mt-2">{test.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const ServicesTab: React.FC<{ results: any }> = ({ results }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-semibold text-gray-900">Service Execution Status</h3>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Object.entries(results.service_statuses || {}).map(([service, status]) => (
        <div key={service} className={`border rounded-lg p-4 ${status ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-gray-900 capitalize">{service.replace('_', ' ')}</h4>
            {status ? (
              <CheckCircle className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-red-500" />
            )}
          </div>
          <p className="text-sm text-gray-600 mt-1">
            {status ? 'Service executed successfully' : 'Service execution failed'}
          </p>
        </div>
      ))}
    </div>

    <div className="mt-6">
      <h4 className="font-medium text-gray-900 mb-3">Execution Timeline</h4>
      <div className="space-y-3">
        {Object.entries(results.results || {}).map(([step, data]: [string, any]) => (
          <div key={step} className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${data?.success !== false ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm font-medium text-gray-700 capitalize">{step.replace('_', ' ')}</span>
            <span className="text-xs text-gray-500">
              {data?.success !== false ? 'Completed' : 'Failed'}
            </span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default ResultsDashboard;