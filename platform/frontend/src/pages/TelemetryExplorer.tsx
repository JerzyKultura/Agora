import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { Search, Filter, Database, Brain, Activity } from 'lucide-react'

interface Span {
    id: string
    execution_id: string
    name: string
    start_time: string
    end_time: string | null
    duration_ms: number | null
    status: string
    attributes: any
    events: any[]
}

export default function TelemetryExplorer() {
    const [spans, setSpans] = useState<Span[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedSpan, setSelectedSpan] = useState<Span | null>(null)

    // Filters
    const [limit, setLimit] = useState(100)
    const [nameFilter, setNameFilter] = useState('')
    const [attrFilter, setAttrFilter] = useState('')

    // Live Mode
    const [liveMode, setLiveMode] = useState(false)
    const [refreshTrigger, setRefreshTrigger] = useState(0)

    useEffect(() => {
        fetchSpans()
    }, [limit, refreshTrigger])

    // Auto-Refresh for Live Mode
    useEffect(() => {
        if (!liveMode) return
        const interval = setInterval(() => {
            // Use a trigger instead of calling fetchSpans directly to avoid race conditions/closures
            setRefreshTrigger(prev => prev + 1)
        }, 3000)
        return () => clearInterval(interval)
    }, [liveMode])

    const fetchSpans = async () => {
        setLoading(true)
        try {
            let query = supabase
                .from('telemetry_spans')
                .select('*')
                .order('start_time', { ascending: false })
                .limit(limit)

            if (nameFilter) {
                query = query.ilike('name', `%${nameFilter}%`)
            }

            const { data, error } = await query

            if (error) throw error

            // Client-side attribute filtering (supa JSONB filtering is tricky with raw text)
            let filteredData = data || []
            if (attrFilter) {
                const lowerFilter = attrFilter.toLowerCase()
                filteredData = filteredData.filter(s =>
                    JSON.stringify(s.attributes).toLowerCase().includes(lowerFilter)
                )
            }

            setSpans(filteredData)
        } catch (error) {
            console.error('Error fetching spans:', error)
        } finally {
            setLoading(false)
        }
    }

    // Debounce helper for filters
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchSpans()
        }, 500)
        return () => clearTimeout(timer)
    }, [nameFilter, attrFilter])

    const getDurationColor = (ms: number | null) => {
        if (!ms) return 'text-gray-400'
        if (ms < 500) return 'text-green-600'
        if (ms < 2000) return 'text-yellow-600'
        return 'text-red-600'
    }



    return (
        <div className="h-[calc(100vh-100px)] flex flex-col">
            {/* Header & Controls */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Activity className="text-blue-500" />
                    Telemetry Explorer
                </h1>
                <p className="text-gray-500 text-sm mt-1">Deep dive into individual operations, vector chunks, and raw spans.</p>

                <div className="mt-4 bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-wrap gap-4 items-center">
                    <div className="flex-1 min-w-[200px] relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            placeholder="Filter by Span Name (e.g. VectorSearch)..."
                            className="w-full pl-9 pr-4 py-2 border rounded-md text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                            value={nameFilter}
                            onChange={(e) => setNameFilter(e.target.value)}
                        />
                    </div>
                    <div className="flex-1 min-w-[200px] relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            placeholder="Search in Attributes (JSON)..."
                            className="w-full pl-9 pr-4 py-2 border rounded-md text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                            value={attrFilter}
                            onChange={(e) => setAttrFilter(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-3 border-l pl-4 ml-2">
                        <button
                            onClick={() => setLiveMode(!liveMode)}
                            className={`px-3 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors ${liveMode
                                    ? 'bg-green-100 text-green-700 border border-green-200'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            <div className={`w-2 h-2 rounded-full ${liveMode ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                            {liveMode ? 'Live Mode ON' : 'Live Mode OFF'}
                        </button>

                        <select
                            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 outline-none"
                            value={limit}
                            onChange={(e) => setLimit(Number(e.target.value))}
                        >
                            <option value={50}>Last 50</option>
                            <option value={100}>Last 100</option>
                            <option value={500}>Last 500</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex gap-6 overflow-hidden">

                {/* Table View */}
                <div className={`flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col ${selectedSpan ? 'w-2/3' : 'w-full'}`}>
                    <div className="overflow-auto flex-1">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50 sticky top-0 z-10">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Operation</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider / Info</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200 text-sm">
                                {loading && (
                                    <tr><td colSpan={5} className="p-8 text-center text-gray-500">Loading spans...</td></tr>
                                )}
                                {!loading && spans.length === 0 && (
                                    <tr><td colSpan={5} className="p-8 text-center text-gray-500">No spans found matching criteria.</td></tr>
                                )}
                                {spans.map(span => (
                                    <tr
                                        key={span.id}
                                        onClick={() => setSelectedSpan(span)}
                                        className={`cursor-pointer transition-colors ${selectedSpan?.id === span.id ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                                    >
                                        <td className="px-4 py-3 whitespace-nowrap text-gray-500 text-xs">
                                            {new Date(span.start_time).toLocaleTimeString()}
                                        </td>
                                        <td className="px-4 py-3 font-medium text-gray-900">
                                            {span.name}
                                        </td>
                                        <td className={`px-4 py-3 whitespace-nowrap font-mono ${getDurationColor(span.duration_ms)}`}>
                                            {span.duration_ms ? `${span.duration_ms}ms` : '-'}
                                        </td>
                                        <td className="px-4 py-3 text-gray-600 max-w-xs truncate">
                                            {/* Smart Column: Show relevant info based on span type */}
                                            {span.attributes['llm.provider'] && (
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 mr-2">
                                                    {span.attributes['llm.provider']}
                                                </span>
                                            )}
                                            {span.attributes['vector_db.provider'] && (
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800 mr-2">
                                                    <Database size={10} className="mr-1" /> {span.attributes['vector_db.provider']}
                                                </span>
                                            )}
                                            {span.attributes['llm.model']}
                                        </td>
                                        <td className="px-4 py-3 whitespace-nowrap">
                                            <span className={`px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${span.status === 'ERROR' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                                                }`}>
                                                {span.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 text-xs text-gray-500 flex justify-between">
                        <span>Showing {spans.length} spans</span>
                        <span>Live Query from Supabase</span>
                    </div>
                </div>

                {/* Inspector Panel */}
                {selectedSpan && (
                    <div className="w-1/3 min-w-[400px] bg-white rounded-lg shadow border border-gray-200 flex flex-col overflow-hidden animate-in slide-in-from-right-10 duration-200">
                        <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                            <h3 className="font-semibold text-gray-800">Span Details</h3>
                            <button
                                onClick={() => setSelectedSpan(null)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="p-4 overflow-auto flex-1 space-y-6">

                            {/* High Level Stats */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-50 p-3 rounded border border-gray-100">
                                    <div className="text-xs text-gray-500 uppercase">Duration</div>
                                    <div className={`text-xl font-bold ${getDurationColor(selectedSpan.duration_ms)}`}>
                                        {selectedSpan.duration_ms}ms
                                    </div>
                                </div>
                                <div className="bg-gray-50 p-3 rounded border border-gray-100">
                                    <div className="text-xs text-gray-500 uppercase">Tokens</div>
                                    <div className="text-xl font-bold text-gray-800">
                                        {selectedSpan.attributes['llm.usage.total_tokens'] || selectedSpan.attributes['tokens.total'] || '-'}
                                    </div>
                                </div>
                            </div>

                            {/* Vector / Retrieval Specifics (The "Killer Feature") */}
                            {(selectedSpan.attributes['vector_db.retrieved_chunks'] || selectedSpan.attributes['memory.retrieved_chunks']) && (
                                <div className="border border-blue-200 bg-blue-50 rounded-lg p-3">
                                    <h4 className="text-sm font-bold text-blue-800 mb-2 flex items-center gap-2">
                                        <Brain size={14} /> Retrieved Content
                                    </h4>
                                    <div className="bg-white border border-blue-100 rounded p-2 text-xs font-mono text-gray-700 max-h-60 overflow-auto whitespace-pre-wrap">
                                        {selectedSpan.attributes['vector_db.retrieved_chunks'] || selectedSpan.attributes['memory.retrieved_chunks']}
                                    </div>
                                </div>
                            )}

                            {/* All Attributes Raw JSON */}
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Full Attributes</h4>
                                <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg text-xs overflow-auto font-mono">
                                    {JSON.stringify(selectedSpan.attributes, null, 2)}
                                </pre>
                            </div>

                            {/* Events */}
                            {selectedSpan.events && selectedSpan.events.length > 0 && (
                                <div>
                                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Events</h4>
                                    <div className="space-y-2">
                                        {selectedSpan.events.map((e, i) => (
                                            <div key={i} className="text-xs border-l-2 border-blue-300 pl-2">
                                                <span className="font-semibold">{e.name}</span> <span className="text-gray-500">{new Date(e.timestamp).toLocaleTimeString()}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                        </div>
                    </div>
                )}

            </div>
        </div>
    )
}
