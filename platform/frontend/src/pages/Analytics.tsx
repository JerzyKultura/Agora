import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts'
import { TrendingUp, Clock, DollarSign, Zap, Calendar } from 'lucide-react'

interface Execution {
    id: string
    workflow_id: string
    status: string
    started_at: string
    duration_ms: number | null
    tokens_used: number | null
    estimated_cost: number | null
}

interface Workflow {
    id: string
    name: string
}

export default function Analytics() {
    const { projectId } = useParams()
    const [executions, setExecutions] = useState<Execution[]>([])
    const [workflows, setWorkflows] = useState<Map<string, Workflow>>(new Map())
    const [loading, setLoading] = useState(true)
    const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('30d')
    const [selectedWorkflow, setSelectedWorkflow] = useState<string>('all')

    useEffect(() => {
        loadAnalyticsData()
    }, [projectId, dateRange])

    const loadAnalyticsData = async () => {
        setLoading(true)
        try {
            let allExecutions: Execution[] = []
            const workflowMap = new Map<string, Workflow>()

            if (projectId) {
                // Project-specific analytics
                const workflowsData = await api.workflows.list(projectId)
                workflowsData.forEach((w: Workflow) => workflowMap.set(w.id, w))

                for (const workflow of workflowsData) {
                    const execs = await api.executions.list({ workflow_id: workflow.id })
                    allExecutions.push(...execs)
                }
            } else {
                // Global analytics
                const projectsData = await api.projects.list()
                for (const project of projectsData) {
                    const workflowsData = await api.workflows.list(project.id)
                    workflowsData.forEach((w: Workflow) => workflowMap.set(w.id, w))

                    for (const workflow of workflowsData) {
                        const execs = await api.executions.list({ workflow_id: workflow.id })
                        allExecutions.push(...execs)
                    }
                }
            }

            // Filter by date range
            const cutoffDate = new Date()
            cutoffDate.setDate(cutoffDate.getDate() - parseInt(dateRange))
            allExecutions = allExecutions.filter(
                (e) => new Date(e.started_at) >= cutoffDate
            )

            setWorkflows(workflowMap)
            setExecutions(allExecutions)
        } catch (error) {
            console.error('Failed to load analytics:', error)
        } finally {
            setLoading(false)
        }
    }

    // Filter executions by selected workflow
    const filteredExecutions = selectedWorkflow === 'all'
        ? executions
        : executions.filter((e) => e.workflow_id === selectedWorkflow)

    // Calculate metrics
    const totalExecutions = filteredExecutions.length
    const successfulExecutions = filteredExecutions.filter((e) => e.status === 'success').length
    const successRate = totalExecutions > 0 ? (successfulExecutions / totalExecutions) * 100 : 0
    const avgDuration = filteredExecutions.reduce((acc, e) => acc + (e.duration_ms || 0), 0) / (totalExecutions || 1)
    const totalCost = filteredExecutions.reduce((acc, e) => acc + (e.estimated_cost || 0), 0)
    const totalTokens = filteredExecutions.reduce((acc, e) => acc + (e.tokens_used || 0), 0)

    // Prepare chart data
    const statusData = [
        { name: 'Success', value: filteredExecutions.filter((e) => e.status === 'success').length, color: '#10b981' },
        { name: 'Error', value: filteredExecutions.filter((e) => e.status === 'error').length, color: '#ef4444' },
        { name: 'Running', value: filteredExecutions.filter((e) => e.status === 'running').length, color: '#3b82f6' },
        { name: 'Timeout', value: filteredExecutions.filter((e) => e.status === 'timeout').length, color: '#f59e0b' }
    ].filter((d) => d.value > 0)

    // Time series data (executions per day)
    const timeSeriesData = (() => {
        const days = parseInt(dateRange)
        const data: { date: string; executions: number; success: number; errors: number }[] = []

        for (let i = days - 1; i >= 0; i--) {
            const date = new Date()
            date.setDate(date.getDate() - i)
            const dateStr = date.toISOString().split('T')[0]

            const dayExecutions = filteredExecutions.filter((e) => {
                const execDate = new Date(e.started_at).toISOString().split('T')[0]
                return execDate === dateStr
            })

            data.push({
                date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                executions: dayExecutions.length,
                success: dayExecutions.filter((e) => e.status === 'success').length,
                errors: dayExecutions.filter((e) => e.status === 'error').length
            })
        }

        return data
    })()

    // Duration distribution
    const durationData = (() => {
        const buckets = [
            { range: '0-1s', min: 0, max: 1000, count: 0 },
            { range: '1-5s', min: 1000, max: 5000, count: 0 },
            { range: '5-10s', min: 5000, max: 10000, count: 0 },
            { range: '10-30s', min: 10000, max: 30000, count: 0 },
            { range: '30s+', min: 30000, max: Infinity, count: 0 }
        ]

        filteredExecutions.forEach((e) => {
            if (e.duration_ms) {
                const bucket = buckets.find((b) => e.duration_ms! >= b.min && e.duration_ms! < b.max)
                if (bucket) bucket.count++
            }
        })

        return buckets.filter((b) => b.count > 0)
    })()

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        )
    }

    return (
        <div>
            <div className="mb-6 flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
                <div className="flex gap-4">
                    <select
                        value={selectedWorkflow}
                        onChange={(e) => setSelectedWorkflow(e.target.value)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Workflows</option>
                        {Array.from(workflows.values()).map((w) => (
                            <option key={w.id} value={w.id}>
                                {w.name}
                            </option>
                        ))}
                    </select>
                    <select
                        value={dateRange}
                        onChange={(e) => setDateRange(e.target.value as '7d' | '30d' | '90d')}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="90d">Last 90 Days</option>
                    </select>
                </div>
            </div>

            {/* Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Total Executions</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{totalExecutions}</p>
                        </div>
                        <div className="bg-blue-100 p-3 rounded-full">
                            <Zap className="w-6 h-6 text-blue-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Success Rate</p>
                            <p className="text-3xl font-bold text-green-600 mt-1">{successRate.toFixed(1)}%</p>
                        </div>
                        <div className="bg-green-100 p-3 rounded-full">
                            <TrendingUp className="w-6 h-6 text-green-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Avg Duration</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">
                                {avgDuration < 1000 ? `${avgDuration.toFixed(0)}ms` : `${(avgDuration / 1000).toFixed(2)}s`}
                            </p>
                        </div>
                        <div className="bg-purple-100 p-3 rounded-full">
                            <Clock className="w-6 h-6 text-purple-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Total Cost</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">
                                ${totalCost.toFixed(4)}
                            </p>
                            {totalTokens > 0 && (
                                <p className="text-xs text-gray-400 mt-1">{totalTokens.toLocaleString()} tokens</p>
                            )}
                        </div>
                        <div className="bg-yellow-100 p-3 rounded-full">
                            <DollarSign className="w-6 h-6 text-yellow-600" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Executions Over Time */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-gray-600" />
                        Executions Over Time
                    </h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={timeSeriesData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" style={{ fontSize: '12px' }} />
                            <YAxis style={{ fontSize: '12px' }} />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="executions" stroke="#3b82f6" strokeWidth={2} name="Total" />
                            <Line type="monotone" dataKey="success" stroke="#10b981" strokeWidth={2} name="Success" />
                            <Line type="monotone" dataKey="errors" stroke="#ef4444" strokeWidth={2} name="Errors" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Status Distribution */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold mb-4">Status Distribution</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={statusData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {statusData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Duration Distribution */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Duration Distribution</h2>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={durationData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="range" style={{ fontSize: '12px' }} />
                        <YAxis style={{ fontSize: '12px' }} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="count" fill="#8b5cf6" name="Executions" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Empty State */}
            {totalExecutions === 0 && (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                    <div className="text-6xl mb-4">📊</div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-2">No Analytics Data</h3>
                    <p className="text-gray-600">
                        Run some workflows to see analytics and insights here.
                    </p>
                </div>
            )}
        </div>
    )
}
