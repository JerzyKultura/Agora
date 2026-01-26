import type { PathAnomaly } from '../utils/pathAnalysis'

interface PathAnomalyBadgeProps {
    anomaly: PathAnomaly
}

export default function PathAnomalyBadge({ anomaly }: PathAnomalyBadgeProps) {
    const severityColors = {
        warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
        error: 'bg-red-100 text-red-700 border-red-200'
    }

    const typeIcons = {
        unexpected_path: '🚨',
        skipped_node: '⏭️',
        extra_node: '➕'
    }

    return (
        <span
            className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${severityColors[anomaly.severity]}`}
            title={`Path anomaly: ${anomaly.message}\nExpected: ${anomaly.expectedPaths[0]?.join(' → ')}`}
        >
            <span>{typeIcons[anomaly.type]}</span>
            <span>{anomaly.message}</span>
        </span>
    )
}
