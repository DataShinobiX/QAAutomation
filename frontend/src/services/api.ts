import axios, { type AxiosInstance } from 'axios';
import type { WorkflowConfig, WorkflowStatus, WorkflowResults, ServiceHealthResponse } from '../types/workflow';

const BASE_URL = 'http://localhost:8008';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async startWorkflow(config: WorkflowConfig): Promise<{ workflow_id: string; status: string; message: string }> {
    const response = await this.client.post('/workflows/start', config);
    return response.data;
  }

  async getWorkflowStatus(workflowId: string): Promise<WorkflowStatus> {
    const response = await this.client.get(`/workflows/${workflowId}/status`);
    return response.data;
  }

  async getWorkflowResults(workflowId: string): Promise<WorkflowResults> {
    const response = await this.client.get(`/workflows/${workflowId}/results`);
    return response.data;
  }

  async getServiceStatus(): Promise<ServiceHealthResponse> {
    const response = await this.client.get('/service-status');
    return response.data;
  }

  async runQuickTest(url: string, credentials?: any): Promise<any> {
    const response = await this.client.post('/workflows/quick-test', {
      url,
      credentials,
    });
    return response.data;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  }
}

export const apiService = new ApiService();