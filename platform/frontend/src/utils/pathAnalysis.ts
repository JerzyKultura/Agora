/**
 * Path analysis utilities for detecting workflow path anomalies
 */

export interface PathAnomaly {
    type: 'unexpected_path' | 'skipped_node' | 'extra_node'
    actualPath: string[]
    expectedPaths: string[][]
    message: string
    severity: 'warning' | 'error'
}

export interface PathAlarm {
    id: string
    workflow: string
    expectedPaths: string[][]
    severity: 'warning' | 'error'
    enabled: boolean
    description?: string
}

/**
 * Extract node path from telemetry spans
 */
export function extractNodePath(spans: any[]): string[] {
    return spans
        .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
        .map(span => span.name)
}

/**
 * Check if actual path matches any expected path
 */
export function pathMatches(actualPath: string[], expectedPaths: string[][]): boolean {
    return expectedPaths.some(expected =>
        JSON.stringify(actualPath) === JSON.stringify(expected)
    )
}

/**
 * Detect if a path is anomalous
 */
export function detectPathAnomaly(
    actualPath: string[],
    alarm: PathAlarm
): PathAnomaly | null {
    if (!alarm.enabled) return null

    if (pathMatches(actualPath, alarm.expectedPaths)) {
        return null
    }

    // Find closest matching path
    const closestPath = findClosestPath(actualPath, alarm.expectedPaths)
    const diff = findPathDifference(actualPath, closestPath)

    return {
        type: diff.type,
        actualPath,
        expectedPaths: alarm.expectedPaths,
        message: diff.message,
        severity: alarm.severity
    }
}

/**
 * Find the closest matching expected path
 */
function findClosestPath(actualPath: string[], expectedPaths: string[][]): string[] {
    let closest = expectedPaths[0] || []
    let minDiff = Infinity

    for (const expected of expectedPaths) {
        const diff = levenshteinDistance(actualPath, expected)
        if (diff < minDiff) {
            minDiff = diff
            closest = expected
        }
    }

    return closest
}

/**
 * Calculate Levenshtein distance between two paths
 */
function levenshteinDistance(path1: string[], path2: string[]): number {
    const m = path1.length
    const n = path2.length
    const dp: number[][] = Array(m + 1).fill(0).map(() => Array(n + 1).fill(0))

    for (let i = 0; i <= m; i++) dp[i][0] = i
    for (let j = 0; j <= n; j++) dp[0][j] = j

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (path1[i - 1] === path2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1]
            } else {
                dp[i][j] = Math.min(
                    dp[i - 1][j] + 1,    // deletion
                    dp[i][j - 1] + 1,    // insertion
                    dp[i - 1][j - 1] + 1 // substitution
                )
            }
        }
    }

    return dp[m][n]
}

/**
 * Find specific difference between actual and expected path
 */
function findPathDifference(actualPath: string[], expectedPath: string[]): {
    type: PathAnomaly['type']
    message: string
} {
    // Check for skipped nodes
    const skipped = expectedPath.filter(node => !actualPath.includes(node))
    if (skipped.length > 0) {
        return {
            type: 'skipped_node',
            message: `Skipped: ${skipped.join(', ')}`
        }
    }

    // Check for extra nodes
    const extra = actualPath.filter(node => !expectedPath.includes(node))
    if (extra.length > 0) {
        return {
            type: 'extra_node',
            message: `Extra: ${extra.join(', ')}`
        }
    }

    // Different order or completely different path
    return {
        type: 'unexpected_path',
        message: `Path: ${actualPath.join(' → ')}`
    }
}

/**
 * Get common paths from execution history
 */
export function analyzeCommonPaths(executions: any[]): Map<string, number> {
    const pathCounts = new Map<string, number>()

    for (const exec of executions) {
        if (!exec.spans || exec.spans.length === 0) continue

        const path = extractNodePath(exec.spans)
        const pathKey = path.join(' → ')

        pathCounts.set(pathKey, (pathCounts.get(pathKey) || 0) + 1)
    }

    return pathCounts
}

/**
 * Suggest expected paths based on execution history
 */
export function suggestExpectedPaths(executions: any[], minFrequency: number = 0.1): string[][] {
    const pathCounts = analyzeCommonPaths(executions)
    const totalExecutions = executions.length
    const threshold = totalExecutions * minFrequency

    const commonPaths: string[][] = []

    for (const [pathStr, count] of pathCounts.entries()) {
        if (count >= threshold) {
            commonPaths.push(pathStr.split(' → '))
        }
    }

    return commonPaths
}
