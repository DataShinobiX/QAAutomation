import React, { useState } from 'react';
import { Globe, Lock, Figma, Play, Settings } from 'lucide-react';
import type { WorkflowConfig } from '../types/workflow';
import { useWorkflow } from '../contexts/WorkflowContext';

const TestConfiguration: React.FC = () => {
  const { startWorkflow, state } = useWorkflow();
  const [formData, setFormData] = useState<WorkflowConfig>({
    url: '',
    workflow_type: 'full_analysis',
  });
  const [showCredentials, setShowCredentials] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await startWorkflow(formData);
  };

  const handleInputChange = (field: keyof WorkflowConfig, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleCredentialChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      credentials: {
        ...prev.credentials,
        [field]: value,
      },
    }));
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">LexiQA Testing Platform</h1>
          <p className="text-gray-600">AI-powered QA automation with comprehensive testing</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Website URL */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <Globe className="w-4 h-4 mr-2" />
              Website URL
            </label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => handleInputChange('url', e.target.value)}
              placeholder="https://example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          {/* Workflow Type */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <Settings className="w-4 h-4 mr-2" />
              Test Type
            </label>
            <select
              value={formData.workflow_type}
              onChange={(e) => handleInputChange('workflow_type', e.target.value as 'quick_analysis' | 'full_analysis')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="quick_analysis">Quick Analysis (30s - 2min)</option>
              <option value="full_analysis">Full Analysis (2-10min)</option>
            </select>
          </div>

          {/* Login Credentials Toggle */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showCredentials}
                onChange={(e) => setShowCredentials(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <Lock className="w-4 h-4 ml-2 mr-2" />
              <span className="text-sm font-medium text-gray-700">Website requires login</span>
            </label>
          </div>

          {/* Credentials Form */}
          {showCredentials && (
            <div className="bg-gray-50 p-4 rounded-md space-y-4">
              <h3 className="text-sm font-medium text-gray-900">Login Credentials</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username/Email
                  </label>
                  <input
                    type="text"
                    value={formData.credentials?.username || ''}
                    onChange={(e) => handleCredentialChange('username', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="your@email.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    value={formData.credentials?.password || ''}
                    onChange={(e) => handleCredentialChange('password', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="••••••••"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Authentication Type
                </label>
                <select
                  value={formData.credentials?.auth_type || 'form_based'}
                  onChange={(e) => handleCredentialChange('auth_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="form_based">Form-based Login</option>
                  <option value="basic_auth">Basic Authentication</option>
                </select>
              </div>
            </div>
          )}

          {/* Figma File Key */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <Figma className="w-4 h-4 mr-2" />
              Figma File Key (Optional)
            </label>
            <input
              type="text"
              value={formData.figma_file_key || ''}
              onChange={(e) => handleInputChange('figma_file_key', e.target.value)}
              placeholder="Enter Figma file key for design comparison"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Include Figma file key to compare design with implementation
            </p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={state.loading || !formData.url}
            className="w-full flex items-center justify-center px-4 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play className="w-4 h-4 mr-2" />
            {state.loading ? 'Starting Test...' : 'Start QA Testing'}
          </button>
        </form>

        {/* Service Health Status */}
        {state.serviceHealth && (
          <div className="mt-8 p-4 bg-gray-50 rounded-md">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Service Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(state.serviceHealth.services).map(([name, status]) => (
                <div
                  key={name}
                  className="flex items-center space-x-2 text-xs"
                >
                  <div
                    className={`w-2 h-2 rounded-full ${
                      status.healthy ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  />
                  <span className="text-gray-700">{name}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {state.serviceHealth.summary.healthy_services}/{state.serviceHealth.summary.total_services} services healthy
            </p>
          </div>
        )}

        {/* Error Display */}
        {state.error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{state.error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestConfiguration;