import { supabase } from './supabase'

const API_URL = 'http://localhost:8000'

async function getAuthToken() {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token
}

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = await getAuthToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

export const api = {
  auth: {
    signUp: (email: string, password: string, organizationName: string) =>
      fetchAPI('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, organization_name: organizationName }),
      }),

    signIn: (email: string, password: string) =>
      fetchAPI('/auth/signin', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),

    signOut: () => fetchAPI('/auth/signout', { method: 'POST' }),
  },

  projects: {
    list: () => fetchAPI('/projects'),
    get: (id: string) => fetchAPI(`/projects/${id}`),
    create: (data: { name: string; description?: string }) =>
      fetchAPI('/projects', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: { name?: string; description?: string }) =>
      fetchAPI(`/projects/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) => fetchAPI(`/projects/${id}`, { method: 'DELETE' }),
  },

  workflows: {
    list: (projectId: string) => fetchAPI(`/projects/${projectId}/workflows`),
    get: (id: string) => fetchAPI(`/workflows/${id}`),
    create: (projectId: string, data: { name: string; description?: string; type?: string }) =>
      fetchAPI(`/projects/${projectId}/workflows`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: { name?: string; description?: string; type?: string }) =>
      fetchAPI(`/workflows/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) => fetchAPI(`/workflows/${id}`, { method: 'DELETE' }),
    getGraph: (id: string) => fetchAPI(`/workflows/${id}/graph`),
  },

  nodes: {
    list: (workflowId: string) => fetchAPI(`/workflows/${workflowId}/nodes`),
    get: (workflowId: string, nodeId: string) => fetchAPI(`/workflows/${workflowId}/nodes/${nodeId}`),
    create: (workflowId: string, data: any) =>
      fetchAPI(`/workflows/${workflowId}/nodes`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (workflowId: string, nodeId: string, data: any) =>
      fetchAPI(`/workflows/${workflowId}/nodes/${nodeId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (workflowId: string, nodeId: string) =>
      fetchAPI(`/workflows/${workflowId}/nodes/${nodeId}`, { method: 'DELETE' }),
  },

  edges: {
    list: (workflowId: string) => fetchAPI(`/workflows/${workflowId}/edges`),
    create: (workflowId: string, data: any) =>
      fetchAPI(`/workflows/${workflowId}/edges`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    delete: (workflowId: string, edgeId: string) =>
      fetchAPI(`/workflows/${workflowId}/edges/${edgeId}`, { method: 'DELETE' }),
  },

  executions: {
    list: (params?: { workflow_id?: string; status?: string; limit?: number; offset?: number }) => {
      const query = new URLSearchParams()
      if (params?.workflow_id) query.append('workflow_id', params.workflow_id)
      if (params?.status) query.append('status', params.status)
      if (params?.limit) query.append('limit', params.limit.toString())
      if (params?.offset) query.append('offset', params.offset.toString())
      return fetchAPI(`/executions?${query}`)
    },
    get: (id: string) => fetchAPI(`/executions/${id}`),
    getNodes: (id: string) => fetchAPI(`/executions/${id}/nodes`),
    getTimeline: (id: string) => fetchAPI(`/executions/${id}/timeline`),
    getSharedState: (id: string) => fetchAPI(`/executions/${id}/shared-state`),
    getSpans: (id: string) => fetchAPI(`/executions/${id}/telemetry-spans`),
    getEvents: (id: string) => fetchAPI(`/executions/${id}/telemetry-events`),
  },
}
