import { Route, Routes, Link, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import JobDetail from './pages/JobDetail'
import Start from './pages/Start'

export default function App() {
  return (
    <div>
      <header style={{padding:'12px 16px', borderBottom:'1px solid #eee', display:'flex', gap:16, alignItems:'center'}}>
        <Link to="/" style={{fontWeight:700}}>AutoVidAI</Link>
        <nav style={{display:'flex', gap:12}}>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/start">Start</NavLink>
        </nav>
      </header>
      <main style={{padding:'16px'}}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/start" element={<Start />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
        </Routes>
      </main>
    </div>
  )
}
