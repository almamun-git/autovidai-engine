import { JsonView, defaultStyles } from 'react-json-view-lite'
import 'react-json-view-lite/dist/index.css'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'

export default function LogsAnalytics() {
  const data = Array.from({ length: 24 }).map((_, i) => ({ hour: `${i}:00`, ms: Math.round(200 + Math.random() * 200) }))
  const log = {
    level: 'info',
    ts: new Date().toISOString(),
    message: 'Render completed',
    jobId: 'job_abc123',
    metrics: { fps: 29.97, time_sec: 62.4, gpu: 'A100' },
  }
  const errors = [
    { ts: '2025-11-12T10:23:11Z', message: 'Media API rate limit', stage: 'Media' },
    { ts: '2025-11-12T09:02:45Z', message: 'Transient S3 error', stage: 'Output' },
  ]
  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div className="xl:col-span-2 card">
        <h3 className="text-base font-semibold">JSON Logs</h3>
        <div className="mt-3 rounded-lg border border-white/10 bg-white/5 p-3 overflow-auto">
          <JsonView data={log} shouldExpandNode={() => true} style={defaultStyles} />
        </div>
      </div>
      <div className="card">
        <h3 className="text-base font-semibold">Performance (ms per stage)</h3>
        <div className="mt-3 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <XAxis dataKey="hour" hide />
              <YAxis hide />
              <Tooltip contentStyle={{ background: 'rgba(0,0,0,0.7)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, color: 'white' }} />
              <Line type="monotone" dataKey="ms" stroke="#22d3ee" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card xl:col-span-3">
        <h3 className="text-base font-semibold">Error Tracing</h3>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          {errors.map((e, idx) => (
            <div key={idx} className="glass p-3 rounded-lg border border-rose-400/20">
              <div className="text-xs text-muted">{e.ts}</div>
              <div className="mt-1 text-rose-300">{e.message}</div>
              <div className="text-xs mt-1">Stage: {e.stage}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
