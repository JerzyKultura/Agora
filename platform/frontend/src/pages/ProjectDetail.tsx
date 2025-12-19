import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import WorkflowGraph from '../components/WorkflowGraph'
import CodeViewer from '../components/CodeViewer'
import { FileCode, X, Activity } from 'lucide-react'
import { api } from '../lib/api'

export default function ProjectDetail() {
  const { projectId } = useParams()
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [project, setProject] = useState<any>(null)
  const [currentWorkflow, setCurrentWorkflow] = useState<any>(null)

  const [graphNodes, setGraphNodes] = useState<any[]>([])
  const [graphEdges, setGraphEdges] = useState<any[]>([])
  const [nodeData, setNodeData] = useState<Record<string, any>>({})

  useEffect(() => {
    if (!projectId) return

    const loadData = async () => {
      setLoading(true)
      try {
        // 1. Fetch Project Details
        const proj = await api.projects.get(projectId)
        setProject(proj)

        // 2. Fetch Workflows
        const flows = await api.workflows.list(projectId)

        if (flows.length > 0) {
          // Default to the most recent workflow (first in list due to API sort)
          const latestFlow = flows[0]
          setCurrentWorkflow(latestFlow)

          // 3. Fetch Graph
          const { nodes, edges } = await api.workflows.getGraph(latestFlow.id)

          // Transform for Cytoscape
          // Nodes: needs { id, label, type }
          // Edges: needs { source, target, label } (Note: edges table structure might differ)
          // DB Edges table usually has: source_node_id, target_node_id
          // BUT: The current python tracer DOES NOT UPLOAD EDGES explicitly yet.
          // Wait, 'demo_workflow.py' prints a diagram, but check if it uploads edges.
          // It calls `add_node_execution` but seemingly not `add_edge`.
          // Let's assume nodes exist. If edges are missing, we might only see nodes.

          const nodeIds = new Set(nodes.map((n: any) => n.id))

          const transformedNodes = nodes.map((n: any) => ({
            id: n.id,
            label: n.name,
            type: n.type === 'start' ? 'start' : n.type === 'end' ? 'end' : 'process'
          }))

          const transformedEdges = edges
            .filter((e: any) => nodeIds.has(e.from_node_id) && nodeIds.has(e.to_node_id))
            .map((e: any) => ({
              source: e.from_node_id,
              target: e.to_node_id,
              label: e.action || ''
            }))

          setGraphNodes(transformedNodes)
          setGraphEdges(transformedEdges)

          // Map node details (prioritize code, fallback to config)
          const detailMap: Record<string, { content: string; language: string }> = {}
          nodes.forEach((n: any) => {
            if (n.code) {
              detailMap[n.id] = { content: n.code, language: 'python' }
            } else {
              detailMap[n.id] = {
                content: n.config ? JSON.stringify(n.config, null, 2) : "No details available",
                language: 'json'
              }
            }
          })
          setNodeData(detailMap)
        }
      } catch (err: any) {
        console.error("Failed to load project:", err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [projectId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600">
        <h2 className="text-xl font-bold mb-2">Error Loading Project</h2>
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col">
      <div className="p-6 pb-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{project?.name || 'Project'}</h1>
        <p className="text-gray-600 mb-4">{project?.description || `Project ID: ${projectId}`}</p>

        {/* Workflow Selector (Simple header for now) */}
        {currentWorkflow && (
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Activity className="w-4 h-4" />
            <span>Viewing Workflow: <strong>{currentWorkflow.name}</strong></span>
          </div>
        )}
      </div>

      <div className="flex-1 flex overflow-hidden p-6 gap-6">
        {/* Graph Area */}
        <div className={`bg-white rounded-lg shadow flex flex-col transition-all duration-300 ${selectedNodeId ? 'w-1/2' : 'w-full'}`}>
          <div className="p-4 border-b border-gray-100 flex justify-between items-center">
            <h2 className="text-lg font-semibold">Workflow Graph</h2>
            <span className="text-xs text-gray-400">{graphNodes.length} Nodes</span>
          </div>
          <div className="flex-1 p-4 relative">
            {graphNodes.length === 0 ? (
              <div className="absolute inset-0 flex items-center justify-center text-gray-400">
                No workflow data found. Run a workflow to see it here.
              </div>
            ) : (
              <div className="absolute inset-0">
                <WorkflowGraph
                  nodes={graphNodes}
                  edges={graphEdges}
                  onNodeClick={setSelectedNodeId}
                />
              </div>
            )}
          </div>
        </div>

        {/* Code Viewer Side Panel */}
        {selectedNodeId && (
          <div className="w-1/2 bg-white rounded-lg shadow flex flex-col animate-in slide-in-from-right duration-300">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-semibold">Node Metadata</h2>
              </div>
              <button
                onClick={() => setSelectedNodeId(null)}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                aria-label="Close code viewer"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="flex-1 p-0 overflow-hidden relative">
              <CodeViewer
                code={nodeData[selectedNodeId]?.content || "# No details available"}
                language={nodeData[selectedNodeId]?.language || "python"}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
