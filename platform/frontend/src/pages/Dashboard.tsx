import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import  api  from '../lib/api'
import { FolderKanban, Activity, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const data = await api.projects.list()
      setProjects(data)
    } catch (error) {
      console.error('Failed to load projects:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome to Agora Cloud</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Projects</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{projects.length}</p>
            </div>
            <FolderKanban className="text-blue-600" size={32} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Workflows</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
            </div>
            <Activity className="text-green-600" size={32} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">0%</p>
            </div>
            <CheckCircle className="text-emerald-600" size={32} />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Recent Projects</h2>
            <Link
              to="/projects"
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              View All
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : projects.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500 mb-4">No projects yet</p>
            <Link
              to="/projects"
              className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Create Your First Project
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {projects.slice(0, 5).map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="block p-6 hover:bg-gray-50 transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{project.name}</h3>
                    {project.description && (
                      <p className="text-sm text-gray-600 mt-1">{project.description}</p>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(project.created_at).toLocaleDateString()}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
