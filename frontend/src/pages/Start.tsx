import { useState, useEffect } from 'react'
import { Input, Label, Range } from '../components/ui/Form'
import ProgressBar from '../components/ui/ProgressBar'
import { apiUrl } from '../lib/api'

export default function Start() {
  // Do not hardcode a default niche — start empty so user can provide their own topic
  const [niche, setNiche] = useState('')
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
  const [idea, setIdea] = useState<any | null>(null)
  const [prompt, setPrompt] = useState<string>('')
  const [script, setScript] = useState<any | null>(null)
  const [stage2Loading, setStage2Loading] = useState(false)
  const [stage2Error, setStage2Error] = useState<string | null>(null)

  const start = async () => {
    setLoading(true)
    setResult(null)
    setProgress(5)
    try {
      const res = await fetch(apiUrl('/api/pipeline'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche, length, pacing, upload, verbose }),
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
      setVideoUrl(apiUrl(`/files/${filename}`))
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

  const fetchStage2Prompt = async () => {
    setStage2Loading(true)
    setStage2Error(null)
    setIdea(null)
    setPrompt('')
    setScript(null)
    try {
      const res = await fetch(apiUrl('/api/stage2/prompt'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche }),
      })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `Stage2 prompt failed with status ${res.status}`)
      }
      const data = await res.json()
      setIdea(data.idea)
      setPrompt(data.prompt)
    } catch (e) {
      setStage2Error(String(e))
    } finally {
      setStage2Loading(false)
    }
  }

  const runStage2 = async () => {
    if (!idea) {
      setStage2Error('No idea available. Generate the prompt first.')
      return
    }
    setStage2Loading(true)
    setStage2Error(null)
    setScript(null)
    try {
      const res = await fetch(apiUrl('/api/stage2/run'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, prompt }),
      })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `Stage2 run failed with status ${res.status}`)
      }
      const data = await res.json()
      setScript(data.script)
    } catch (e) {
      setStage2Error(String(e))
    } finally {
      setStage2Loading(false)
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
                    const r = await fetch(apiUrl('/api/pipeline/suggest?count=5'), { method: 'POST' })
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
          <div className="grid grid-cols-1 gap-4">
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
          <div className="mt-6 border-t border-white/10 pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Interactive Scriptwriter (Stage 2)</h3>
              <button
                type="button"
                className="btn-secondary text-xs"
                disabled={stage2Loading || !niche}
                onClick={fetchStage2Prompt}
              >
                {stage2Loading ? 'Loading…' : 'Generate Prompt'}
              </button>
            </div>
            {!niche && (
              <p className="text-xs text-muted">
                Enter a niche/topic above, then click “Generate Prompt”.
              </p>
            )}
            {stage2Error && (
              <p className="text-xs text-rose-300">{stage2Error}</p>
            )}
            {prompt && (
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted">
                  Stage 2 Prompt (editable)
                </label>
                <textarea
                  className="w-full h-40 text-xs font-mono bg-black/40 border border-white/10 rounded-lg p-2 focus:outline-none focus:border-cyan-400/60"
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                />
                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    className="btn-primary text-xs"
                    disabled={stage2Loading}
                    onClick={runStage2}
                  >
                    {stage2Loading ? 'Running Scriptwriter…' : 'Run Scriptwriter'}
                  </button>
                  {script && Array.isArray(script.scenes) && (
                    <span className="text-xs text-emerald-300">
                      Script generated with {script.scenes.length} scenes
                    </span>
                  )}
                </div>
              </div>
            )}
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
        <div className="pt-3 border-t border-white/10 space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted">
            Stage 2 Script
          </h4>
          {script && Array.isArray(script.scenes) && script.scenes.length > 0 ? (
            <div className="space-y-2 max-h-56 overflow-auto pr-1">
              {script.scenes.map((scene: any, idx: number) => (
                <div
                  key={idx}
                  className="border border-white/10 rounded-md p-2 bg-black/40"
                >
                  <div className="text-xs font-semibold mb-1">Scene {idx + 1}</div>
                  <div className="text-[11px] text-muted mb-1">
                    <span className="font-semibold">Visual:</span> {scene.visual}
                  </div>
                  <div className="text-[11px]">
                    <span className="font-semibold">Narration:</span> {scene.narration}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted">No script yet. Use Interactive Scriptwriter to generate one.</p>
          )}
        </div>
      </div>
    </div>
  )
}
