import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import type { WorkflowConfig, WorkflowStatus, WorkflowResults, ServiceHealthResponse } from '../types/workflow';
import { apiService } from '../services/api';

type WorkflowState = {
  config: WorkflowConfig | null;
  currentWorkflow: WorkflowStatus | null;
  results: WorkflowResults | null;
  serviceHealth: ServiceHealthResponse | null;
  loading: boolean;
  error: string | null;
};

type WorkflowAction =
  | { type: 'SET_CONFIG'; payload: WorkflowConfig }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_WORKFLOW_STATUS'; payload: WorkflowStatus }
  | { type: 'SET_RESULTS'; payload: WorkflowResults }
  | { type: 'SET_SERVICE_HEALTH'; payload: ServiceHealthResponse }
  | { type: 'RESET_WORKFLOW' };

const initialState: WorkflowState = {
  config: null,
  currentWorkflow: null,
  results: null,
  serviceHealth: null,
  loading: false,
  error: null,
};

function workflowReducer(state: WorkflowState, action: WorkflowAction): WorkflowState {
  switch (action.type) {
    case 'SET_CONFIG':
      return { ...state, config: action.payload, error: null };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_WORKFLOW_STATUS':
      return { ...state, currentWorkflow: action.payload };
    case 'SET_RESULTS':
      return { ...state, results: action.payload };
    case 'SET_SERVICE_HEALTH':
      return { ...state, serviceHealth: action.payload };
    case 'RESET_WORKFLOW':
      return { ...initialState, serviceHealth: state.serviceHealth };
    default:
      return state;
  }
}

type WorkflowContextType = {
  state: WorkflowState;
  startWorkflow: (config: WorkflowConfig) => Promise<void>;
  pollWorkflowStatus: (workflowId: string) => void;
  fetchResults: (workflowId: string) => Promise<void>;
  fetchServiceHealth: () => Promise<void>;
  resetWorkflow: () => void;
};

const WorkflowContext = createContext<WorkflowContextType | undefined>(undefined);

export function useWorkflow() {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflow must be used within WorkflowProvider');
  }
  return context;
}

interface WorkflowProviderProps {
  children: ReactNode;
}

export function WorkflowProvider({ children }: WorkflowProviderProps) {
  const [state, dispatch] = useReducer(workflowReducer, initialState);

  const startWorkflow = async (config: WorkflowConfig) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_CONFIG', payload: config });
      
      const result = await apiService.startWorkflow(config);
      
      const initialStatus: WorkflowStatus = {
        workflow_id: result.workflow_id,
        status: 'initializing',
        progress: 0,
        current_step: 'Starting workflow...',
        start_time: new Date().toISOString(),
        results_available: false,
      };
      
      dispatch({ type: 'SET_WORKFLOW_STATUS', payload: initialStatus });
      pollWorkflowStatus(result.workflow_id);
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to start workflow' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const pollWorkflowStatus = (workflowId: string) => {
    const poll = async () => {
      try {
        const status = await apiService.getWorkflowStatus(workflowId);
        dispatch({ type: 'SET_WORKFLOW_STATUS', payload: status });
        
        if (status.status === 'completed' || status.status === 'failed') {
          await fetchResults(workflowId);
          return;
        }
        
        if (status.status !== 'cancelled') {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: 'Failed to fetch workflow status' });
      }
    };
    
    poll();
  };

  const fetchResults = async (workflowId: string) => {
    try {
      const results = await apiService.getWorkflowResults(workflowId);
      dispatch({ type: 'SET_RESULTS', payload: results });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to fetch results' });
    }
  };

  const fetchServiceHealth = async () => {
    try {
      const health = await apiService.getServiceStatus();
      dispatch({ type: 'SET_SERVICE_HEALTH', payload: health });
    } catch (error) {
      console.warn('Failed to fetch service health:', error);
    }
  };

  const resetWorkflow = () => {
    dispatch({ type: 'RESET_WORKFLOW' });
  };

  useEffect(() => {
    fetchServiceHealth();
    const interval = setInterval(fetchServiceHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const value: WorkflowContextType = {
    state,
    startWorkflow,
    pollWorkflowStatus,
    fetchResults,
    fetchServiceHealth,
    resetWorkflow,
  };

  return (
    <WorkflowContext.Provider value={value}>
      {children}
    </WorkflowContext.Provider>
  );
}