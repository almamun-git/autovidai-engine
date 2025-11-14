import { useEffect, useState } from 'react'

type LibraryVideo = {
  filename: string
  url: string
  size: number
  mtime: number
}

export default function VideoLibrary() {
  const [videos, setVideos] = useState<LibraryVideo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const fetchVideos = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/library/videos')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setVideos(data.videos || [])
    } catch (e: any) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchVideos() }, [])

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="font-medium">Generated Videos</div>
          <button className="btn-secondary" onClick={fetchVideos} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button>
        </div>
        {error ? <div className="text-xs text-rose-300 mt-2">{error}</div> : null}
      </div>

      {videos.length === 0 ? (
        <div className="card text-sm text-muted">No videos found. Generate one from the Start page first.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {videos.map(v => (
            <div key={v.filename} className="card p-0 overflow-hidden group">
              <div className="relative aspect-video bg-white/5">
                {/* Use an inline video poster-less preview; show controls on hover */}
                <video src={v.url} className="w-full h-full object-cover" muted playsInline/>
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 flex items-center justify-center gap-2">
                  <button className="btn-primary" onClick={() => setPreviewUrl(v.url)}>Preview</button>
                  <a className="btn-secondary" href={v.url} download>Download</a>
                </div>
              </div>
              <div className="p-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium truncate" title={v.filename}>{v.filename}</div>
                  <span className="badge text-muted">{(v.size/1024/1024).toFixed(2)} MB</span>
                </div>
                <div className="text-xs text-muted mt-1">{new Date(v.mtime*1000).toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {previewUrl ? (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-6" onClick={() => setPreviewUrl(null)}>
          <div className="bg-black rounded-lg border border-white/10 p-3 w-full max-w-4xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-2">
              <div className="font-medium">Preview</div>
              <button className="btn-ghost" onClick={() => setPreviewUrl(null)}>Close</button>
            </div>
            <video src={previewUrl} controls className="w-full rounded"/>
          </div>
        </div>
      ) : null}
    </div>
  )
}
