import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from '../lib/api'

interface Execution {
  id: string
  workflow_id: string
  status: string
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  error_message: string | null
  input_data: any
  output_data: any
}

interface NodeExecution {
  id: string
  node_id: string
  status: string
  started_at: string
  completed_at: string | null
  prep_duration_ms: number | null
  exec_duration_ms: number | null
  post_duration_ms: number | null
  error_message: string | null
  retry_count: number
}

interface Node {
  id: string
  name: string
  type: string
}

export default function ExecutionDetail() {
  const { executionId } = useParams()
  const navigate = useNavigate()
  const [execution, setExecution] = useState<Execution | null>(null)
  const [nodeExecutions, setNodeExecutions] = useState<NodeExecution[]>([])
  const [nodes, setNodes] = useState<Map<string, Node>>(new Map())
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'timeline' | 'details' | 'data'>('timeline')

  useEffect(() => {
    loadExecutionData()
  }, [executionId])

  const loadExecutionData = async () => {
    try {
      const execData = await api.executions.get(executionId!)
      setExecution(execData)

      const nodeExecs = await api.executions.getNodes(executionId!)
      setNodeExecutions(nodeExecs)

      const nodesData = await api.nodes.list(execData.workflow_id)
      const nodeMap = new Map(nodesData.map((n: Node) => [n.id, n]))
      setNodes(nodeMap)
    } catch (error) {
      console.error('Failed to load execution:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800'
      case 'error': return 'bg-red-100 text-red-800'
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'skipped': return 'bg-gray-100 text-gray-800'
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading execution details...</div>
      </div>
    )
  }

  if (!execution) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Execution not found</div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="text-blue-600 hover:text-blue-800 mb-4 flex items-center"
        >
          ← Back
        </button>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Execution Detail</h1>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>ID: {execution.id.substring(0, 8)}...</span>
              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(execution.status)}`}>
                {execution.status}
              </span>
            </div>
          </div>
          <div className="text-right text-sm text-gray-600">
            <div>Started: {formatDate(execution.started_at)}</div>
            {execution.completed_at && (
              <div>Completed: {formatDate(execution.completed_at)}</div>
            )}
            <div className="font-semibold mt-1">Duration: {formatDuration(execution.duration_ms)}</div>
          </div>
        </div>
      </div>

      <div className="mb-6 border-b border-gray-200">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-4 py-2 font-medium ${activeTab === 'timeline' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Timeline
          </button>
          <button
            onClick={() => setActiveTab('details')}
            className={`px-4 py-2 font-medium ${activeTab === 'details' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab('data')}
            className={`px-4 py-2 font-medium ${activeTab === 'data' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Input/Output
          </button>
        </div>
      </div>

      {activeTab === 'timeline' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {nodeExecutions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No node executions recorded
            </div>
          ) : (
            <div className="p-6">
              <h2 className="text-lg font-semibold mb-4">Node Execution Timeline</h2>
              <div className="space-y-4">
                {nodeExecutions.map((nodeExec, index) => (
                  <div key={nodeExec.id} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {index + 1}. {nodes.get(nodeExec.node_id)?.name || 'Unknown Node'}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getStatusColor(nodeExec.status)}`}>
                            {nodeExec.status}
                          </span>
                          {nodeExec.retry_count > 0 && (
                            <span className="text-xs text-yellow-600">
                              (Retries: {nodeExec.retry_count})
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          Type: {nodes.get(nodeExec.node_id)?.type || 'unknown'}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          Started: {formatDate(nodeExec.started_at)}
                        </div>
                        {nodeExec.error_message && (
                          <div className="text-sm text-red-600 mt-2 bg-red-50 p-2 rounded">
                            Error: {nodeExec.error_message}
                          </div>
                        )}
                      </div>
                      <div className="text-right text-sm">
                        {nodeExec.prep_duration_ms && (
                          <div className="text-gray-600">Prep: {formatDuration(nodeExec.prep_duration_ms)}</div>
                        )}
                        {nodeExec.exec_duration_ms && (
                          <div className="text-gray-600 font-medium">Exec: {formatDuration(nodeExec.exec_duration_ms)}</div>
                        )}
                        {nodeExec.post_duration_ms && (
                          <div className="text-gray-600">Post: {formatDuration(nodeExec.post_duration_ms)}</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'details' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Execution Metrics</h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-gray-500">Total Nodes</div>
              <div className="text-2xl font-bold">{nodeExecutions.length}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Success Rate</div>
              <div className="text-2xl font-bold text-green-600">
                {nodeExecutions.length > 0
                  ? Math.round((nodeExecutions.filter(n => n.status === 'success').length / nodeExecutions.length) * 100)
                  : 0}%
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Average Node Duration</div>
              <div className="text-2xl font-bold">
                {nodeExecutions.length > 0
                  ? formatDuration(
                      Math.round(
                        nodeExecutions.reduce((acc, n) => acc + (n.exec_duration_ms || 0), 0) / nodeExecutions.length
                      )
                    )
                  : '-'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Total Retries</div>
              <div className="text-2xl font-bold text-yellow-600">
                {nodeExecutions.reduce((acc, n) => acc + n.retry_count, 0)}
              </div>
            </div>
          </div>
          {execution.error_message && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="text-sm font-medium text-red-800 mb-1">Execution Error</div>
              <div className="text-sm text-red-700">{execution.error_message}</div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'data' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Input Data</h2>
            <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto max-h-96">
              {JSON.stringify(execution.input_data || {}, null, 2)}
            </pre>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Output Data</h2>
            <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto max-h-96">
              {JSON.stringify(execution.output_data || {}, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
