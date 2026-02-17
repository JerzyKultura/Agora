import { useState, useEffect, useRef, useCallback } from 'react'
import Prism from 'prismjs'
import 'prismjs/components/prism-python'

const tabs = [
  {
    label: 'Define Nodes',
    code: `from agora.agora_tracer import init_agora, agora_node

init_agora(app_name="my-app", enable_cloud_upload=True)

@agora_node(name="FetchData")
async def fetch_data(shared):
    shared["data"] = await get_from_api()
    return "process"

@agora_node(name="ProcessData")
async def process_data(shared):
    shared["result"] = transform(shared["data"])
    return "save"`,
  },
  {
    label: 'Build Flow',
    code: `from agora.agora_tracer import TracedAsyncFlow

flow = TracedAsyncFlow("DataPipeline")
flow.start(fetch_data)
fetch_data - "process" >> process_data
process_data - "save" >> save_result

await flow.run_async({"source": "api"})`,
  },
  {
    label: 'Run & Observe',
    code: `# Telemetry is captured automatically!
# View in console, export to JSON, or send to the cloud.

from agora.telemetry import AuditLogger

logger = AuditLogger("session-001")
# ... run your flow with AuditedNodes ...

logger.save_json("audit_trail.json")
# {
#   "session_id": "session-001",
#   "events": [...],
#   "total_duration_ms": 342
# }`,
  },
]

const terminalLines = [
  { text: '$ python pipeline.py', delay: 0, color: 'text-gray-400' },
  { text: '', delay: 300, color: '' },
  { text: '[Agora] Initializing telemetry...', delay: 600, color: 'text-neon-blue' },
  { text: '[Agora] Cloud upload: enabled', delay: 900, color: 'text-neon-cyan' },
  { text: '', delay: 1000, color: '' },
  { text: '▶ Flow "DataPipeline" started', delay: 1200, color: 'text-white' },
  { text: '  ├─ FetchData.prep()    12ms', delay: 1600, color: 'text-gray-400' },
  { text: '  ├─ FetchData.exec()    89ms', delay: 2000, color: 'text-gray-400' },
  { text: '  ├─ FetchData.post()  → "process"', delay: 2400, color: 'text-neon-violet' },
  { text: '  ├─ ProcessData.prep()   3ms', delay: 2800, color: 'text-gray-400' },
  { text: '  ├─ ProcessData.exec()  45ms', delay: 3200, color: 'text-gray-400' },
  { text: '  ├─ ProcessData.post() → "save"', delay: 3600, color: 'text-neon-violet' },
  { text: '  └─ SaveResult.exec()   18ms', delay: 4000, color: 'text-gray-400' },
  { text: '', delay: 4200, color: '' },
  { text: '✓ Flow completed in 342ms', delay: 4400, color: 'text-neon-cyan' },
  { text: '✓ Telemetry uploaded to Agora Cloud', delay: 4800, color: 'text-neon-blue' },
  { text: '✓ Audit trail saved: audit_trail.json', delay: 5200, color: 'text-neon-blue' },
]

export default function Demo() {
  const [activeTab, setActiveTab] = useState(0)
  const [visibleLines, setVisibleLines] = useState<number>(0)
  const [isRunning, setIsRunning] = useState(false)
  const codeRef = useRef<HTMLElement>(null)
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    if (codeRef.current) {
      Prism.highlightElement(codeRef.current)
    }
  }, [activeTab])

  const runDemo = useCallback(() => {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
    setVisibleLines(0)
    setIsRunning(true)

    terminalLines.forEach((line, i) => {
      const timer = setTimeout(() => {
        setVisibleLines(i + 1)
        if (i === terminalLines.length - 1) {
          setIsRunning(false)
        }
      }, line.delay)
      timersRef.current.push(timer)
    })
  }, [])

  useEffect(() => {
    return () => {
      timersRef.current.forEach(clearTimeout)
    }
  }, [])

  return (
    <section id="demo" className="relative py-32">
      <div className="max-w-5xl mx-auto px-6">
        {/* Section header */}
        <div className="text-center mb-16 animate-on-scroll">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            See it in <span className="gradient-text">action</span>
          </h2>
          <p className="mt-4 text-gray-400 text-lg max-w-2xl mx-auto">
            Define nodes, build flows, and get full observability — all in a few lines of Python.
          </p>
        </div>

        <div className="animate-on-scroll">
          {/* Code viewer */}
          <div className="code-block overflow-hidden">
            {/* Tab bar */}
            <div className="flex border-b border-white/5">
              {tabs.map((tab, i) => (
                <button
                  key={tab.label}
                  onClick={() => setActiveTab(i)}
                  className={`px-6 py-3 text-sm font-medium transition-all duration-200 border-b-2 ${
                    activeTab === i
                      ? 'text-neon-blue border-neon-blue bg-white/[0.02]'
                      : 'text-gray-500 border-transparent hover:text-gray-300 hover:bg-white/[0.01]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Code content */}
            <div className="p-6 overflow-x-auto">
              <pre className="!bg-transparent !m-0 !p-0">
                <code ref={codeRef} className="language-python">
                  {tabs[activeTab].code}
                </code>
              </pre>
            </div>
          </div>

          {/* Terminal output */}
          <div className="mt-6 code-block overflow-hidden">
            <div className="flex items-center justify-between px-6 py-3 border-b border-white/5">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/60" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                  <div className="w-3 h-3 rounded-full bg-green-500/60" />
                </div>
                <span className="text-xs text-gray-500 ml-3 font-mono">terminal</span>
              </div>
              <button
                onClick={runDemo}
                disabled={isRunning}
                className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all duration-300 ${
                  isRunning
                    ? 'bg-white/5 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-neon-blue to-neon-violet text-white hover:shadow-lg hover:shadow-neon-blue/20'
                }`}
              >
                {isRunning ? 'Running...' : 'Run Demo'}
              </button>
            </div>

            <div className="p-6 font-mono text-sm min-h-[280px]">
              {visibleLines === 0 && !isRunning && (
                <p className="text-gray-600 italic">Click "Run Demo" to see Agora in action...</p>
              )}
              {terminalLines.slice(0, visibleLines).map((line, i) => (
                <div key={i} className={`${line.color} leading-7`}>
                  {line.text || '\u00A0'}
                </div>
              ))}
              {isRunning && <span className="typing-cursor" />}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
