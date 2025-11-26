import { useParams } from 'react-router-dom'

export default function Monitoring() {
  const { projectId } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Monitoring</h1>
      <p className="text-gray-600">Project ID: {projectId}</p>
      <div className="mt-8 bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">Execution monitoring coming soon...</p>
        <p className="text-sm text-gray-400 mt-2">Real-time execution tracking will be displayed here</p>
      </div>
    </div>
  )
}
