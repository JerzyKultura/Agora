import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { supabase } from '../lib/supabase'

interface Execution {
  id: string
  workflow_id: string
  status: string
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  error_message: string | null
  tokens_used: number | null
  estimated_cost: number | null
  input_data: any | null
  output_data: any | null
}

interface Workflow {
  id: string
  name: string
  project_id: string
}

interface Project {
  id: string
  name: string
}

export default function Monitoring() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [executions, setExecutions] = useState<Execution[]>([])
  const [workflows, setWorkflows] = useState<Map<string, Workflow>>(new Map())
  const [projects, setProjects] = useState<Map<string, Project>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [workflowFilter, setWorkflowFilter] = useState<string>('all')

  useEffect(() => {
    loadExecutions()

    // Subscribe to all execution changes for this project (or all if no project)
    const channel = supabase
      .channel('monitoring_executions')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'executions'
      }, () => loadExecutions())
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [projectId, filter])

  const loadExecutions = async () => {
    try {
      if (projectId) {
        // Project-specific monitoring
        const workflowsData = await api.workflows.list(projectId)
        const workflowMap = new Map(workflowsData.map((w: Workflow) => [w.id, w]))
        setWorkflows(workflowMap)

        const allExecutions: Execution[] = []
        for (const workflow of workflowsData) {
          try {
            const execs = await api.executions.list({
              workflow_id: workflow.id,
              status: filter === 'all' ? undefined : filter
            })
            allExecutions.push(...execs)
          } catch (e) {
            console.error('Failed to load executions for workflow:', workflow.id)
          }
        }

        allExecutions.sort((a, b) =>
          new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        )

        setExecutions(allExecutions)
      } else {
        // Global monitoring - all projects
        const projectsData = await api.projects.list()
        const projectMap = new Map(projectsData.map((p: Project) => [p.id, p]))
        setProjects(projectMap)

        const allWorkflows: Workflow[] = []
        for (const project of projectsData) {
          const workflowsData = await api.workflows.list(project.id)
          allWorkflows.push(...workflowsData)
        }

        const workflowMap = new Map(allWorkflows.map((w: Workflow) => [w.id, w]))
        setWorkflows(workflowMap)

        const allExecutions: Execution[] = []
        for (const workflow of allWorkflows) {
          try {
            const execs = await api.executions.list({
              workflow_id: workflow.id,
              status: filter === 'all' ? undefined : filter
            })
            allExecutions.push(...execs)
          } catch (e) {
            console.error('Failed to load executions for workflow:', workflow.id)
          }
        }

        allExecutions.sort((a, b) =>
          new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        )

        setExecutions(allExecutions)
      }
    } catch (error: any) {
      console.error('Failed to load executions:', error)
      setError(error.message || 'Failed to load monitoring data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800'
      case 'error': return 'bg-red-100 text-red-800'
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'timeout': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDuration = (ms: number | null) => {
    if (!ms) return '-'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  const filteredExecutions = executions.filter(execution => {
    const matchesSearch = execution.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesWorkflow = workflowFilter === 'all' || execution.workflow_id === workflowFilter
    return matchesSearch && matchesWorkflow
  })

  if (loading && executions.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (error && executions.length === 0) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
        <h3 className="font-bold mb-1">Error Loading Monitoring Data</h3>
        <p>{error}</p>
        <button
          onClick={() => loadExecutions()}
          className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 rounded-md transition-colors"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">Monitoring</h1>
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-[10px] font-bold uppercase tracking-wider animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            Live
          </span>
        </div>
        <div className="flex flex-wrap gap-4 items-center">
          <div className="relative">
            <input
              type="text"
              placeholder="Search Execution ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
            />
          </div>
          <select
            value={workflowFilter}
            onChange={(e) => setWorkflowFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Workflows</option>
            {Array.from(workflows.values()).map(w => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
          </select>
        </div>
      </div>

      {filteredExecutions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-6xl mb-4">🚀</div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No Execution Data Yet</h3>
          <p className="text-gray-600 mb-4">Run your Python workflow to see telemetry data here!</p>
          <div className="bg-gray-50 rounded-lg p-4 mt-6 text-left max-w-2xl mx-auto">
            <p className="font-semibold text-gray-700 mb-2">Quick Start:</p>
            <pre className="text-sm text-gray-600 bg-white p-3 rounded border border-gray-200">
              {`# Install dependencies
pip install traceloop-sdk supabase openai

# Set environment variables (use your .env values)
export VITE_SUPABASE_URL="https://xxx.supabase.co"
export VITE_SUPABASE_ANON_KEY="eyJhbGci..."
export OPENAI_API_KEY="sk-..."

# Run demo
python demo_workflow.py`}
            </pre>
            <p className="text-sm text-gray-500 mt-3">
              Read <code className="bg-white px-2 py-1 rounded border">TELEMETRY_SETUP.md</code> for complete instructions
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {!projectId && <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Workflow</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Context</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Input Preview</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredExecutions.map((execution) => {
                const workflow = workflows.get(execution.workflow_id)
                const project = workflow ? projects.get(workflow.project_id) : null
                return (
                  <tr key={execution.id} className="hover:bg-gray-50">
                    {!projectId && (
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {project?.name || 'Unknown Project'}
                        </div>
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="font-medium">{workflow?.name || 'Unknown'}</div>
                      <div className="text-xs text-gray-400 font-mono">{execution.id.substring(0, 8)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-[10px] leading-4 font-bold rounded-full uppercase tracking-wider ${getStatusColor(execution.status)}`}>
                        {execution.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-mono italic max-w-xs truncate">
                      {execution.input_data ? JSON.stringify(execution.input_data).substring(0, 40) + '...' : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(execution.started_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDuration(execution.duration_ms)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {execution.tokens_used?.toLocaleString() || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {execution.estimated_cost ? `$${execution.estimated_cost.toFixed(4)}` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => navigate(`/executions/${execution.id}`)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
