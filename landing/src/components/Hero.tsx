export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 py-24 flex flex-col lg:flex-row items-center gap-16">
        {/* Left: Text content */}
        <div className="flex-1 text-center lg:text-left">
          <div className="inline-block px-4 py-1.5 rounded-full glass text-xs font-medium text-neon-blue tracking-wide uppercase mb-6">
            Open Source Framework
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight">
            <span className="text-white">Workflow Orchestration</span>
            <br />
            <span className="gradient-text">with Built-in Observability</span>
          </h1>

          <p className="mt-6 text-lg text-gray-400 leading-relaxed max-w-xl mx-auto lg:mx-0">
            Build node-based workflows with three-phase execution, conditional routing,
            and automatic telemetry. Agora adds audit logging, OpenTelemetry tracing,
            and a cloud monitoring platform to your pipelines.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
            <a
              href="#quickstart"
              className="px-8 py-3.5 rounded-xl text-base font-semibold bg-gradient-to-r from-neon-blue to-neon-violet text-white hover:shadow-xl hover:shadow-neon-blue/25 transition-all duration-300 text-center"
            >
              Quick Start
            </a>
            <a
              href="#beta"
              className="px-8 py-3.5 rounded-xl text-base font-semibold glass neon-border text-white hover:bg-white/5 transition-all duration-300 text-center"
            >
              Join the Beta
            </a>
          </div>
        </div>

        {/* Right: Animated node-flow diagram */}
        <div className="flex-1 flex justify-center">
          <div className="relative w-[380px] h-[380px] sm:w-[440px] sm:h-[440px]">
            <FlowDiagram />
          </div>
        </div>
      </div>

      {/* Bottom fade gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-dark-900 to-transparent" />
    </section>
  )
}

function FlowDiagram() {
  const nodes = [
    { id: 'start', label: 'Start', x: 190, y: 30, color: '#00D4FF' },
    { id: 'prep', label: 'prep()', x: 80, y: 140, color: '#7B61FF' },
    { id: 'exec', label: 'exec()', x: 300, y: 140, color: '#7B61FF' },
    { id: 'post', label: 'post()', x: 190, y: 250, color: '#7B61FF' },
    { id: 'telemetry', label: 'Telemetry', x: 330, y: 310, color: '#00FFE0' },
    { id: 'next', label: 'Next Node', x: 60, y: 340, color: '#00D4FF' },
  ]

  const edges: [number, number][] = [
    [0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [3, 5],
  ]

  return (
    <svg viewBox="0 0 400 400" className="w-full h-full">
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00D4FF" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#7B61FF" stopOpacity="0.6" />
        </linearGradient>
      </defs>

      {/* Edges */}
      {edges.map(([from, to], i) => (
        <line
          key={i}
          x1={nodes[from].x}
          y1={nodes[from].y + 20}
          x2={nodes[to].x}
          y2={nodes[to].y - 10}
          stroke="url(#edgeGrad)"
          strokeWidth="2"
          className="edge-flow"
        />
      ))}

      {/* Nodes */}
      {nodes.map((node) => (
        <g key={node.id}>
          {/* Glow circle */}
          <circle
            cx={node.x}
            cy={node.y}
            r="32"
            fill={node.color}
            opacity="0.08"
            filter="url(#glow)"
          />
          {/* Node circle */}
          <circle
            cx={node.x}
            cy={node.y}
            r="24"
            fill="rgba(10, 10, 15, 0.8)"
            stroke={node.color}
            strokeWidth="1.5"
            className="pulse-glow"
            style={{ animationDelay: `${Math.random() * 3}s` }}
          />
          {/* Label */}
          <text
            x={node.x}
            y={node.y + 1}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={node.color}
            fontSize="10"
            fontFamily="'JetBrains Mono', monospace"
            fontWeight="500"
          >
            {node.label}
          </text>
        </g>
      ))}
    </svg>
  )
}
