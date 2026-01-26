import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { Search, Filter, AlertCircle, CheckCircle, Clock, ChevronDown, ChevronRight } from 'lucide-react'

interface TelemetryLog {
    id: string
    execution_id: string
    trace_id: string
    name: string
    kind: string
    status: string
    start_time: string
    end_time: string
    duration_ms: number
    tokens_used: number
    estimated_cost: number
    attributes: any
    events: any[]
}

export default function TelemetryLogs() {
    const [logs, setLogs] = useState<TelemetryLog[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [expandedLog, setExpandedLog] = useState<string | null>(null)
    const [autoRefresh, setAutoRefresh] = useState(true)

    useEffect(() => {
        loadLogs()

        if (autoRefresh) {
            const interval = setInterval(loadLogs, 5000) // Refresh every 5 seconds
            return () => clearInterval(interval)
        }
    }, [searchQuery, statusFilter, autoRefresh])

    const loadLogs = async () => {
        try {
            let query = supabase
                .from('telemetry_spans')
                .select('*')
                .order('start_time', { ascending: false })
                .limit(100)

            if (searchQuery) {
                query = query.or(`name.ilike.%${searchQuery}%,execution_id.ilike.%${searchQuery}%`)
            }

            if (statusFilter !== 'all') {
                query = query.eq('status', statusFilter)
            }

            const { data, error } = await query

            if (error) throw error
            setLogs(data || [])
        } catch (error) {
            console.error('Failed to load logs:', error)
        } finally {
            setLoading(false)
        }
    }

    const formatDuration = (ms: number) => {
        if (ms < 1000) return `${ms}ms`
        return `${(ms / 1000).toFixed(2)}s`
    }

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp)
        const now = new Date()
        const diff = now.getTime() - date.getTime()

        if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`

        return date.toLocaleString()
    }

    const getStatusIcon = (status: string) => {
        if (status === 'error') return <AlertCircle className="w-4 h-4 text-red-500" />
        return <CheckCircle className="w-4 h-4 text-green-500" />
    }

    return (
        <div className="p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Telemetry Logs</h1>
                    <p className="text-gray-600">Real-time execution logs and debugging</p>
                </div>

                {/* Controls */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                    <div className="flex gap-4 items-center">
                        {/* Search */}
                        <div className="flex-1">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                <input
                                    type="text"
                                    placeholder="Search by workflow name or execution ID..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        {/* Status Filter */}
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">All Status</option>
                            <option value="success">Success</option>
                            <option value="error">Error</option>
                        </select>

                        {/* Auto Refresh */}
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                                className="w-4 h-4"
                            />
                            <span className="text-sm text-gray-700">Auto-refresh</span>
                        </label>

                        {/* Refresh Button */}
                        <button
                            onClick={loadLogs}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                {/* Logs List */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                    {loading ? (
                        <div className="p-8 text-center text-gray-500">Loading logs...</div>
                    ) : logs.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">No logs found</div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {logs.map((log) => (
                                <div key={log.id} className="hover:bg-gray-50">
                                    {/* Log Row */}
                                    <div
                                        className="p-4 cursor-pointer"
                                        onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                                    >
                                        <div className="flex items-start gap-4">
                                            {/* Expand Icon */}
                                            <div className="mt-1">
                                                {expandedLog === log.id ? (
                                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                                ) : (
                                                    <ChevronRight className="w-5 h-5 text-gray-400" />
                                                )}
                                            </div>

                                            {/* Status Icon */}
                                            <div className="mt-1">
                                                {getStatusIcon(log.status)}
                                            </div>

                                            {/* Main Content */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-3 mb-1">
                                                    <span className="font-medium text-gray-900">{log.name}</span>
                                                    <span className="text-xs text-gray-500">{log.kind}</span>
                                                </div>
                                                <div className="flex items-center gap-4 text-sm text-gray-600">
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="w-3 h-3" />
                                                        {formatTimestamp(log.start_time)}
                                                    </span>
                                                    <span>Duration: {formatDuration(log.duration_ms)}</span>
                                                    {log.tokens_used > 0 && (
                                                        <span>Tokens: {log.tokens_used.toLocaleString()}</span>
                                                    )}
                                                    {log.estimated_cost > 0 && (
                                                        <span>Cost: ${log.estimated_cost.toFixed(4)}</span>
                                                    )}
                                                </div>
                                                <div className="text-xs text-gray-500 mt-1 font-mono">
                                                    Execution: {log.execution_id?.substring(0, 16)}...
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Expanded Details */}
                                    {expandedLog === log.id && (
                                        <div className="px-4 pb-4 border-t border-gray-100 bg-gray-50">
                                            <div className="mt-4 space-y-4">
                                                {/* Timestamps */}
                                                <div>
                                                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Timestamps</h4>
                                                    <div className="text-sm space-y-1">
                                                        <div><span className="text-gray-600">Start:</span> {new Date(log.start_time).toLocaleString()}</div>
                                                        <div><span className="text-gray-600">End:</span> {log.end_time ? new Date(log.end_time).toLocaleString() : 'N/A'}</div>
                                                    </div>
                                                </div>

                                                {/* IDs */}
                                                <div>
                                                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Identifiers</h4>
                                                    <div className="text-sm space-y-1 font-mono">
                                                        <div><span className="text-gray-600">Span ID:</span> {log.id}</div>
                                                        <div><span className="text-gray-600">Execution ID:</span> {log.execution_id}</div>
                                                        <div><span className="text-gray-600">Trace ID:</span> {log.trace_id}</div>
                                                    </div>
                                                </div>

                                                {/* Attributes */}
                                                {log.attributes && Object.keys(log.attributes).length > 0 && (
                                                    <div>
                                                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Attributes</h4>
                                                        <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto">
                                                            {JSON.stringify(log.attributes, null, 2)}
                                                        </pre>
                                                    </div>
                                                )}

                                                {/* Events */}
                                                {log.events && log.events.length > 0 && (
                                                    <div>
                                                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Events ({log.events.length})</h4>
                                                        <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto max-h-64">
                                                            {JSON.stringify(log.events, null, 2)}
                                                        </pre>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer Info */}
                <div className="mt-4 text-sm text-gray-500 text-center">
                    Showing {logs.length} most recent logs
                    {autoRefresh && ' • Auto-refreshing every 5 seconds'}
                </div>
            </div>
        </div>
    )
}
