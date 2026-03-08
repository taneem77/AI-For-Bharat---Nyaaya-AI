export default function ProgressBar({ fields }) {
  if (!fields) return null

  const total = 11 // total possible profile fields
  const filled = Object.values(fields).filter(v => v !== null && v !== undefined).length
  const pct = Math.min(Math.round((filled / total) * 100), 100)

  return (
    <div className="px-4 py-2 bg-dark-800 border-b border-dark-700">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-400">Profile progress</span>
        <span className="text-xs font-medium text-teal-400">{pct}%</span>
      </div>
      <div className="w-full h-1.5 bg-dark-600 rounded-full overflow-hidden">
        <div
          className="h-full bg-teal-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
