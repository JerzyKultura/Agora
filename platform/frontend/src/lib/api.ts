import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  
  if (!session?.access_token) {
    throw new Error('Not authenticated');
  }

  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  };
}

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const headers = await getAuthHeaders();
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || error.message || 'API request failed');
  }

  return response.json();
}

// Projects
export const projects = {
  list: () => fetchAPI('/projects'),
  get: (id: string) => fetchAPI(`/projects/${id}`),
  create: (data: { name: string; description?: string }) =>
    fetchAPI('/projects', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: { name?: string; description?: string }) =>
    fetchAPI(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => fetchAPI(`/projects/${id}`, { method: 'DELETE' }),
  
  workflows: {
    list: (projectId: string) => fetchAPI(`/projects/${projectId}/workflows`),
    create: (projectId: string, data: any) =>
      fetchAPI(`/projects/${projectId}/workflows`, { method: 'POST', body: JSON.stringify(data) }),
  },
};

// Workflows
export const workflows = {
  get: (id: string) => fetchAPI(`/workflows/${id}`),
  update: (id: string, data: any) =>
    fetchAPI(`/workflows/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => fetchAPI(`/workflows/${id}`, { method: 'DELETE' }),
  
  nodes: {
    list: (workflowId: string) => fetchAPI(`/workflows/${workflowId}/nodes`),
    get: (workflowId: string, nodeId: string) =>
      fetchAPI(`/workflows/${workflowId}/nodes/${nodeId}`),
    create: (workflowId: string, data: any) =>
      fetchAPI(`/workflows/${workflowId}/nodes`, { method: 'POST', body: JSON.stringify(data) }),
    update: (workflowId: string, nodeId: string, data: any) =>
      fetchAPI(`/workflows/${workflowId}/nodes/${nodeId}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (workflowId: string, nodeId: string) =>
      fetchAPI(`/workflows/${workflowId}/nodes/${nodeId}`, { method: 'DELETE' }),
  },
  
  edges: {
    list: (workflowId: string) => fetchAPI(`/workflows/${workflowId}/edges`),
    create: (workflowId: string, data: any) =>
      fetchAPI(`/workflows/${workflowId}/edges`, { method: 'POST', body: JSON.stringify(data) }),
    delete: (workflowId: string, edgeId: string) =>
      fetchAPI(`/workflows/${workflowId}/edges/${edgeId}`, { method: 'DELETE' }),
  },
  
  graph: (workflowId: string) => fetchAPI(`/workflows/${workflowId}/graph`),
};

// Executions
export const executions = {
  list: (params?: { workflow_id?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.workflow_id) query.set('workflow_id', params.workflow_id);
    if (params?.status) query.set('status', params.status);
    return fetchAPI(`/executions?${query}`);
  },
  get: (id: string) => fetchAPI(`/executions/${id}`),
  getNodes: (id: string) => fetchAPI(`/executions/${id}/nodes`),
  getTimeline: (id: string) => fetchAPI(`/executions/${id}/timeline`),
  getSharedState: (id: string) => fetchAPI(`/executions/${id}/shared-state`),
  getTelemetrySpans: (id: string) => fetchAPI(`/executions/${id}/telemetry-spans`),
  getTelemetryEvents: (id: string) => fetchAPI(`/executions/${id}/telemetry-events`),
};

// API Keys (NEW!)
export const apiKeys = {
  list: () => fetchAPI('/api-keys/'),
  create: (data: { name: string; expires_at?: string }) =>
    fetchAPI('/api-keys/', { method: 'POST', body: JSON.stringify(data) }),
  revoke: (id: string) =>
    fetchAPI(`/api-keys/${id}/`, { method: 'DELETE' }),
};

export default {
  projects,
  workflows,
  executions,
  apiKeys,
};