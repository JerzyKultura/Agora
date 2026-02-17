const features = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-7 h-7">
        <circle cx="12" cy="5" r="2.5" />
        <circle cx="5" cy="19" r="2.5" />
        <circle cx="19" cy="19" r="2.5" />
        <path d="M12 7.5V12M12 12L6.5 16.5M12 12L17.5 16.5" />
      </svg>
    ),
    title: 'Node-Based Workflows',
    description:
      'Three-phase execution model — prep(), exec(), post() — gives you clean separation of data fetching, processing, and state management.',
    accent: 'text-neon-blue',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-7 h-7">
        <path d="M4 12h4l3-9 3 18 3-9h4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: 'Conditional Routing',
    description:
      'Dynamic flow control with node - "action" >> next_node syntax. Route execution based on return values for complex branching logic.',
    accent: 'text-neon-violet',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-7 h-7">
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <path d="M8 8h8M8 12h6M8 16h4" strokeLinecap="round" />
      </svg>
    ),
    title: 'Audit Logging',
    description:
      'Structured JSON audit trails for every execution. Track node timings, shared state changes, routing decisions, and error details.',
    accent: 'text-neon-cyan',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-7 h-7">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 3" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="1.5" fill="currentColor" />
      </svg>
    ),
    title: 'OpenTelemetry',
    description:
      'Distributed tracing with automatic spans for every node phase. Export to Jaeger, Zipkin, or the Agora Cloud Platform.',
    accent: 'text-neon-blue',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-7 h-7">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: 'Async & Batch',
    description:
      'First-class async/await support with AsyncNode, BatchNode, and ParallelBatchNode for high-throughput parallel processing.',
    accent: 'text-neon-violet',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-7 h-7">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" strokeLinecap="round" />
        <circle cx="12" cy="10" r="3" />
      </svg>
    ),
    title: 'Cloud Platform',
    description:
      'Full-featured web UI for workflow monitoring, execution visualization, analytics dashboards, and team collaboration.',
    accent: 'text-neon-cyan',
  },
]

export default function Features() {
  return (
    <section id="features" className="relative py-32">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section header */}
        <div className="text-center mb-20 animate-on-scroll">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            Everything you need for{' '}
            <span className="gradient-text">production workflows</span>
          </h2>
          <p className="mt-4 text-gray-400 text-lg max-w-2xl mx-auto">
            From simple pipelines to complex AI agent orchestration, Agora provides the
            building blocks with observability built in from day one.
          </p>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <div
              key={feature.title}
              className={`glass neon-border rounded-2xl p-8 transition-all duration-300 hover:-translate-y-1 animate-on-scroll delay-${i + 1}`}
            >
              <div className={`${feature.accent} mb-4`}>{feature.icon}</div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
