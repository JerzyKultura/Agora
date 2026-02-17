import { useState } from 'react'

const steps = [
  {
    number: '01',
    title: 'Install Agora',
    description: 'Install the framework with pip. Add the telemetry extra for OpenTelemetry and cloud platform support.',
    code: 'pip install git+https://github.com/JerzyKultura/Agora.git[telemetry]',
  },
  {
    number: '02',
    title: 'Initialize Telemetry',
    description: 'One line to set up tracing, audit logging, and optional cloud upload for your project.',
    code: `from agora.agora_tracer import init_agora

init_agora(
    app_name="my-app",
    project_name="My Project",
    enable_cloud_upload=True
)`,
  },
  {
    number: '03',
    title: 'Define Your Nodes',
    description: 'Use the @agora_node decorator to turn any async function into a traced workflow node.',
    code: `from agora.agora_tracer import agora_node

@agora_node(name="ProcessData")
async def process_data(shared):
    shared["result"] = transform(shared["input"])
    return "next"`,
  },
  {
    number: '04',
    title: 'Build & Run',
    description: 'Chain nodes into a flow with intuitive routing syntax, then run it. Telemetry is captured automatically.',
    code: `from agora.agora_tracer import TracedAsyncFlow

flow = TracedAsyncFlow("MyPipeline")
flow.start(fetch_data)
fetch_data - "process" >> process_data
process_data - "save" >> save_result

await flow.run_async({"input": "data"})`,
  },
]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="absolute top-3 right-3 px-2.5 py-1 rounded-md text-xs font-medium glass hover:bg-white/10 transition-all duration-200"
      title="Copy to clipboard"
    >
      {copied ? (
        <span className="text-neon-cyan">Copied!</span>
      ) : (
        <span className="text-gray-400">Copy</span>
      )}
    </button>
  )
}

export default function QuickStart() {
  return (
    <section id="quickstart" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        {/* Section header */}
        <div className="text-center mb-16 animate-on-scroll">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            Get started in <span className="gradient-text">minutes</span>
          </h2>
          <p className="mt-4 text-gray-400 text-lg max-w-2xl mx-auto">
            Four steps from zero to a fully instrumented workflow with telemetry.
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-8">
          {steps.map((step, i) => (
            <div
              key={step.number}
              className={`animate-on-scroll delay-${i + 1}`}
            >
              <div className="glass neon-border rounded-2xl p-8 transition-all duration-300 hover:-translate-y-0.5">
                <div className="flex items-start gap-6">
                  {/* Step number */}
                  <div className="hidden sm:flex shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-neon-blue/20 to-neon-violet/20 items-center justify-center">
                    <span className="text-xl font-bold gradient-text">{step.number}</span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="sm:hidden text-sm font-bold gradient-text">{step.number}</span>
                      <h3 className="text-lg font-semibold text-white">{step.title}</h3>
                    </div>
                    <p className="text-gray-400 text-sm mb-4">{step.description}</p>

                    {/* Code block */}
                    <div className="relative code-block p-4 overflow-x-auto">
                      <CopyButton text={step.code} />
                      <pre className="!m-0 !p-0 !bg-transparent">
                        <code className="text-neon-blue/90 font-mono text-sm">{step.code}</code>
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
