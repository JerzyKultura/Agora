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

interface Span {
  id: string
  span_id: string
  trace_id: string
  parent_span_id: string | null
  name: string
  kind: string
  status: string
  start_time: string
  end_time: string | null
  duration_ms: number | null
  attributes: any
  events: any[]
}

function TraceRow({ span, allSpans, depth, onSelect, selectedId }: {
  span: Span,
  allSpans: Span[],
  depth: number,
  onSelect: (span: Span) => void,
  selectedId?: string
}) {
  const children = allSpans.filter(s => s.parent_span_id === span.span_id)
  const isSelected = selectedId === span.span_id

  return (
    <div>
      <div
        onClick={() => onSelect(span)}
        className={`flex items-center gap-2 py-1.5 px-3 cursor-pointer hover:bg-blue-50 transition-colors border-l-2 ${isSelected ? 'bg-blue-50 border-blue-500' : 'border-transparent'
          }`}
        style={{ paddingLeft: `${depth * 20 + 12}px` }}
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {children.length > 0 ? (
            <span className="text-[10px] text-gray-400">▼</span>
          ) : (
            <span className="w-2" />
          )}
          <span className={`text-sm font-medium truncate ${isSelected ? 'text-blue-700' : 'text-gray-700'}`}>
            {span.name}
          </span>
          {span.kind.includes('SERVER') && (
            <span className="text-[10px] bg-purple-100 text-purple-700 px-1 rounded">server</span>
          )}
          {span.attributes['llm.model_name'] && (
            <span className="text-[10px] bg-green-100 text-green-700 px-1 rounded truncate max-w-[100px]">
              {span.attributes['llm.model_name']}
            </span>
          )}
        </div>
        <div className="text-[10px] text-gray-400 font-mono">
          {span.duration_ms ? `${span.duration_ms}ms` : ''}
        </div>
      </div>
      {children.map(child => (
        <TraceRow
          key={child.span_id}
          span={child}
          allSpans={allSpans}
          depth={depth + 1}
          onSelect={onSelect}
          selectedId={selectedId}
        />
      ))}
    </div>
  )
}

export default function ExecutionDetail() {
  const { executionId } = useParams()
  const navigate = useNavigate()
  const [execution, setExecution] = useState<Execution | null>(null)
  const [nodeExecutions, setNodeExecutions] = useState<NodeExecution[]>([])
  const [spans, setSpans] = useState<Span[]>([])
  const [nodes, setNodes] = useState<Map<string, Node>>(new Map())
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'timeline' | 'trace' | 'details' | 'data'>('timeline')
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null)

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

      const spansData = await api.executions.getSpans(executionId!)
      setSpans(spansData)
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
            onClick={() => setActiveTab('trace')}
            className={`px-4 py-2 font-medium ${activeTab === 'trace' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Trace (Spans)
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

      {activeTab === 'trace' && (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-8 bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
              <h3 className="font-semibold text-gray-700">Trace Tree</h3>
              <span className="text-xs text-gray-500">{spans.length} spans</span>
            </div>
            <div className="p-4 overflow-x-auto">
              <div className="min-w-max">
                {spans.filter(s => !s.parent_span_id).map(span => (
                  <TraceRow
                    key={span.span_id}
                    span={span}
                    allSpans={spans}
                    depth={0}
                    onSelect={setSelectedSpan}
                    selectedId={selectedSpan?.span_id}
                  />
                ))}
                {spans.length === 0 && (
                  <div className="p-8 text-center text-gray-500">
                    No span data found. Make sure opentelemetry is correctly configured.
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="col-span-12 lg:col-span-4 space-y-4">
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-semibold text-gray-700 mb-4 border-b pb-2">Span Attributes</h3>
              {selectedSpan ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-gray-500 uppercase font-bold">Name</div>
                    <div className="text-sm font-mono text-blue-600">{selectedSpan.name}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 uppercase font-bold">Status</div>
                    <span className={`text-xs px-2 py-0.5 rounded font-semibold ${selectedSpan.status === 'ERROR' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                      {selectedSpan.status}
                    </span>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 uppercase font-bold mb-1">Attributes</div>
                    <pre className="text-xs bg-gray-50 p-2 rounded border overflow-auto max-h-64">
                      {JSON.stringify(selectedSpan.attributes, null, 2)}
                    </pre>
                  </div>
                  {selectedSpan.events && selectedSpan.events.length > 0 && (
                    <div>
                      <div className="text-xs text-gray-500 uppercase font-bold mb-1">Events</div>
                      <div className="space-y-2">
                        {selectedSpan.events.map((e: any, i: number) => (
                          <div key={i} className="text-xs border-l-2 border-blue-400 pl-2 py-1 bg-blue-50 rounded-r">
                            <span className="font-semibold">{e.name}</span>
                            <div className="text-[10px] text-gray-500">{new Date(e.timestamp).toLocaleTimeString()}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-400 italic text-center py-10">
                  Select a span to view details
                </div>
              )}
            </div>
          </div>
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
