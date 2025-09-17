export interface WorkflowConfig {
  url: string;
  workflow_type: 'quick_analysis' | 'full_analysis';
  credentials?: {
    username?: string;
    password?: string;
    auth_type?: 'form_based' | 'basic_auth';
    additional_fields?: Record<string, string>;
  };
  figma_file_key?: string;
  options?: Record<string, any>;
}

export interface WorkflowStatus {
  workflow_id: string;
  status: 'initializing' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step: string;
  start_time: string;
  estimated_completion?: string;
  results_available: boolean;
  results_preview?: Record<string, string>;
}

export interface WorkflowResults {
  workflow_id: string;
  status: string;
  execution_time: number;
  results: {
    authentication?: any;
    website_analysis?: any;
    screenshots?: any;
    figma_analysis?: any;
    requirements_parsing?: any;
    unified_tests?: any;
    test_execution?: any;
  };
  errors?: string[];
  service_statuses?: Record<string, boolean>;
}

export interface ServiceStatus {
  name: string;
  healthy: boolean;
  response_time_ms?: number;
  last_check: string;
  error_message?: string;
}

export interface ServiceHealthResponse {
  summary: {
    total_services: number;
    healthy_services: number;
    unhealthy_services: number;
    last_check: string;
  };
  services: Record<string, ServiceStatus>;
}