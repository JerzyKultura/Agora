import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { Search, Filter, TrendingUp } from 'lucide-react'

interface PathPattern {
    path: string[]
    count: number
    percentage: number
}

export default function TelemetryExplorer() {
    const [workflowFilter, setWorkflowFilter] = useState('')
    const [executions, setExecutions] = useState<any[]>([])
    const [pathPatterns, setPathPatterns] = useState<PathPattern[]>([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        loadExecutions()
    }, [workflowFilter])

    const loadExecutions = async () => {
        setLoading(true)
        try {
            let query = supabase
                .from('telemetry_spans')
                .select('*')
                .not('execution_id', 'is', null)
                .order('start_time', { ascending: false })
                .limit(500)

            if (workflowFilter) {
                query = query.ilike('name', `%${workflowFilter}%`)
            }

            const { data, error } = await query

            if (error) throw error

            // Group by execution_id
            const execMap = new Map<string, any[]>()
            data?.forEach(span => {
                const execId = span.execution_id
                if (!execMap.has(execId)) {
                    execMap.set(execId, [])
                }
                execMap.get(execId)!.push(span)
            })

            // Extract paths
            const paths: string[][] = []
            execMap.forEach(spans => {
                const sorted = spans.sort((a, b) =>
                    new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
                )
                paths.push(sorted.map(s => s.name))
            })

            // Count path patterns
            const pathCounts = new Map<string, number>()
            paths.forEach(path => {
                const key = path.join(' → ')
                pathCounts.set(key, (pathCounts.get(key) || 0) + 1)
            })

            // Convert to array and calculate percentages
            const patterns: PathPattern[] = Array.from(pathCounts.entries())
                .map(([pathStr, count]) => ({
                    path: pathStr.split(' → '),
                    count,
                    percentage: (count / paths.length) * 100
                }))
                .sort((a, b) => b.count - a.count)

            setExecutions(Array.from(execMap.values()))
            setPathPatterns(patterns)
        } catch (error) {
            console.error('Failed to load executions:', error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Telemetry Explorer</h1>
                    <p className="text-gray-600">Query and analyze workflow execution patterns</p>
                </div>

                {/* Search & Filters */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                    <div className="flex gap-4">
                        <div className="flex-1">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                <input
                                    type="text"
                                    placeholder="Search by workflow name..."
                                    value={workflowFilter}
                                    onChange={(e) => setWorkflowFilter(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                        <button
                            onClick={loadExecutions}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                        >
                            <Filter className="w-4 h-4" />
                            Apply
                        </button>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                        <div className="text-sm text-gray-600 mb-1">Total Executions</div>
                        <div className="text-2xl font-bold text-gray-900">{executions.length}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                        <div className="text-sm text-gray-600 mb-1">Unique Paths</div>
                        <div className="text-2xl font-bold text-gray-900">{pathPatterns.length}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                        <div className="text-sm text-gray-600 mb-1">Most Common</div>
                        <div className="text-sm font-medium text-gray-900">
                            {pathPatterns[0] ? `${pathPatterns[0].percentage.toFixed(1)}%` : '-'}
                        </div>
                    </div>
                </div>

                {/* Path Patterns */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <div className="flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-blue-600" />
                            <h2 className="text-lg font-semibold text-gray-900">Path Patterns</h2>
                        </div>
                    </div>

                    {loading ? (
                        <div className="p-8 text-center text-gray-500">Loading...</div>
                    ) : pathPatterns.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">No patterns found</div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {pathPatterns.slice(0, 20).map((pattern, idx) => (
                                <div key={idx} className="px-6 py-4 hover:bg-gray-50">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-3">
                                            <span className="text-sm font-semibold text-gray-500">#{idx + 1}</span>
                                            <div>
                                                <div className="text-sm font-medium text-gray-900 mb-1">
                                                    {pattern.count}x executions ({pattern.percentage.toFixed(1)}%)
                                                </div>
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    {pattern.path.map((node, nodeIdx) => (
                                                        <div key={nodeIdx} className="flex items-center gap-2">
                                                            <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono">
                                                                {node}
                                                            </span>
                                                            {nodeIdx < pattern.path.length - 1 && (
                                                                <span className="text-gray-400">→</span>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    {/* Progress bar */}
                                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full transition-all"
                                            style={{ width: `${pattern.percentage}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
