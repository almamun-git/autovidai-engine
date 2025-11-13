import { ReactNode, useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
// Temporarily remove heroicons to resolve a React child error

type Props = { children: ReactNode }

export default function AppShell({ children }: Props) {
  const [open, setOpen] = useState(false)
  const nav = [
    { to: '/', label: 'Dashboard' },
    { to: '/workflow', label: 'Workflow Builder' },
    { to: '/generate', label: 'Generate Video' },
    { to: '/library', label: 'Video Library' },
    { to: '/logs', label: 'Logs & Analytics' },
  ]
  return (
    <div className="min-h-screen bg-ai-gradient">
      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr]">
        <aside className={`glass lg:sticky lg:top-0 lg:h-screen ${open ? 'block' : 'hidden'} lg:block m-3 p-4` }>
          <Link to="/" className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-white/5">
            <div className="h-8 w-8 rounded-lg bg-primary/20 border border-white/10 flex items-center justify-center">
              <span className="text-primary text-sm font-semibold">AI</span>
            </div>
            <span className="text-lg font-semibold">AutoVidAI</span>
          </Link>
          <nav className="mt-4 flex flex-col gap-1">
            {nav.map((n) => (
              <NavLink key={n.to} to={n.to} end className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${isActive ? 'bg-white/10' : 'hover:bg-white/5'}`}>
                <span className="inline-block h-2 w-2 rounded-full bg-white/40" />
                <span>{n.label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="mt-auto hidden lg:block text-xs text-muted px-3 pt-6">© {new Date().getFullYear()} AutoVidAI</div>
        </aside>
        <div className="m-3 lg:m-6">
          <header className="glass flex items-center justify-between px-4 py-3">
            <button className="lg:hidden btn-secondary" onClick={() => setOpen(!open)}>
              Menu
            </button>
            <div className="hidden lg:flex items-center gap-2 text-sm text-muted">
              <span className="badge">Status: Operational</span>
            </div>
            <div className="flex items-center gap-2">
              <Link to="/generate" className="btn-primary">
                Generate Video
              </Link>
            </div>
          </header>
          <main className="mt-4 lg:mt-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
