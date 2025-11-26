import { useParams } from 'react-router-dom'

export default function ProjectDetail() {
  const { projectId } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Project Detail</h1>
      <p className="text-gray-600">Project ID: {projectId}</p>
      <div className="mt-8 bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">Workflow visualization coming soon...</p>
        <p className="text-sm text-gray-400 mt-2">Cytoscape.js graph will be displayed here</p>
      </div>
    </div>
  )
}
