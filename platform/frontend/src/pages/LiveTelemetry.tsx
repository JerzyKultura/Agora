import { useEffect, useState, useRef } from 'react'
import { supabase } from '../lib/supabase'
import { Pause, Play, Trash2, Filter, Radio } from 'lucide-react'

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

interface Execution {
    id: string
    workflow_id: string
}

interface Workflow {
    id: string
    name: string
}

export default function LiveTelemetry() {
    const [spans, setSpans] = useState<TelemetrySpan[]>([])
    const [isPaused, setIsPaused] = useState(false)
    const [filterMode, setFilterMode] = useState<'all' | 'llm' | 'agora'>('all')
    const [autoScroll, setAutoScroll] = useState(true)
    const [executions, setExecutions] = useState<Map<string, string>>(new Map())
    const bottomRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        // Load recent spans (last 50)
        loadRecentSpans()

        // Subscribe to new spans
        const channel = supabase
            .channel('live_telemetry_spans')
            .on('postgres_changes', {
                event: 'INSERT',
                schema: 'public',
                table: 'telemetry_spans'
            }, async (payload) => {
                if (!isPaused) {
                    const newSpan = payload.new as TelemetrySpan

                    // Load execution/workflow name if available
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

                    setSpans(prev => [newSpan, ...prev].slice(0, 200)) // Keep last 200
                }
            })
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [isPaused])

    useEffect(() => {
        if (autoScroll && bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [spans, autoScroll])

    const loadRecentSpans = async () => {
        try {
            const { data, error } = await supabase
                .from('telemetry_spans')
                .select('*')
                .order('created_at', { ascending: false })
                .limit(50)

            if (error) throw error

            if (data) {
                setSpans(data)

                // Load workflow names for executions
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

    const clearSpans = () => {
        setSpans([])
    }

    const formatTime = (timestamp: string) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3
        })
    }

    const formatDuration = (ms: number | null) => {
        if (!ms) return '-'
        if (ms < 1000) return `${ms}ms`
        return `${(ms / 1000).toFixed(2)}s`
    }

    const extractLLMInfo = (span: TelemetrySpan) => {
        const attrs = span.attributes || {}

        return {
            provider: attrs['llm.provider'] || attrs['traceloop.provider'],
            model: attrs['llm.model'] || attrs['gen_ai.request.model'],
            operation: attrs['llm.operation'] || attrs['gen_ai.operation.name'],
            promptPreview: attrs['llm.prompt'] || attrs['prompt.preview'] || attrs['gen_ai.prompt.0.content'],
            responsePreview: attrs['llm.response'] || attrs['response.preview'] || attrs['gen_ai.completion.0.content'],
            temperature: attrs['llm.temperature'] || attrs['gen_ai.request.temperature'],
            maxTokens: attrs['llm.max_tokens'] || attrs['gen_ai.request.max_tokens'],
            promptTokens: attrs['llm.usage.prompt_tokens'] || attrs['gen_ai.usage.prompt_tokens'],
            completionTokens: attrs['llm.usage.completion_tokens'] || attrs['gen_ai.usage.completion_tokens'],
        }
    }

    const isLLMSpan = (span: TelemetrySpan) => {
        const llmInfo = extractLLMInfo(span)
        return !!(llmInfo.provider || llmInfo.model || span.name.includes('openai') || span.name.includes('chat') || span.name.includes('completion'))
    }

    const isAgoraSpan = (span: TelemetrySpan) => {
        return span.attributes?.['agora.kind'] || span.name.includes('agora') || span.name.includes('.node')
    }

    const filteredSpans = spans.filter(span => {
        if (filterMode === 'llm') return isLLMSpan(span)
        if (filterMode === 'agora') return isAgoraSpan(span)
        return true
    })

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="mb-6 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <h1 className="text-3xl font-bold text-gray-900">Live Telemetry</h1>
                    <span className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${isPaused ? 'bg-gray-100 text-gray-700' : 'bg-green-100 text-green-700 animate-pulse'
                        }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${isPaused ? 'bg-gray-500' : 'bg-green-500'}`}></span>
                        {isPaused ? 'Paused' : 'Live'}
                    </span>
                    <span className="text-sm text-gray-500">
                        {filteredSpans.length} spans
                    </span>
                </div>

                {/* Controls */}
                <div className="flex gap-2">
                    <select
                        value={filterMode}
                        onChange={(e) => setFilterMode(e.target.value as 'all' | 'llm' | 'agora')}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                        <option value="all">All Spans</option>
                        <option value="llm">LLM Calls Only</option>
                        <option value="agora">Agora Nodes Only</option>
                    </select>

                    <button
                        onClick={() => setAutoScroll(!autoScroll)}
                        className={`px-3 py-2 border rounded-lg text-sm font-medium transition-colors ${autoScroll
                                ? 'bg-blue-50 border-blue-300 text-blue-700'
                                : 'bg-white border-gray-300 text-gray-700'
                            }`}
                    >
                        Auto-scroll: {autoScroll ? 'On' : 'Off'}
                    </button>

                    <button
                        onClick={() => setIsPaused(!isPaused)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isPaused
                                ? 'bg-green-100 border border-green-300 text-green-700'
                                : 'bg-yellow-100 border border-yellow-300 text-yellow-700'
                            }`}
                    >
                        {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                        {isPaused ? 'Resume' : 'Pause'}
                    </button>

                    <button
                        onClick={clearSpans}
                        className="flex items-center gap-2 px-4 py-2 bg-red-100 border border-red-300 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
                    >
                        <Trash2 className="w-4 h-4" />
                        Clear
                    </button>
                </div>
            </div>

            {/* Telemetry Stream */}
            <div className="flex-1 bg-gray-900 rounded-lg shadow-lg overflow-hidden flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-sm">
                    {filteredSpans.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <Radio className="w-12 h-12 mb-4 opacity-50" />
                            <p className="text-lg">Waiting for telemetry data...</p>
                            <p className="text-sm mt-2">Run a workflow to see live spans here</p>
                        </div>
                    ) : (
                        filteredSpans.map((span) => {
                            const llmInfo = extractLLMInfo(span)
                            const isLLM = isLLMSpan(span)
                            const isAgora = isAgoraSpan(span)
                            const workflowName = span.execution_id ? executions.get(span.execution_id) : null

                            return (
                                <div
                                    key={span.id}
                                    className={`border-l-4 p-3 rounded-r ${span.status === 'ERROR'
                                            ? 'border-red-500 bg-red-950/30'
                                            : isLLM
                                                ? 'border-purple-500 bg-purple-950/20'
                                                : isAgora
                                                    ? 'border-blue-500 bg-blue-950/20'
                                                    : 'border-gray-600 bg-gray-800/50'
                                        }`}
                                >
                                    {/* Header */}
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <span className="text-gray-400 text-xs">{formatTime(span.start_time)}</span>
                                            <span className={`font-semibold ${isLLM ? 'text-purple-400' : isAgora ? 'text-blue-400' : 'text-gray-300'
                                                }`}>
                                                {span.name}
                                            </span>
                                            {isLLM && (
                                                <span className="px-2 py-0.5 bg-purple-900/50 text-purple-300 rounded text-xs">
                                                    LLM
                                                </span>
                                            )}
                                            {isAgora && (
                                                <span className="px-2 py-0.5 bg-blue-900/50 text-blue-300 rounded text-xs">
                                                    NODE
                                                </span>
                                            )}
                                            {span.status === 'ERROR' && (
                                                <span className="px-2 py-0.5 bg-red-900/50 text-red-300 rounded text-xs">
                                                    ERROR
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-3 text-xs">
                                            {workflowName && (
                                                <span className="text-gray-500">{workflowName}</span>
                                            )}
                                            {span.duration_ms && (
                                                <span className="text-gray-400">{formatDuration(span.duration_ms)}</span>
                                            )}
                                        </div>
                                    </div>

                                    {/* LLM-specific Info */}
                                    {isLLM && (
                                        <div className="space-y-2 mb-2">
                                            {llmInfo.provider && (
                                                <div className="flex gap-2 text-xs">
                                                    <span className="text-gray-500">Provider:</span>
                                                    <span className="text-purple-300">{llmInfo.provider}</span>
                                                    {llmInfo.model && (
                                                        <>
                                                            <span className="text-gray-600">/</span>
                                                            <span className="text-purple-300">{llmInfo.model}</span>
                                                        </>
                                                    )}
                                                </div>
                                            )}

                                            {llmInfo.promptPreview && (
                                                <div className="bg-gray-800/80 p-2 rounded border border-purple-900/50">
                                                    <div className="text-xs text-purple-400 mb-1 font-semibold">Prompt:</div>
                                                    <div className="text-gray-300 text-xs whitespace-pre-wrap break-words">
                                                        {String(llmInfo.promptPreview).slice(0, 500)}
                                                        {String(llmInfo.promptPreview).length > 500 && '...'}
                                                    </div>
                                                </div>
                                            )}

                                            {llmInfo.responsePreview && (
                                                <div className="bg-gray-800/80 p-2 rounded border border-purple-900/50">
                                                    <div className="text-xs text-purple-400 mb-1 font-semibold">Response:</div>
                                                    <div className="text-gray-300 text-xs whitespace-pre-wrap break-words">
                                                        {String(llmInfo.responsePreview).slice(0, 500)}
                                                        {String(llmInfo.responsePreview).length > 500 && '...'}
                                                    </div>
                                                </div>
                                            )}

                                            <div className="flex gap-4 text-xs">
                                                {span.tokens_used && (
                                                    <span className="text-gray-400">
                                                        Tokens: <span className="text-purple-300 font-semibold">{span.tokens_used}</span>
                                                    </span>
                                                )}
                                                {llmInfo.promptTokens && (
                                                    <span className="text-gray-400">
                                                        ({llmInfo.promptTokens} + {llmInfo.completionTokens})
                                                    </span>
                                                )}
                                                {span.estimated_cost && (
                                                    <span className="text-gray-400">
                                                        Cost: <span className="text-green-400 font-semibold">${span.estimated_cost.toFixed(6)}</span>
                                                    </span>
                                                )}
                                                {llmInfo.temperature && (
                                                    <span className="text-gray-400">
                                                        Temp: <span className="text-gray-300">{llmInfo.temperature}</span>
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Agora Node Info */}
                                    {isAgora && span.attributes?.['agora.node'] && (
                                        <div className="text-xs mb-2">
                                            <span className="text-gray-500">Node: </span>
                                            <span className="text-blue-300">{span.attributes['agora.node']}</span>
                                        </div>
                                    )}

                                    {/* Span IDs */}
                                    <div className="flex gap-4 text-xs text-gray-600">
                                        <span>Span: {span.span_id.substring(0, 8)}</span>
                                        <span>Trace: {span.trace_id.substring(0, 16)}</span>
                                        {span.parent_span_id && (
                                            <span>Parent: {span.parent_span_id.substring(0, 8)}</span>
                                        )}
                                    </div>

                                    {/* All Attributes (collapsed by default) */}
                                    {Object.keys(span.attributes || {}).length > 0 && (
                                        <details className="mt-2">
                                            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                                                View all {Object.keys(span.attributes).length} attributes
                                            </summary>
                                            <pre className="mt-2 text-xs bg-gray-950/50 p-2 rounded overflow-x-auto text-gray-400">
                                                {JSON.stringify(span.attributes, null, 2)}
                                            </pre>
                                        </details>
                                    )}
                                </div>
                            )
                        })
                    )}
                    <div ref={bottomRef} />
                </div>
            </div>
        </div>
    )
}