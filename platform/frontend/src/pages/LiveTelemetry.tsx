import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { ChevronRight, Clock, Zap, DollarSign, Radio, X } from 'lucide-react'

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
  duration_ms: number
  total_tokens: number
  total_cost: number
  workflow_name?: string
}

export default function LiveTelemetry() {
  const [spans, setSpans] = useState<TelemetrySpan[]>([])
  const [traces, setTraces] = useState<Trace[]>([])
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null)
  const [selectedSpan, setSelectedSpan] = useState<TelemetrySpan | null>(null)
  const [activeTab, setActiveTab] = useState<'prompt' | 'completions' | 'llm_data' | 'details' | 'raw'>('prompt')
  const [executions, setExecutions] = useState<Map<string, string>>(new Map())

  useEffect(() => {
    loadRecentSpans()

    const channel = supabase
      .channel('live_telemetry_spans')
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'telemetry_spans'
      }, async (payload) => {
        const newSpan = payload.new as TelemetrySpan

        if (newSpan.execution_id && !executions.has(newSpan.execution_id)) {
          try {
            const { data: exec } = await supabase
              .from('executions')
              .select('workflow_id, workflows(name)')
              .eq('id', newSpan.execution_id)
              .single()

            if (exec) {
              const workflowName = (exec as any).workflows?.name || 'Unknown'
              setExecutions(prev => new Map(prev).set(newSpan.execution_id!, workflowName))
            }
          } catch (e) {
            console.error('Failed to load execution:', e)
          }
        }

        setSpans(prev => [newSpan, ...prev].slice(0, 200))
      })
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
      const totalTokens = traceSpans.reduce((sum, s) => sum + (s.tokens_used || 0), 0)
      const totalCost = traceSpans.reduce((sum, s) => sum + (s.estimated_cost || 0), 0)

      const minTime = Math.min(...sortedSpans.map(s => new Date(s.start_time).getTime()))
      const maxTime = Math.max(...sortedSpans.map(s => new Date(s.end_time || s.start_time).getTime()))

      const workflowName = rootSpan.execution_id ? executions.get(rootSpan.execution_id) : undefined

      return {
        trace_id,
        spans: sortedSpans,
        root_span: rootSpan,
        start_time: new Date(minTime).toISOString(),
        duration_ms: maxTime - minTime,
        total_tokens: totalTokens,
        total_cost: totalCost,
        workflow_name
      }
    })

    setTraces(tracesArray.sort((a, b) =>
      new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
    ))
  }, [spans, executions])

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

        setExecutions(execMap)
      }
    } catch (error) {
      console.error('Failed to load recent spans:', error)
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

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
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

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">Tracing</h1>
            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">
              LIVE
            </span>
            <span className="text-sm text-gray-500">{traces.length} traces</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Traces List */}
        {!selectedTrace && (
          <div className="flex-1 overflow-y-auto bg-white">
            {traces.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <Radio className="w-16 h-16 mb-4" />
                <p className="text-lg font-medium">Waiting for telemetry data...</p>
                <p className="text-sm mt-2">Run a workflow to see traces appear here</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Trace
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
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {trace.workflow_name || trace.root_span.name}
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
                          {trace.trace_id.substring(0, 16)}...
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {trace.spans.length}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {formatDuration(trace.duration_ms)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {trace.total_tokens > 0 ? trace.total_tokens.toLocaleString() : '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-green-600 font-semibold">
                        {trace.total_cost > 0 ? `$${trace.total_cost.toFixed(6)}` : '-'}
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
          <div className="flex-1 flex">
            {/* Left: Span List */}
            <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <div className="text-sm font-semibold text-gray-900">Spans</div>
                <button
                  onClick={closeDetail}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
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
        )}
      </div>
    </div>
  )
}
