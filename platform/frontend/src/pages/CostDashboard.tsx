import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { supabase } from '../lib/supabase'

interface CostMetric {
    project_id: string
    project_name: string
    total_tokens: number
    total_cost: number
    execution_count: number
}

interface ProviderMetric {
    provider: string
    model: string
    calls: number
    tokens: number
    cost: number
}

export default function CostDashboard() {
    const [metrics, setMetrics] = useState<CostMetric[]>([])
    const [providerMetrics, setProviderMetrics] = useState<ProviderMetric[]>([])
    const [loading, setLoading] = useState(true)
    const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('7d')
    const [selectedProvider, setSelectedProvider] = useState<string>('all')

    useEffect(() => {
        loadCostMetrics()
    }, [timeRange])

    const loadCostMetrics = async () => {
        setLoading(true)
        try {
            // Calculate date filter
            const now = new Date()
            const filterDate = new Date()
            if (timeRange === '24h') filterDate.setDate(now.getDate() - 1)
            if (timeRange === '7d') filterDate.setDate(now.getDate() - 7)
            if (timeRange === '30d') filterDate.setDate(now.getDate() - 30)

            // 1. Load Provider Metrics FIRST (source of truth for provider split)
            const { data: spans } = await supabase
                .from('telemetry_spans')
                .select('attributes, execution_id')
                .gte('start_time', filterDate.toISOString())
                .limit(2000)

            const pMap = new Map<string, ProviderMetric>()
            const executionProviderMap = new Map<string, string>() // Map execution_id -> provider

            if (spans) {
                spans.forEach(span => {
                    const attrs = span.attributes || {}
                    // Normalize provider name
                    let provider = attrs['llm.provider'] ||
                        (attrs['llm.model']?.startsWith('gpt') ? 'openai' : null) ||
                        (attrs['llm.model']?.startsWith('claude') ? 'anthropic' : null) ||
                        (attrs['llm.model']?.startsWith('grok') ? 'xai' : null) ||
                        'unknown'

                    // Simple normalization
                    provider = provider.toLowerCase()
                    if (provider.includes('openai')) provider = 'openai'
                    if (provider.includes('anthropic')) provider = 'anthropic'
                    if (provider.includes('xai') || provider.includes('grok')) provider = 'xai'

                    const model = attrs['llm.model'] || 'unknown'
                    const tokens = parseInt(attrs['tokens.total'] || attrs['llm.usage.total_tokens'] || '0')
                    const cost = parseFloat(attrs['estimated_cost'] || attrs['traceloop.cost.usd'] || '0')

                    if (tokens > 0 || cost > 0) {
                        const key = `${provider}:${model}`
                        if (!pMap.has(key)) {
                            pMap.set(key, { provider, model, calls: 0, tokens: 0, cost: 0 })
                        }
                        const m = pMap.get(key)!
                        m.calls++
                        m.tokens += tokens
                        m.cost += cost

                        // Track which execution used which provider (simplified: last provider wins for mixed execs)
                        if (span.execution_id) {
                            executionProviderMap.set(span.execution_id, provider)
                        }
                    }
                })
                setProviderMetrics(Array.from(pMap.values()).sort((a, b) => b.cost - a.cost))
            }

            // 2. Load Project Metrics (from executions)
            const projects = await api.projects.list()
            const metricData: CostMetric[] = []

            for (const project of projects) {
                const workflows = await api.workflows.list(project.id)
                let totalTokens = 0
                let totalCost = 0
                let executionCount = 0

                for (const workflow of workflows) {
                    const { data: execs } = await supabase
                        .from('executions')
                        .select('id, tokens_used, estimated_cost')
                        .eq('workflow_id', workflow.id)
                        .gte('started_at', filterDate.toISOString())

                    if (execs) {
                        execs.forEach(e => {
                            // Filter by provider if selected is NOT 'all'
                            // We use the map we built from spans to decide if we include this execution
                            // If we don't know the provider, we include it only if selectedProvider is 'all' or 'unknown'
                            const execProvider = executionProviderMap.get(e.id) || 'unknown'

                            if (typeof e.tokens_used === 'number') totalTokens += e.tokens_used
                            if (typeof e.estimated_cost === 'number') totalCost += e.estimated_cost
                            executionCount++
                        })
                    }
                }

                metricData.push({
                    project_id: project.id,
                    project_name: project.name,
                    total_tokens: totalTokens,
                    total_cost: totalCost,
                    execution_count: executionCount
                })
            }
            setMetrics(metricData)

        } catch (error) {
            console.error('Failed to load cost metrics:', error)
        } finally {
            setLoading(false)
        }
    }

    // Filter Logic
    const uniqueProviders = Array.from(new Set(providerMetrics.map(p => p.provider))).sort()

    // Filter the Provider Metrics Table
    const filteredProviderMetrics = selectedProvider === 'all'
        ? providerMetrics
        : providerMetrics.filter(p => p.provider === selectedProvider)

    // Calculate totals based on FILTERED provider metrics (more accurate than project metrics for this view)
    const totalGlobalCost = filteredProviderMetrics.reduce((acc, m) => acc + m.cost, 0)
    const totalGlobalTokens = filteredProviderMetrics.reduce((acc, m) => acc + m.tokens, 0)
    const totalCalls = filteredProviderMetrics.reduce((acc, m) => acc + m.calls, 0)

    const getColorForProvider = (provider: string) => {
        if (provider.includes('openai')) return 'bg-green-100 text-green-800'
        if (provider.includes('anthropic') || provider.includes('claude')) return 'bg-purple-100 text-purple-800'
        if (provider.includes('azure')) return 'bg-blue-100 text-blue-800'
        if (provider.includes('cohere')) return 'bg-yellow-100 text-yellow-800'
        if (provider.includes('xai') || provider.includes('grok')) return 'bg-gray-100 text-gray-800'
        return 'bg-gray-100 text-gray-800'
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Cost & Usage</h1>
                    <p className="text-gray-500 mt-1">Unified telemetry across all LLM providers</p>
                </div>

                <div className="flex gap-3">
                    {/* Provider Filter */}
                    <select
                        value={selectedProvider}
                        onChange={(e) => setSelectedProvider(e.target.value)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                        <option value="all">All Providers</option>
                        {uniqueProviders.map(p => (
                            <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                        ))}
                    </select>

                    {/* Time Filter */}
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value as any)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                    </select>
                </div>
            </div>

            {/* Top Cards - Dynamic based on filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500 transition-all">
                    <div className="text-sm font-medium text-gray-500 uppercase">Total Spending (Est.)</div>
                    <div className="mt-2 text-3xl font-bold text-gray-900">${totalGlobalCost.toFixed(4)}</div>
                    <div className="mt-1 text-sm text-gray-400">
                        {selectedProvider === 'all' ? 'Across all providers' : `For ${selectedProvider}`}
                    </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500 transition-all">
                    <div className="text-sm font-medium text-gray-500 uppercase">Total Tokens Used</div>
                    <div className="mt-2 text-3xl font-bold text-gray-900">{totalGlobalTokens.toLocaleString()}</div>
                    <div className="mt-1 text-sm text-gray-400">
                        {selectedProvider === 'all' ? 'Aggregated LLM calls' : `For ${selectedProvider}`}
                    </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500 transition-all">
                    <div className="text-sm font-medium text-gray-500 uppercase">Avg Cost / Call</div>
                    <div className="mt-2 text-3xl font-bold text-gray-900">
                        ${totalCalls > 0
                            ? (totalGlobalCost / totalCalls).toFixed(4)
                            : '0.0000'}
                    </div>
                    <div className="mt-1 text-sm text-gray-400">Unit efficiency</div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Provider Breakdown Table (Primary View for this) */}
                <div className="bg-white rounded-lg shadow overflow-hidden lg:col-span-2">
                    <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                        <h3 className="font-semibold text-gray-700">Usage by Model / Provider</h3>
                    </div>
                    {loading ? (
                        <div className="p-8 text-center text-gray-500">Loading provider data...</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Calls</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Estimated Cost</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">% of Total</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredProviderMetrics.map((pm, idx) => (
                                        <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-semibold rounded-full uppercase ${getColorForProvider(pm.provider)}`}>
                                                    {pm.provider}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{pm.model}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">{pm.calls}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">{pm.tokens.toLocaleString()}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 font-medium">${pm.cost.toFixed(4)}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
                                                {totalGlobalCost > 0 ? ((pm.cost / totalGlobalCost) * 100).toFixed(1) : '0.0'}%
                                            </td>
                                        </tr>
                                    ))}
                                    {filteredProviderMetrics.length === 0 && (
                                        <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500 text-sm">No data found for selected filters</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Disclaimer */}
            <div className="text-center text-xs text-gray-400 mt-8">
                Usage data is updated in real-time as workflows complete. Costs and token counts are normalized across all providers.
            </div>
        </div>
    )
}
