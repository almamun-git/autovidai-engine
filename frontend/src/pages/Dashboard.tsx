import StatCard from '../components/ui/StatCard'
import ActivityTimeline from '../components/ActivityTimeline'

export default function Dashboard() {
  const items = [
    { id: '1', title: 'Video #482 rendered (00:58)', time: '2m ago', status: 'Success' as const },
    { id: '2', title: 'Script generation queued for “Stoicism tips”', time: '12m ago', status: 'Pending' as const },
    { id: '3', title: 'Media search API rate limit recovered', time: '34m ago', status: 'Success' as const },
  ]
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
  <StatCard title="Generated Videos" value={482} />
  <StatCard title="Queued Tasks" value={7} />
        <StatCard title="API Usage (24h)" value={<span>12,430 <span className="text-xs text-muted">requests</span></span>} />
        <StatCard title="Workflow Health" value={<span className="text-emerald-400">98.9%</span>} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 card">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">Recent Activity</h3>
            <button className="btn-secondary text-sm">View all</button>
          </div>
          <div className="mt-4">
            <ActivityTimeline items={items} />
          </div>
        </div>
        <div className="card">
          <h3 className="text-base font-semibold">Quick Actions</h3>
          <div className="mt-4 grid gap-2">
            <a href="/generate" className="btn-primary justify-center">Generate Video</a>
            <button className="btn-secondary justify-center">Retry Workflow</button>
            <a href="/logs" className="btn-secondary justify-center">View Logs</a>
          </div>
        </div>
      </div>
    </div>
  )
}
