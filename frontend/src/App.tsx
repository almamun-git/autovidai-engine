import { Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import JobDetail from './pages/JobDetail'
import Start from './pages/Start'
import WorkflowBuilder from './pages/WorkflowBuilder'
import VideoLibrary from './pages/VideoLibrary'
import LogsAnalytics from './pages/LogsAnalytics'
import AppShell from './components/Layout/AppShell'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/workflow" element={<WorkflowBuilder />} />
        <Route path="/generate" element={<Start />} />
        <Route path="/library" element={<VideoLibrary />} />
        <Route path="/logs" element={<LogsAnalytics />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
      </Routes>
    </AppShell>
  )
}
