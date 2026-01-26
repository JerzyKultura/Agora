/**
 * Statistical utilities for anomaly detection
 */

export interface ExecutionStats {
    avgDuration: number
    stdDevDuration: number
    avgTokens: number
    stdDevTokens: number
    avgCost: number
    stdDevCost: number
    errorRate: number
    totalExecutions: number
}

export interface Anomaly {
    type: 'slow' | 'expensive' | 'error' | 'high_tokens'
    severity: 'warning' | 'error'
    message: string
    icon: string
    multiplier?: number
}

/**
 * Calculate mean of an array of numbers
 */
export function mean(values: number[]): number {
    if (values.length === 0) return 0
    return values.reduce((sum, val) => sum + val, 0) / values.length
}

/**
 * Calculate standard deviation
 */
export function standardDeviation(values: number[]): number {
    if (values.length === 0) return 0
    const avg = mean(values)
    const squareDiffs = values.map(value => Math.pow(value - avg, 2))
    return Math.sqrt(mean(squareDiffs))
}

/**
 * Calculate statistics for a set of executions
 */
export function calculateStats(executions: any[]): ExecutionStats {
    if (executions.length === 0) {
        return {
            avgDuration: 0,
            stdDevDuration: 0,
            avgTokens: 0,
            stdDevTokens: 0,
            avgCost: 0,
            stdDevCost: 0,
            errorRate: 0,
            totalExecutions: 0
        }
    }

    const durations = executions.map(e => {
        if (e.end_time && e.start_time) {
            const start = new Date(e.start_time).getTime()
            const end = new Date(e.end_time).getTime()
            return (end - start) / 1000 // Convert to seconds
        }
        return e.duration_ms ? e.duration_ms / 1000 : 0
    }).filter(d => d > 0)

    const tokens = executions.map(e => e.tokens_used || 0).filter(t => t > 0)
    const costs = executions.map(e => e.estimated_cost || 0).filter(c => c > 0)
    const errors = executions.filter(e => e.status === 'error' || e.status === 'failed')

    return {
        avgDuration: mean(durations),
        stdDevDuration: standardDeviation(durations),
        avgTokens: mean(tokens),
        stdDevTokens: standardDeviation(tokens),
        avgCost: mean(costs),
        stdDevCost: standardDeviation(costs),
        errorRate: errors.length / executions.length,
        totalExecutions: executions.length
    }
}

/**
 * Detect anomalies in an execution
 */
export function detectAnomalies(execution: any, stats: ExecutionStats): Anomaly[] {
    const anomalies: Anomaly[] = []

    // Calculate execution duration
    let duration = 0
    if (execution.end_time && execution.start_time) {
        const start = new Date(execution.start_time).getTime()
        const end = new Date(execution.end_time).getTime()
        duration = (end - start) / 1000
    } else if (execution.duration_ms) {
        duration = execution.duration_ms / 1000
    }

    // Slow execution (2 standard deviations above mean)
    if (duration > 0 && stats.avgDuration > 0) {
        const threshold = stats.avgDuration + (2 * stats.stdDevDuration)
        if (duration > threshold) {
            const multiplier = duration / stats.avgDuration
            anomalies.push({
                type: 'slow',
                severity: 'warning',
                message: `${multiplier.toFixed(1)}x slower`,
                icon: '⚠️',
                multiplier
            })
        }
    }

    // High token usage
    const tokens = execution.tokens_used || 0
    if (tokens > 0 && stats.avgTokens > 0) {
        const threshold = stats.avgTokens + (2 * stats.stdDevTokens)
        if (tokens > threshold) {
            const multiplier = tokens / stats.avgTokens
            anomalies.push({
                type: 'high_tokens',
                severity: 'warning',
                message: `${multiplier.toFixed(1)}x more tokens`,
                icon: '💰',
                multiplier
            })
        }
    }

    // High cost
    const cost = execution.estimated_cost || 0
    if (cost > 0 && stats.avgCost > 0) {
        const threshold = stats.avgCost + (2 * stats.stdDevCost)
        if (cost > threshold) {
            const multiplier = cost / stats.avgCost
            anomalies.push({
                type: 'expensive',
                severity: 'warning',
                message: `${multiplier.toFixed(1)}x more expensive`,
                icon: '💸',
                multiplier
            })
        }
    }

    // Error status
    if (execution.status === 'error' || execution.status === 'failed') {
        anomalies.push({
            type: 'error',
            severity: 'error',
            message: 'Execution failed',
            icon: '🔴'
        })
    }

    return anomalies
}
