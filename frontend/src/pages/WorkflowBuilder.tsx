import { useState } from 'react'
import StatusPill from '../components/ui/StatusPill'
import Drawer from '../components/ui/Drawer'

type Stage = { key: string; name: string; status: 'Pending'|'Running'|'Success'|'Error'; log: string }

export default function WorkflowBuilder() {
  const [open, setOpen] = useState<null | Stage>(null)
  const stages: Stage[] = [
    { key: 'idea', name: 'Idea', status: 'Success', log: '{"msg":"Idea generated","topic":"Stoicism tips"}' },
    { key: 'script', name: 'Script', status: 'Running', log: '{"progress":72,"status":"Drafting scenes"}' },
    { key: 'media', name: 'Media', status: 'Pending', log: '{"queued":true}' },
    { key: 'render', name: 'Render', status: 'Pending', log: '{"gpu":"idle"}' },
    { key: 'output', name: 'Output', status: 'Pending', log: '{"destination":"/videos"}' },
  ]
  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-base font-semibold">Pipeline</h3>
        <div className="mt-6 grid grid-cols-1 md:grid-cols-5 gap-4">
          {stages.map((s, i) => (
            <button key={s.key} onClick={() => setOpen(s)} className="group card hover:bg-white/7 transition-colors">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">{i+1}. {s.name}</div>
                <StatusPill status={s.status} />
              </div>
              <div className="mt-3 h-2 rounded bg-white/10 overflow-hidden">
                <div className={`h-full ${s.status==='Success'?'bg-emerald-400': s.status==='Running'?'bg-primary': s.status==='Error'?'bg-rose-400':'bg-white/20'}`} style={{ width: s.status==='Success' ? '100%' : s.status==='Running' ? '70%' : '10%' }} />
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <h4 className="font-semibold">Hints</h4>
          <p className="text-sm text-muted mt-2">Click a stage to view logs and actions in the drawer.</p>
        </div>
      </div>

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open?.name + ' Logs'}>
        {open && (
          <pre className="text-xs font-mono bg-white/5 p-3 rounded-lg border border-white/10 overflow-auto">{open.log}</pre>
        )}
      </Drawer>
    </div>
  )
}
