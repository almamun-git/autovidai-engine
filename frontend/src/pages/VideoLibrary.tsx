export default function VideoLibrary() {
  const videos = Array.from({ length: 8 }).map((_, i) => ({
    id: i + 1,
    title: `Video #${480 + i}`,
    thumb: `https://picsum.photos/seed/auto${i}/640/360`,
    status: i % 3 === 0 ? 'Success' : i % 3 === 1 ? 'Pending' : 'Error',
    date: '2025-11-12',
    category: ['Motivational', 'Educational', 'Storytelling'][i % 3],
  }))
  return (
    <div className="space-y-4">
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input placeholder="Search title…" className="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 outline-none focus:ring-2 focus:ring-primary/50" />
          <select className="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 outline-none focus:ring-2 focus:ring-primary/50">
            <option>All statuses</option>
            <option>Success</option>
            <option>Pending</option>
            <option>Error</option>
          </select>
          <select className="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 outline-none focus:ring-2 focus:ring-primary/50">
            <option>All categories</option>
            <option>Motivational</option>
            <option>Educational</option>
            <option>Storytelling</option>
          </select>
          <input type="date" className="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 outline-none focus:ring-2 focus:ring-primary/50" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {videos.map(v => (
          <div key={v.id} className="card p-0 overflow-hidden group">
            <div className="relative aspect-video bg-white/5">
              <img src={v.thumb} alt="thumb" className="w-full h-full object-cover" />
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 flex items-center justify-center gap-2">
                <button className="btn-primary">Preview</button>
                <button className="btn-secondary">Download</button>
                <a href={`/logs?id=${v.id}`} className="btn-secondary">View Logs</a>
              </div>
            </div>
            <div className="p-3">
              <div className="flex items-center justify-between">
                <div className="font-medium">{v.title}</div>
                <span className={`badge ${v.status==='Success'?'text-emerald-300 border-emerald-400/20 bg-emerald-500/10':v.status==='Error'?'text-rose-300 border-rose-400/20 bg-rose-500/10':'text-muted'}`}>{v.status}</span>
              </div>
              <div className="text-xs text-muted mt-1">{v.category} • {v.date}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
