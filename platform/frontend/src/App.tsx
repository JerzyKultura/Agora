import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'
import type { User } from '@supabase/supabase-js'

import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import Monitoring from './pages/Monitoring'
import ExecutionDetail from './pages/ExecutionDetail'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import CostDashboard from './pages/CostDashboard'
import LiveTelemetry from './pages/LiveTelemetry'

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={!user ? <Login /> : <Navigate to="/dashboard" />} />
        <Route path="/" element={user ? <Layout /> : <Navigate to="/login" />}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:projectId" element={<ProjectDetail />} />
          <Route path="monitoring" element={<Monitoring />} />
          <Route path="monitoring/:projectId" element={<Monitoring />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="analytics/:projectId" element={<Analytics />} />
          <Route path="cost" element={<CostDashboard />} />
          <Route path="live" element={<LiveTelemetry />} />
          <Route path="executions/:executionId" element={<ExecutionDetail />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App