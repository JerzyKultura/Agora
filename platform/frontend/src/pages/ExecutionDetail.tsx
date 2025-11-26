import { useParams } from 'react-router-dom'

export default function ExecutionDetail() {
  const { executionId } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Execution Detail</h1>
      <p className="text-gray-600">Execution ID: {executionId}</p>
      <div className="mt-8 bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">Execution timeline and telemetry coming soon...</p>
        <p className="text-sm text-gray-400 mt-2">Node-by-node execution details will be displayed here</p>
      </div>
    </div>
  )
}
