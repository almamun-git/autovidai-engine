type Props = { value: number }

export default function ProgressBar({ value }: Props) {
  const clamped = Math.min(100, Math.max(0, value))
  const anim = clamped < 100 ? 'animate-shimmer' : ''
  return (
    <div className="progress-track">
      <div
        className={`progress-fill transition-all ${anim}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  )
}
