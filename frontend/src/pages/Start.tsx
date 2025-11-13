import { useState } from 'react'
import { Input, Label, Select, Range } from '../components/ui/Form'
import ProgressBar from '../components/ui/ProgressBar'

export default function Start() {
  const [niche, setNiche] = useState('Stoicism')
  const [style, setStyle] = useState('motivational')
  const [length, setLength] = useState(60)
  const [pacing, setPacing] = useState(50)
  const [upload, setUpload] = useState(false)
  const [verbose, setVerbose] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)

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
            <Input value={niche} onChange={e => setNiche(e.target.value)} placeholder="e.g. Stoicism, AI productivity" />
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
      <div className="card">
        <h3 className="text-base font-semibold">Result</h3>
        <div className="mt-3">
          {result ? (
            <pre className="text-xs font-mono bg-white/5 p-3 rounded-lg border border-white/10 overflow-auto">{JSON.stringify(result, null, 2)}</pre>
          ) : (
            <p className="text-sm text-muted">Output will appear here after generation starts.</p>
          )}
        </div>
      </div>
    </div>
  )
}
