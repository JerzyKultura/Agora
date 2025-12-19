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

export default function CostDashboard() {
    const [metrics, setMetrics] = useState<CostMetric[]>([])
    const [loading, setLoading] = useState(true)
    const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('7d')

    useEffect(() => {
        loadCostMetrics()
    }, [timeRange])

    const loadCostMetrics = async () => {
        setLoading(true)
        try {
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
                        .select('tokens_used, estimated_cost')
                        .eq('workflow_id', workflow.id)
                        .not('tokens_used', 'is', null)

                    if (execs) {
                        execs.forEach(e => {
                            totalTokens += e.tokens_used || 0
                            totalCost += e.estimated_cost || 0
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

    const totalGlobalCost = metrics.reduce((acc, m) => acc + m.total_cost, 0)
    const totalGlobalTokens = metrics.reduce((acc, m) => acc + m.total_tokens, 0)

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-900">Cost & Usage</h1>
                <select
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value as any)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="24h">Last 24 Hours</option>
                    <option value="7d">Last 7 Days</option>
                    <option value="30d">Last 30 Days</option>
                </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
                    <div className="text-sm font-medium text-gray-500 uppercase">Total Spending (Estimated)</div>
                    <div className="mt-2 text-3xl font-bold text-gray-900">${totalGlobalCost.toFixed(4)}</div>
                    <div className="mt-1 text-sm text-gray-400">Across all projects</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
                    <div className="text-sm font-medium text-gray-500 uppercase">Total Tokens Used</div>
                    <div className="mt-2 text-3xl font-bold text-gray-900">{totalGlobalTokens.toLocaleString()}</div>
                    <div className="mt-1 text-sm text-gray-400">Aggregated LLM calls</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
                    <div className="text-sm font-medium text-gray-500 uppercase">Avg Cost Per Execution</div>
                    <div className="mt-2 text-3xl font-bold text-gray-900">
                        ${metrics.reduce((acc, m) => acc + m.execution_count, 0) > 0
                            ? (totalGlobalCost / metrics.reduce((acc, m) => acc + m.execution_count, 0)).toFixed(4)
                            : '0.0000'}
                    </div>
                    <div className="mt-1 text-sm text-gray-400">Unit efficiency</div>
                </div>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                    <h3 className="font-semibold text-gray-700">Usage by Project</h3>
                </div>
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading usage data...</div>
                ) : (
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Executions</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estimated Cost</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Share</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {metrics.map((metric) => (
                                <tr key={metric.project_id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">{metric.project_name}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {metric.execution_count}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {metric.total_tokens.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                                        ${metric.total_cost.toFixed(4)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div
                                                className="bg-blue-600 h-2 rounded-full"
                                                style={{ width: `${totalGlobalCost > 0 ? (metric.total_cost / totalGlobalCost) * 100 : 0}%` }}
                                            ></div>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
