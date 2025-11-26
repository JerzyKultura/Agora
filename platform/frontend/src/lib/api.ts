import { supabase } from './supabase'

async function getCurrentUserOrganization() {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Not authenticated')

  const { data: userOrg } = await supabase
    .from('user_organizations')
    .select('organization_id')
    .eq('user_id', user.id)
    .maybeSingle()

  if (!userOrg) throw new Error('No organization found')
  return userOrg.organization_id
}

export const api = {
  auth: {
    signUp: async (email: string, password: string, _organizationName: string) => {
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
      })

      if (authError) throw authError
      if (!authData.user) throw new Error('Failed to create user')

      return authData
    },

    signIn: async (email: string, password: string) => {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) throw error
      return data
    },

    signOut: () => supabase.auth.signOut(),
  },

  projects: {
    list: async () => {
      const orgId = await getCurrentUserOrganization()
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('organization_id', orgId)
        .order('created_at', { ascending: false })

      if (error) throw error
      return data || []
    },

    get: async (id: string) => {
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('id', id)
        .single()

      if (error) throw error
      return data
    },

    create: async (projectData: { name: string; description?: string }) => {
      const orgId = await getCurrentUserOrganization()
      const { data, error } = await supabase
        .from('projects')
        .insert({
          organization_id: orgId,
          name: projectData.name,
          description: projectData.description,
        })
        .select()
        .single()

      if (error) throw error
      return data
    },

    update: async (id: string, projectData: { name?: string; description?: string }) => {
      const { data, error } = await supabase
        .from('projects')
        .update(projectData)
        .eq('id', id)
        .select()
        .single()

      if (error) throw error
      return data
    },

    delete: async (id: string) => {
      const { error } = await supabase
        .from('projects')
        .delete()
        .eq('id', id)

      if (error) throw error
    },
  },

  workflows: {
    list: async (projectId: string) => {
      const { data, error } = await supabase
        .from('workflows')
        .select('*')
        .eq('project_id', projectId)
        .order('created_at', { ascending: false })

      if (error) throw error
      return data || []
    },

    get: async (id: string) => {
      const { data, error } = await supabase
        .from('workflows')
        .select('*')
        .eq('id', id)
        .single()

      if (error) throw error
      return data
    },

    create: async (projectId: string, workflowData: { name: string; description?: string; type?: string }) => {
      const { data, error } = await supabase
        .from('workflows')
        .insert({
          project_id: projectId,
          name: workflowData.name,
          description: workflowData.description,
          type: workflowData.type || 'sequential',
        })
        .select()
        .single()

      if (error) throw error
      return data
    },

    update: async (id: string, workflowData: { name?: string; description?: string; type?: string }) => {
      const { data, error } = await supabase
        .from('workflows')
        .update(workflowData)
        .eq('id', id)
        .select()
        .single()

      if (error) throw error
      return data
    },

    delete: async (id: string) => {
      const { error } = await supabase
        .from('workflows')
        .delete()
        .eq('id', id)

      if (error) throw error
    },

    getGraph: async (id: string) => {
      const [{ data: nodes }, { data: edges }] = await Promise.all([
        supabase.from('nodes').select('*').eq('workflow_id', id),
        supabase.from('edges').select('*').eq('workflow_id', id),
      ])

      return { nodes: nodes || [], edges: edges || [] }
    },
  },

  nodes: {
    list: async (workflowId: string) => {
      const { data, error } = await supabase
        .from('nodes')
        .select('*')
        .eq('workflow_id', workflowId)

      if (error) throw error
      return data || []
    },

    get: async (workflowId: string, nodeId: string) => {
      const { data, error } = await supabase
        .from('nodes')
        .select('*')
        .eq('workflow_id', workflowId)
        .eq('id', nodeId)
        .single()

      if (error) throw error
      return data
    },

    create: async (workflowId: string, nodeData: any) => {
      const { data, error } = await supabase
        .from('nodes')
        .insert({
          workflow_id: workflowId,
          ...nodeData,
        })
        .select()
        .single()

      if (error) throw error
      return data
    },

    update: async (workflowId: string, nodeId: string, nodeData: any) => {
      const { data, error } = await supabase
        .from('nodes')
        .update(nodeData)
        .eq('workflow_id', workflowId)
        .eq('id', nodeId)
        .select()
        .single()

      if (error) throw error
      return data
    },

    delete: async (workflowId: string, nodeId: string) => {
      const { error } = await supabase
        .from('nodes')
        .delete()
        .eq('workflow_id', workflowId)
        .eq('id', nodeId)

      if (error) throw error
    },
  },

  edges: {
    list: async (workflowId: string) => {
      const { data, error } = await supabase
        .from('edges')
        .select('*')
        .eq('workflow_id', workflowId)

      if (error) throw error
      return data || []
    },

    create: async (workflowId: string, edgeData: any) => {
      const { data, error } = await supabase
        .from('edges')
        .insert({
          workflow_id: workflowId,
          ...edgeData,
        })
        .select()
        .single()

      if (error) throw error
      return data
    },

    delete: async (workflowId: string, edgeId: string) => {
      const { error } = await supabase
        .from('edges')
        .delete()
        .eq('workflow_id', workflowId)
        .eq('id', edgeId)

      if (error) throw error
    },
  },

  executions: {
    list: async (params?: { workflow_id?: string; status?: string; limit?: number; offset?: number }) => {
      let query = supabase.from('executions').select('*')

      if (params?.workflow_id) query = query.eq('workflow_id', params.workflow_id)
      if (params?.status) query = query.eq('status', params.status)
      if (params?.limit) query = query.limit(params.limit)
      if (params?.offset) query = query.range(params.offset, params.offset + (params.limit || 10) - 1)

      query = query.order('created_at', { ascending: false })

      const { data, error } = await query
      if (error) throw error
      return data || []
    },

    get: async (id: string) => {
      const { data, error } = await supabase
        .from('executions')
        .select('*')
        .eq('id', id)
        .single()

      if (error) throw error
      return data
    },

    getNodes: async (id: string) => {
      const { data, error } = await supabase
        .from('node_executions')
        .select('*')
        .eq('execution_id', id)
        .order('started_at', { ascending: true })

      if (error) throw error
      return data || []
    },

    getTimeline: async (id: string) => {
      const { data, error } = await supabase
        .from('node_executions')
        .select('*')
        .eq('execution_id', id)
        .order('started_at', { ascending: true })

      if (error) throw error
      return data || []
    },

    getSharedState: async (id: string) => {
      const { data, error } = await supabase
        .from('shared_state_snapshots')
        .select('*')
        .eq('execution_id', id)
        .order('sequence', { ascending: true })

      if (error) throw error
      return data || []
    },

    getSpans: async (id: string) => {
      const { data, error } = await supabase
        .from('telemetry_spans')
        .select('*')
        .eq('execution_id', id)
        .order('start_time', { ascending: true })

      if (error) throw error
      return data || []
    },

    getEvents: async (id: string) => {
      const { data, error } = await supabase
        .from('telemetry_events')
        .select('*')
        .eq('execution_id', id)
        .order('timestamp', { ascending: true })

      if (error) throw error
      return data || []
    },
  },
}
