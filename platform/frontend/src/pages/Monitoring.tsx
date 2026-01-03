import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { api } from '../lib/api'
import { ChevronRight, Clock, Zap, DollarSign, Radio, X, Activity, List } from 'lucide-react'

interface TelemetrySpan {
  id: string
  span_id: string
  trace_id: string
  parent_span_id: string | null
  execution_id: string | null
  name: string
  kind: string
  status: string
  start_time: string
  end_time: string | null
  duration_ms: number | null
  attributes: Record<string, any>
  events: any[]
  tokens_used: number | null
  estimated_cost: number | null
  created_at: string
}

interface Trace {
  trace_id: string
  spans: TelemetrySpan[]
  root_span: TelemetrySpan
  start_time: string
  end_time: string
  duration_ms: number
  total_tokens: number
  total_cost: number
  workflow_name?: string
  execution_id?: string
  // Aggregated LLM info
  llm_calls_count: number
  total_prompt_tokens: number
  total_completion_tokens: number
  models_used: string[]
  providers_used: string[]
  // Status tracking
  has_errors: boolean
  error_count: number
  success_count: number
  // Performance metrics
  avg_duration_ms: number
  max_duration_ms: number
  min_duration_ms: number
}

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

type ViewMode = 'traces' | 'executions'

export default function Monitoring() {
  const navigate = useNavigate()
  const [viewMode, setViewMode] = useState<ViewMode>('traces')

  // Traces view state
  const [spans, setSpans] = useState<TelemetrySpan[]>([])
  const [traces, setTraces] = useState<Trace[]>([])
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null)
  const [selectedSpan, setSelectedSpan] = useState<TelemetrySpan | null>(null)
  const [activeTab, setActiveTab] = useState<'prompt' | 'completions' | 'llm_data' | 'details' | 'raw'>('prompt')

  // Executions view state
  const [executions, setExecutions] = useState<Execution[]>([])
  const [workflows, setWorkflows] = useState<Map<string, Workflow>>(new Map())
  const [filter, setFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)

  // Shared state
  const [executionNames, setExecutionNames] = useState<Map<string, string>>(new Map())

  useEffect(() => {
    loadRecentSpans()
    loadExecutions()

    const channel = supabase
      .channel('monitoring_telemetry_spans')
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'telemetry_spans'
      }, async (payload) => {
        const newSpan = payload.new as TelemetrySpan

        if (newSpan.execution_id && !executionNames.has(newSpan.execution_id)) {
          try {
            const { data: exec } = await supabase
              .from('executions')
              .select('workflow_id, workflows(name)')
              .eq('id', newSpan.execution_id)
              .single()

            if (exec) {
              const workflowName = (exec as any).workflows?.name || 'Unknown'
              setExecutionNames(prev => new Map(prev).set(newSpan.execution_id!, workflowName))
            }
          } catch (e) {
            console.error('Failed to load execution:', e)
          }
        }

        setSpans(prev => [newSpan, ...prev].slice(0, 200))
      })
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'executions'
      }, () => loadExecutions())
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  useEffect(() => {
    // Group spans by trace_id
    const traceMap = new Map<string, TelemetrySpan[]>()

    spans.forEach(span => {
      if (!traceMap.has(span.trace_id)) {
        traceMap.set(span.trace_id, [])
      }
      traceMap.get(span.trace_id)!.push(span)
    })

    const tracesArray: Trace[] = Array.from(traceMap.entries()).map(([trace_id, traceSpans]) => {
      const sortedSpans = traceSpans.sort((a, b) =>
        new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
      )

      const rootSpan = sortedSpans.find(s => !s.parent_span_id) || sortedSpans[0]

      // Calculate times
      const minTime = Math.min(...sortedSpans.map(s => new Date(s.start_time).getTime()))
      const maxTime = Math.max(...sortedSpans.map(s => new Date(s.end_time || s.start_time).getTime()))

      // Token aggregation
      const totalTokens = traceSpans.reduce((sum, s) => sum + (s.tokens_used || 0), 0)
      const totalCost = traceSpans.reduce((sum, s) => sum + (s.estimated_cost || 0), 0)

      // LLM-specific metrics
      const llmSpans = traceSpans.filter(s => isLLMSpan(s))
      const totalPromptTokens = llmSpans.reduce((sum, s) => {
        const llmInfo = extractLLMInfo(s)
        return sum + llmInfo.promptTokens
      }, 0)
      const totalCompletionTokens = llmSpans.reduce((sum, s) => {
        const llmInfo = extractLLMInfo(s)
        return sum + llmInfo.completionTokens
      }, 0)

      // Extract unique models and providers
      const models = new Set<string>()
      const providers = new Set<string>()
      llmSpans.forEach(s => {
        const llmInfo = extractLLMInfo(s)
        if (llmInfo.model) models.add(llmInfo.model)
        if (llmInfo.provider) providers.add(llmInfo.provider)
      })

      // Status tracking
      const errorSpans = traceSpans.filter(s => s.status === 'ERROR')
      const successSpans = traceSpans.filter(s => s.status === 'OK')

      // Performance metrics
      const durations = sortedSpans.filter(s => s.duration_ms !== null).map(s => s.duration_ms!)
      const avgDuration = durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : 0
      const maxDuration = durations.length > 0 ? Math.max(...durations) : 0
      const minDuration = durations.length > 0 ? Math.min(...durations) : 0

      const workflowName = rootSpan.execution_id ? executionNames.get(rootSpan.execution_id) : undefined

      return {
        trace_id,
        spans: sortedSpans,
        root_span: rootSpan,
        start_time: new Date(minTime).toISOString(),
        end_time: new Date(maxTime).toISOString(),
        duration_ms: maxTime - minTime,
        total_tokens: totalTokens,
        total_cost: totalCost,
        workflow_name,
        execution_id: rootSpan.execution_id || undefined,
        llm_calls_count: llmSpans.length,
        total_prompt_tokens: totalPromptTokens,
        total_completion_tokens: totalCompletionTokens,
        models_used: Array.from(models),
        providers_used: Array.from(providers),
        has_errors: errorSpans.length > 0,
        error_count: errorSpans.length,
        success_count: successSpans.length,
        avg_duration_ms: avgDuration,
        max_duration_ms: maxDuration,
        min_duration_ms: minDuration
      }
    })

    setTraces(tracesArray.sort((a, b) =>
      new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
    ))
  }, [spans, executionNames])

  const loadRecentSpans = async () => {
    try {
      const { data, error } = await supabase
        .from('telemetry_spans')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100)

      if (error) throw error

      if (data) {
        setSpans(data)

        const executionIds = [...new Set(data.map(s => s.execution_id).filter(Boolean))]
        const execMap = new Map<string, string>()

        for (const execId of executionIds) {
          try {
            const { data: exec } = await supabase
              .from('executions')
              .select('workflow_id, workflows(name)')
              .eq('id', execId)
              .single()

            if (exec) {
              const workflowName = (exec as any).workflows?.name || 'Unknown'
              execMap.set(execId!, workflowName)
            }
          } catch (e) {
            console.error('Failed to load execution:', e)
          }
        }

        setExecutionNames(execMap)
      }
    } catch (error) {
      console.error('Failed to load recent spans:', error)
    }
  }

  const loadExecutions = async () => {
    try {
      setLoading(true)
      const projectsData = await api.projects.list()

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
    } catch (error) {
      console.error('Failed to load executions:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
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

  const extractLLMInfo = (span: TelemetrySpan) => {
    const attrs = span.attributes || {}

    // Extract all prompts (handle multiple messages)
    const prompts: Array<{role: string, content: string}> = []
    let i = 0
    while (attrs[`gen_ai.prompt.${i}.content`] || attrs[`gen_ai.prompt.${i}.role`]) {
      prompts.push({
        role: attrs[`gen_ai.prompt.${i}.role`] || 'user',
        content: attrs[`gen_ai.prompt.${i}.content`] || ''
      })
      i++
    }

    // Extract completions
    const completions: Array<{role: string, content: string}> = []
    i = 0
    while (attrs[`gen_ai.completion.${i}.content`] || attrs[`gen_ai.completion.${i}.role`]) {
      completions.push({
        role: attrs[`gen_ai.completion.${i}.role`] || 'assistant',
        content: attrs[`gen_ai.completion.${i}.content`] || ''
      })
      i++
    }

    return {
      provider: attrs['gen_ai.system'] || attrs['llm.provider'],
      model: attrs['gen_ai.request.model'] || attrs['gen_ai.response.model'] || attrs['llm.model'],
      temperature: attrs['gen_ai.request.temperature'] || attrs['llm.temperature'],
      maxTokens: attrs['gen_ai.request.max_tokens'] || attrs['llm.max_tokens'],
      promptTokens: attrs['gen_ai.usage.input_tokens'] || attrs['llm.usage.prompt_tokens'] || 0,
      completionTokens: attrs['gen_ai.usage.output_tokens'] || attrs['llm.usage.completion_tokens'] || 0,
      totalTokens: attrs['llm.usage.total_tokens'] ||
                   (attrs['gen_ai.usage.input_tokens'] || 0) + (attrs['gen_ai.usage.output_tokens'] || 0),
      prompts,
      completions,
      finishReason: attrs['gen_ai.response.finish_reasons'] || attrs['llm.finish_reason'],
      apiBase: attrs['gen_ai.openai.api_base'],
      responseId: attrs['gen_ai.response.id']
    }
  }

  const isLLMSpan = (span: TelemetrySpan) => {
    const attrs = span.attributes || {}
    return !!(attrs['gen_ai.system'] || attrs['llm.provider'] || span.name.includes('openai') || span.name.includes('chat'))
  }

  const closeDetail = () => {
    setSelectedTrace(null)
    setSelectedSpan(null)
  }

  const renderPromptTab = (span: TelemetrySpan) => {
    const llmInfo = extractLLMInfo(span)

    if (llmInfo.prompts.length === 0) {
      return (
        <div className="text-gray-400 text-sm">No prompt data available</div>
      )
    }

    return (
      <div className="space-y-3">
        <div className="text-sm font-semibold text-gray-300">Prompts</div>
        {llmInfo.prompts.map((msg, idx) => (
          <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-xs font-semibold text-purple-400 mb-2 uppercase">{msg.role}</div>
            <div className="text-sm text-gray-300 whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
      </div>
    )
  }

  const renderCompletionsTab = (span: TelemetrySpan) => {
    const llmInfo = extractLLMInfo(span)

    if (llmInfo.completions.length === 0) {
      return (
        <div className="text-gray-400 text-sm">No completion data available</div>
      )
    }

    return (
      <div className="space-y-3">
        <div className="text-sm font-semibold text-gray-300">Completions</div>
        {llmInfo.completions.map((msg, idx) => (
          <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-xs font-semibold text-green-400 mb-2 uppercase">{msg.role}</div>
            <div className="text-sm text-gray-300 whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
        {llmInfo.finishReason && (
          <div className="text-xs text-gray-500">
            Finish reason: <span className="text-gray-400">{String(llmInfo.finishReason)}</span>
          </div>
        )}
      </div>
    )
  }

  const renderLLMDataTab = (span: TelemetrySpan) => {
    const llmInfo = extractLLMInfo(span)

    return (
      <div className="space-y-4">
        <div>
          <div className="text-xs text-gray-500 mb-1">Model</div>
          <div className="text-sm text-gray-200">{llmInfo.model || 'N/A'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Provider</div>
          <div className="text-sm text-gray-200">{llmInfo.provider || 'N/A'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Temperature</div>
          <div className="text-sm text-gray-200">{llmInfo.temperature ?? 'N/A'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Max Tokens</div>
          <div className="text-sm text-gray-200">{llmInfo.maxTokens || 'N/A'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Token Usage</div>
          <div className="text-sm text-gray-200">
            {llmInfo.promptTokens} input + {llmInfo.completionTokens} output = {llmInfo.totalTokens} total
          </div>
        </div>
        {span.estimated_cost && (
          <div>
            <div className="text-xs text-gray-500 mb-1">Estimated Cost</div>
            <div className="text-sm text-green-400 font-semibold">${span.estimated_cost.toFixed(6)}</div>
          </div>
        )}
        {llmInfo.apiBase && (
          <div>
            <div className="text-xs text-gray-500 mb-1">API Base</div>
            <div className="text-sm text-gray-200 font-mono text-xs">{llmInfo.apiBase}</div>
          </div>
        )}
        {llmInfo.responseId && (
          <div>
            <div className="text-xs text-gray-500 mb-1">Response ID</div>
            <div className="text-sm text-gray-200 font-mono text-xs">{llmInfo.responseId}</div>
          </div>
        )}
      </div>
    )
  }

  const renderDetailsTab = (span: TelemetrySpan) => {
    return (
      <div className="space-y-4">
        <div>
          <div className="text-xs text-gray-500 mb-1">Span ID</div>
          <div className="text-sm text-gray-200 font-mono">{span.span_id}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Trace ID</div>
          <div className="text-sm text-gray-200 font-mono">{span.trace_id}</div>
        </div>
        {span.parent_span_id && (
          <div>
            <div className="text-xs text-gray-500 mb-1">Parent Span ID</div>
            <div className="text-sm text-gray-200 font-mono">{span.parent_span_id}</div>
          </div>
        )}
        <div>
          <div className="text-xs text-gray-500 mb-1">Name</div>
          <div className="text-sm text-gray-200">{span.name}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Kind</div>
          <div className="text-sm text-gray-200">{span.kind}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Status</div>
          <div className={`text-sm ${span.status === 'ERROR' ? 'text-red-400' : 'text-green-400'}`}>
            {span.status}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Start Time</div>
          <div className="text-sm text-gray-200">{new Date(span.start_time).toLocaleString()}</div>
        </div>
        {span.end_time && (
          <div>
            <div className="text-xs text-gray-500 mb-1">End Time</div>
            <div className="text-sm text-gray-200">{new Date(span.end_time).toLocaleString()}</div>
          </div>
        )}
        {span.duration_ms !== null && (
          <div>
            <div className="text-xs text-gray-500 mb-1">Duration</div>
            <div className="text-sm text-gray-200">{formatDuration(span.duration_ms)}</div>
          </div>
        )}
      </div>
    )
  }

  const renderRawTab = (span: TelemetrySpan) => {
    return (
      <pre className="text-xs bg-gray-950 p-4 rounded overflow-auto text-gray-300 font-mono">
        {JSON.stringify(span, null, 2)}
      </pre>
    )
  }

  // Calculate aggregated metrics for executions view
  const totalTokensUsed = executions.reduce((sum, e) => sum + (e.tokens_used || 0), 0)
  const totalCost = executions.reduce((sum, e) => sum + (e.estimated_cost || 0), 0)
  const successCount = executions.filter(e => e.status === 'success').length
  const errorCount = executions.filter(e => e.status === 'error').length
  const runningCount = executions.filter(e => e.status === 'running').length

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">Monitoring</h1>
            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">
              LIVE
            </span>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex gap-2 border-b border-gray-200">
          <button
            onClick={() => setViewMode('traces')}
            className={`px-4 py-2 font-medium text-sm transition-colors flex items-center gap-2 ${
              viewMode === 'traces'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Activity className="w-4 h-4" />
            Traces
            <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{traces.length}</span>
          </button>
          <button
            onClick={() => setViewMode('executions')}
            className={`px-4 py-2 font-medium text-sm transition-colors flex items-center gap-2 ${
              viewMode === 'executions'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <List className="w-4 h-4" />
            Executions
            <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{executions.length}</span>
          </button>
        </div>

        {/* Aggregated Metrics Bar (only for executions view) */}
        {viewMode === 'executions' && executions.length > 0 && (
          <div className="mt-4 grid grid-cols-5 gap-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-xs text-blue-600 font-semibold mb-1">Total Executions</div>
              <div className="text-2xl font-bold text-blue-900">{executions.length}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-xs text-green-600 font-semibold mb-1">Success</div>
              <div className="text-2xl font-bold text-green-900">{successCount}</div>
            </div>
            <div className="bg-red-50 rounded-lg p-3">
              <div className="text-xs text-red-600 font-semibold mb-1">Errors</div>
              <div className="text-2xl font-bold text-red-900">{errorCount}</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-3">
              <div className="text-xs text-purple-600 font-semibold mb-1">Total Tokens</div>
              <div className="text-2xl font-bold text-purple-900">{totalTokensUsed.toLocaleString()}</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3">
              <div className="text-xs text-yellow-600 font-semibold mb-1">Total Cost</div>
              <div className="text-2xl font-bold text-yellow-900">${totalCost.toFixed(4)}</div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        {viewMode === 'traces' ? (
          // TRACES VIEW
          <>
            {!selectedTrace && (
              <div className="flex-1 overflow-y-auto bg-white">
                {traces.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-400">
                    <Radio className="w-16 h-16 mb-4" />
                    <p className="text-lg font-medium">Waiting for telemetry data...</p>
                    <p className="text-sm mt-2">Run a workflow to see traces appear here</p>
                    <p className="text-xs mt-4 text-gray-500">💾 All historical data is stored permanently</p>
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Trace
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Model / Provider
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Spans
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <Clock className="w-4 h-4 inline mr-1" />
                          Duration
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <Zap className="w-4 h-4 inline mr-1" />
                          Tokens
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <DollarSign className="w-4 h-4 inline mr-1" />
                          Cost
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Time
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {traces.map((trace) => (
                        <tr
                          key={trace.trace_id}
                          onClick={() => {
                            setSelectedTrace(trace)
                            setSelectedSpan(trace.root_span)
                          }}
                          className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                            trace.has_errors ? 'bg-red-50' : ''
                          }`}
                        >
                          <td className="px-6 py-4">
                            <div className="text-sm font-medium text-gray-900">
                              {trace.workflow_name || trace.root_span.name}
                            </div>
                            <div className="text-xs text-gray-500 font-mono">
                              {trace.trace_id.substring(0, 16)}...
                            </div>
                            {trace.llm_calls_count > 0 && (
                              <div className="mt-1">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                  {trace.llm_calls_count} LLM call{trace.llm_calls_count > 1 ? 's' : ''}
                                </span>
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            {trace.models_used.length > 0 ? (
                              <div className="space-y-1">
                                {trace.models_used.map((model, idx) => (
                                  <div key={idx} className="text-sm text-gray-900">{model}</div>
                                ))}
                                {trace.providers_used.length > 0 && (
                                  <div className="text-xs text-gray-500">
                                    {trace.providers_used.join(', ')}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-sm text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            {trace.has_errors ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                {trace.error_count} error{trace.error_count > 1 ? 's' : ''}
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Success
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {trace.spans.length}
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm text-gray-900">{formatDuration(trace.duration_ms)}</div>
                            {trace.avg_duration_ms > 0 && (
                              <div className="text-xs text-gray-500">
                                avg {formatDuration(trace.avg_duration_ms)}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            {trace.total_tokens > 0 ? (
                              <div>
                                <div className="text-sm text-gray-900">
                                  {trace.total_tokens.toLocaleString()}
                                </div>
                                {trace.llm_calls_count > 0 && (
                                  <div className="text-xs text-gray-500">
                                    {trace.total_prompt_tokens} + {trace.total_completion_tokens}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-sm text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            {trace.total_cost > 0 ? (
                              <span className="text-sm text-green-600 font-semibold">
                                ${trace.total_cost.toFixed(6)}
                              </span>
                            ) : (
                              <span className="text-sm text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {formatTime(trace.start_time)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {/* Trace Detail View */}
            {selectedTrace && (
              <div className="flex-1 flex flex-col">
                {/* Trace Summary Header */}
                <div className="bg-white border-b border-gray-200 px-6 py-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-bold text-gray-900">
                        {selectedTrace.workflow_name || selectedTrace.root_span.name}
                      </h2>
                      {selectedTrace.has_errors ? (
                        <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-semibold">
                          {selectedTrace.error_count} ERROR{selectedTrace.error_count > 1 ? 'S' : ''}
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">
                          SUCCESS
                        </span>
                      )}
                    </div>
                    <button
                      onClick={closeDetail}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Comprehensive Trace Stats Grid */}
                  <div className="grid grid-cols-6 gap-4">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Trace ID</div>
                      <div className="text-sm font-mono text-gray-900">{selectedTrace.trace_id.substring(0, 16)}...</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Total Spans</div>
                      <div className="text-sm font-semibold text-gray-900">{selectedTrace.spans.length}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Duration</div>
                      <div className="text-sm font-semibold text-gray-900">{formatDuration(selectedTrace.duration_ms)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Total Tokens</div>
                      <div className="text-sm font-semibold text-gray-900">
                        {selectedTrace.total_tokens > 0 ? selectedTrace.total_tokens.toLocaleString() : '-'}
                      </div>
                      {selectedTrace.llm_calls_count > 0 && (
                        <div className="text-xs text-gray-500">
                          {selectedTrace.total_prompt_tokens} in + {selectedTrace.total_completion_tokens} out
                        </div>
                      )}
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Total Cost</div>
                      <div className="text-sm font-semibold text-green-600">
                        {selectedTrace.total_cost > 0 ? `$${selectedTrace.total_cost.toFixed(6)}` : '-'}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Started</div>
                      <div className="text-sm text-gray-900">{formatTime(selectedTrace.start_time)}</div>
                    </div>
                  </div>

                  {/* LLM Specific Stats */}
                  {selectedTrace.llm_calls_count > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-5 gap-4">
                      <div>
                        <div className="text-xs text-gray-500 mb-1">LLM Calls</div>
                        <div className="text-sm font-semibold text-purple-600">{selectedTrace.llm_calls_count}</div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Models Used</div>
                        <div className="text-sm text-gray-900">
                          {selectedTrace.models_used.length > 0 ? selectedTrace.models_used.join(', ') : '-'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Providers</div>
                        <div className="text-sm text-gray-900">
                          {selectedTrace.providers_used.length > 0 ? selectedTrace.providers_used.join(', ') : '-'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Avg Duration</div>
                        <div className="text-sm text-gray-900">{formatDuration(selectedTrace.avg_duration_ms)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Duration Range</div>
                        <div className="text-sm text-gray-900">
                          {formatDuration(selectedTrace.min_duration_ms)} - {formatDuration(selectedTrace.max_duration_ms)}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex-1 flex overflow-hidden">
                  {/* Left: Span List */}
                  <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
                    <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3">
                      <div className="text-sm font-semibold text-gray-900">Spans ({selectedTrace.spans.length})</div>
                    </div>
                    <div className="divide-y divide-gray-100">
                      {selectedTrace.spans.map((span) => {
                        const isSelected = selectedSpan?.span_id === span.span_id
                        const isLLM = isLLMSpan(span)

                        return (
                          <div
                            key={span.span_id}
                            onClick={() => {
                              setSelectedSpan(span)
                              if (isLLM) {
                                setActiveTab('prompt')
                              } else {
                                setActiveTab('details')
                              }
                            }}
                            className={`px-4 py-3 cursor-pointer transition-colors ${
                              isSelected ? 'bg-blue-50 border-l-4 border-l-blue-500' : 'hover:bg-gray-50 border-l-4 border-l-transparent'
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <ChevronRight className={`w-4 h-4 text-gray-400 ${isSelected ? 'rotate-90' : ''}`} />
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {span.name}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  {isLLM && (
                                    <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-semibold">
                                      LLM
                                    </span>
                                  )}
                                  {span.duration_ms && (
                                    <span className="text-xs text-gray-500">
                                      {formatDuration(span.duration_ms)}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Right: Span Inspector */}
                  {selectedSpan && (
                    <div className="flex-1 bg-gray-900 flex flex-col">
                      {/* Tabs */}
                      <div className="bg-gray-800 border-b border-gray-700 flex gap-1 px-4">
                        {isLLMSpan(selectedSpan) ? (
                          <>
                            <button
                              onClick={() => setActiveTab('prompt')}
                              className={`px-4 py-3 text-sm font-medium transition-colors ${
                                activeTab === 'prompt'
                                  ? 'text-white border-b-2 border-blue-500'
                                  : 'text-gray-400 hover:text-gray-300'
                              }`}
                            >
                              Prompt
                            </button>
                            <button
                              onClick={() => setActiveTab('completions')}
                              className={`px-4 py-3 text-sm font-medium transition-colors ${
                                activeTab === 'completions'
                                  ? 'text-white border-b-2 border-blue-500'
                                  : 'text-gray-400 hover:text-gray-300'
                              }`}
                            >
                              Completions
                            </button>
                            <button
                              onClick={() => setActiveTab('llm_data')}
                              className={`px-4 py-3 text-sm font-medium transition-colors ${
                                activeTab === 'llm_data'
                                  ? 'text-white border-b-2 border-blue-500'
                                  : 'text-gray-400 hover:text-gray-300'
                              }`}
                            >
                              LLM Data
                            </button>
                          </>
                        ) : null}
                        <button
                          onClick={() => setActiveTab('details')}
                          className={`px-4 py-3 text-sm font-medium transition-colors ${
                            activeTab === 'details'
                              ? 'text-white border-b-2 border-blue-500'
                              : 'text-gray-400 hover:text-gray-300'
                          }`}
                        >
                          Details
                        </button>
                        <button
                          onClick={() => setActiveTab('raw')}
                          className={`px-4 py-3 text-sm font-medium transition-colors ${
                            activeTab === 'raw'
                              ? 'text-white border-b-2 border-blue-500'
                              : 'text-gray-400 hover:text-gray-300'
                          }`}
                        >
                          Raw
                        </button>
                      </div>

                      {/* Tab Content */}
                      <div className="flex-1 overflow-y-auto p-6">
                        {activeTab === 'prompt' && renderPromptTab(selectedSpan)}
                        {activeTab === 'completions' && renderCompletionsTab(selectedSpan)}
                        {activeTab === 'llm_data' && renderLLMDataTab(selectedSpan)}
                        {activeTab === 'details' && renderDetailsTab(selectedSpan)}
                        {activeTab === 'raw' && renderRawTab(selectedSpan)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          // EXECUTIONS VIEW
          <div className="flex-1 overflow-y-auto bg-white p-6">
            <div className="mb-4 flex gap-4 items-center">
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

            {loading && executions.length === 0 ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
            ) : executions.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <div className="text-6xl mb-4">🚀</div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">No Execution Data Yet</h3>
                <p className="text-gray-600">Run your Python workflow to see execution data here!</p>
                <p className="text-sm text-gray-500 mt-4">💾 All historical data is stored permanently</p>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Workflow</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {executions.map((execution) => {
                      const workflow = workflows.get(execution.workflow_id)
                      return (
                        <tr key={execution.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="font-medium">{workflow?.name || 'Unknown'}</div>
                            <div className="text-xs text-gray-400 font-mono">{execution.id.substring(0, 8)}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(execution.status)}`}>
                              {execution.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(execution.started_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {execution.duration_ms ? formatDuration(execution.duration_ms) : '-'}
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
        )}
      </div>
    </div>
  )
}
