import { Outlet, Link, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { LayoutDashboard, FolderKanban, LogOut } from 'lucide-react'

export default function Layout() {
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-gray-900 text-white">
        <div className="p-6">
          <h1 className="text-2xl font-bold">Agora Cloud</h1>
          <p className="text-sm text-gray-400 mt-1">Workflow Platform</p>
        </div>
        <nav className="mt-6">
          <Link
            to="/dashboard"
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition"
          >
            <LayoutDashboard size={20} />
            Dashboard
          </Link>
          <Link
            to="/projects"
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition"
          >
            <FolderKanban size={20} />
            Projects
          </Link>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition w-full text-left mt-auto"
          >
            <LogOut size={20} />
            Sign Out
          </button>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
