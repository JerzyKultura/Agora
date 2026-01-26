import type { Anomaly } from '../utils/anomalyDetection'

interface AnomalyBadgeProps {
    anomaly: Anomaly
}

export default function AnomalyBadge({ anomaly }: AnomalyBadgeProps) {
    const severityColors = {
        warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
        error: 'bg-red-100 text-red-700 border-red-200'
    }

    return (
        <span
            className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${severityColors[anomaly.severity]}`}
            title={`${anomaly.type}: ${anomaly.message}`}
        >
            <span>{anomaly.icon}</span>
            <span>{anomaly.message}</span>
        </span>
    )
}
