import { useState } from 'react'

export default function Start() {
  const [niche, setNiche] = useState('Stoicism')
  const [upload, setUpload] = useState(false)
  const [verbose, setVerbose] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const start = async () => {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('/api/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche, upload, verbose }),
      })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ error: String(e) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h2>Start a Pipeline</h2>
      <label>
        Niche
        <input value={niche} onChange={e => setNiche(e.target.value)} placeholder="e.g. Stoicism" />
      </label>
      <div style={{display:'flex', gap:16, margin:'12px 0'}}>
        <label>
          <input type="checkbox" checked={upload} onChange={e => setUpload(e.target.checked)} /> Upload to YouTube
        </label>
        <label>
          <input type="checkbox" checked={verbose} onChange={e => setVerbose(e.target.checked)} /> Verbose logs
        </label>
      </div>
      <button disabled={loading} onClick={start}>{loading ? 'Running…' : 'Run Pipeline'}</button>

      {result && (
        <pre style={{marginTop:16, padding:12, background:'#f8f8f8', overflow:'auto'}}>
{JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  )
}
