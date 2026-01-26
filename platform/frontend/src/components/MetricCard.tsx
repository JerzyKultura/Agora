interface MetricCardProps {
    title: string
    value: string | number
    icon?: string
    trend?: 'up' | 'down' | 'neutral'
    severity?: 'normal' | 'warning' | 'error'
}

export default function MetricCard({ title, value, icon, trend, severity = 'normal' }: MetricCardProps) {
    const severityColors = {
        normal: 'bg-white border-gray-200',
        warning: 'bg-yellow-50 border-yellow-200',
        error: 'bg-red-50 border-red-200'
    }

    const trendIcons = {
        up: '↗️',
        down: '↘️',
        neutral: '→'
    }

    return (
        <div className={`p-4 rounded-lg border ${severityColors[severity]}`}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">{title}</span>
                {icon && <span className="text-2xl">{icon}</span>}
            </div>
            <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-gray-900">{value}</span>
                {trend && (
                    <span className="text-sm text-gray-500">{trendIcons[trend]}</span>
                )}
            </div>
        </div>
    )
}
