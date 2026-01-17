import { Outlet, Link, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { LayoutDashboard, FolderKanban, Activity, BarChart3, Settings, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'

export default function Layout() {
  const navigate = useNavigate()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex bg-gray-50 transition-colors">
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:static lg:inset-0
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-6 flex justify-between items-center border-b border-gray-800">
          <div>
            <h1 className="text-2xl font-bold text-white">Agora</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest mt-1">Telemetry Platform</p>
          </div>
          <button
            className="lg:hidden text-gray-400 hover:text-white"
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="mt-6 flex flex-col h-[calc(100%-120px)]">
          <Link
            to="/dashboard"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition text-gray-300 hover:text-white"
          >
            <LayoutDashboard size={18} />
            <span className="text-sm font-medium">Dashboard</span>
          </Link>
          <Link
            to="/projects"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition text-gray-300 hover:text-white"
          >
            <FolderKanban size={18} />
            <span className="text-sm font-medium">Projects</span>
          </Link>
          <Link
            to="/monitoring"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition text-gray-300 hover:text-white"
          >
            <Activity size={18} />
            <span className="text-sm font-medium">Monitoring</span>
          </Link>
          <Link
            to="/analytics"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition text-gray-300 hover:text-white"
          >
            <BarChart3 size={18} />
            <span className="text-sm font-medium">Analytics</span>
          </Link>
          <Link
            to="/cost"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition text-gray-300 hover:text-white"
          >
            <Activity size={18} className="text-green-400" />
            <span className="text-sm font-medium">Cost & Usage</span>
          </Link>
          <Link
            to="/settings"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition text-gray-300 hover:text-white"
          >
            <Settings size={18} />
            <span className="text-sm font-medium">Settings</span>
          </Link>

          <div className="mt-auto px-6 py-6 border-t border-gray-800">
            <button
              onClick={handleSignOut}
              className="flex items-center gap-3 text-red-400 hover:text-red-300 transition w-full text-left"
            >
              <LogOut size={18} />
              <span className="text-sm font-medium">Sign Out</span>
            </button>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-50 transition-colors relative">
        {/* Mobile Header */}
        <header className="lg:hidden bg-white border-b border-gray-200 p-4 flex justify-between items-center sticky top-0 z-30">
          <h1 className="font-bold text-gray-900">Agora</h1>
          <button
            className="text-gray-500"
            onClick={() => setIsMobileMenuOpen(true)}
          >
            <Menu size={24} />
          </button>
        </header>

        <div className="p-4 md:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
