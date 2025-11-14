import { useState, useEffect } from 'react'
import { Input, Label, Select, Range } from '../components/ui/Form'
import ProgressBar from '../components/ui/ProgressBar'

export default function Start() {
  // Do not hardcode a default niche — start empty so user can provide their own topic
  const [niche, setNiche] = useState('')
  const [style, setStyle] = useState('motivational')
  const [length, setLength] = useState(60)
  const [pacing, setPacing] = useState(50)
  const [upload, setUpload] = useState(false)
  const [verbose, setVerbose] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [suggesting, setSuggesting] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [suggestError, setSuggestError] = useState<string | null>(null)

  const start = async () => {
    setLoading(true)
    setResult(null)
    setProgress(5)
    try {
      const res = await fetch('/api/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche, style, length, pacing, upload, verbose }),
      })
      const data = await res.json()
      setProgress(90)
      setResult(data)
      // Derive playable video URL
      if (data.final_video_url) {
        if (data.final_video_url.startsWith('http')) {
          setVideoUrl(data.final_video_url)
        } else {
          const parts = data.final_video_url.split('/')
          const filename = parts[parts.length - 1] || 'final_video.mp4'
          setVideoUrl(`/files/${filename}`)
        }
      } else {
        setVideoUrl(null)
      }
    } catch (e) {
      setResult({ error: String(e) })
    } finally {
      setProgress(100)
      setLoading(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 card">
        <h2 className="text-lg font-semibold">Video Generation</h2>
        <div className="mt-4 grid gap-4">
          <div>
            <Label>Niche / Topic</Label>
            <div className="flex gap-2 items-center">
              <Input value={niche} onChange={e => setNiche(e.target.value)} placeholder="e.g. Stoicism, AI productivity" />
              <button
                type="button"
                className="btn-secondary"
                onClick={async () => {
                  setSuggesting(true)
                  setSuggestions([])
                  setSuggestError(null)
                  try {
                    const r = await fetch('/api/pipeline/suggest?count=5', { method: 'POST' })
                    if (!r.ok) throw new Error('Suggestion failed')
                    const j = await r.json()
                    if (Array.isArray(j.niches)) setSuggestions(j.niches)
                    else if (j.niche) setSuggestions([j.niche])
                  } catch (e) {
                    console.error(e)
                    setSuggestError(String(e))
                  } finally {
                    setSuggesting(false)
                  }
                }}
              >
                {suggesting ? 'Suggesting…' : 'Suggest topics'}
              </button>
            </div>
            {suggestError ? (
              <div className="mt-2 text-xs text-rose-300">{suggestError}</div>
            ) : null}
            {suggestions.length > 0 ? (
              <div className="mt-2 flex items-center gap-2 text-sm flex-wrap">
                <span className="text-muted">Top topics:</span>
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="px-2 py-1 rounded bg-white/5 border border-white/10 hover:border-primary/40"
                    onClick={() => setNiche(s)}
                    title="Use this topic"
                  >
                    {s}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Style</Label>
              <Select value={style} onChange={e => setStyle(e.target.value)}>
                <option value="motivational">Motivational</option>
                <option value="educational">Educational</option>
                <option value="storytelling">Storytelling</option>
                <option value="news">News</option>
              </Select>
            </div>
            <div>
              <Label>Video Length (sec)</Label>
              <Range label="Length" value={length} onChange={setLength} min={30} max={180} />
            </div>
          </div>
          <div>
            <Label>Pacing</Label>
            <Range label="Pacing" value={pacing} onChange={setPacing} min={0} max={100} />
          </div>
          <div className="flex items-center gap-6 text-sm">
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" className="accent-cyan-400" checked={upload} onChange={e => setUpload(e.target.checked)} /> Upload to YouTube
            </label>
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" className="accent-cyan-400" checked={verbose} onChange={e => setVerbose(e.target.checked)} /> Verbose logs
            </label>
          </div>
          <div className="flex items-center gap-3">
            <button disabled={loading} onClick={start} className="btn-primary">
              {loading ? 'Generating…' : 'Start Generation'}
            </button>
            <div className="flex-1">
              <ProgressBar value={progress} />
            </div>
          </div>
        </div>
      </div>
      <div className="card space-y-4">
        <h3 className="text-base font-semibold">Result</h3>
        <div>
          {videoUrl ? (
            <video
              key={videoUrl}
              controls
              className="w-full rounded-lg border border-white/10 bg-black"
              src={videoUrl}
            />
          ) : (
            <p className="text-xs text-muted">No video yet.</p>
          )}
        </div>
        <div>
          {result ? (
            <pre className="text-xs font-mono bg-white/5 p-3 rounded-lg border border-white/10 max-h-64 overflow-auto">{JSON.stringify(result, null, 2)}</pre>
          ) : (
            <p className="text-sm text-muted">Output will appear here after generation starts.</p>
          )}
        </div>
      </div>
    </div>
  )
}
