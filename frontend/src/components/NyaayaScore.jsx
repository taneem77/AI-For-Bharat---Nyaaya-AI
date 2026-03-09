import { useState, useEffect } from 'react'
import { useLanguage } from '../context/LanguageContext'

const GRADE_COLORS = {
  A: { ring: 'text-emerald-400', bg: 'bg-emerald-400', glow: 'shadow-emerald-500/30' },
  B: { ring: 'text-teal-400', bg: 'bg-teal-400', glow: 'shadow-teal-500/30' },
  C: { ring: 'text-yellow-400', bg: 'bg-yellow-400', glow: 'shadow-yellow-500/30' },
  D: { ring: 'text-orange-400', bg: 'bg-orange-400', glow: 'shadow-orange-500/30' },
  F: { ring: 'text-red-400', bg: 'bg-red-400', glow: 'shadow-red-500/30' },
}

const LABEL_KEYS = {
  coverage: 'score_coverage',
  benefit: 'score_benefit',
  speed: 'score_speed',
  confidence: 'score_confidence',
}

export default function NyaayaScore({ scoreData }) {
  const { t } = useLanguage()
  const [animatedScore, setAnimatedScore] = useState(0)

  const score = scoreData?.score ?? 0
  const grade = scoreData?.grade ?? 'F'
  const breakdown = scoreData?.breakdown ?? {}
  const interpretation = scoreData?.interpretation ?? ''
  const colors = GRADE_COLORS[grade] || GRADE_COLORS.F

  useEffect(() => {
    if (score === 0) return
    const duration = 1200
    const steps = 60
    const increment = score / steps
    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= score) {
        setAnimatedScore(score)
        clearInterval(timer)
      } else {
        setAnimatedScore(Math.round(current * 10) / 10)
      }
    }, duration / steps)
    return () => clearInterval(timer)
  }, [score])

  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (animatedScore / 100) * circumference

  return (
    <div className="animate-fade-slide-up">
      <div className="flex flex-col items-center mb-5">
        <div className={`relative w-36 h-36 ${colors.glow} shadow-lg rounded-full`} role="img" aria-label={`Nyaaya Score: ${score}/100, Grade ${grade}`}>
          <svg className="w-36 h-36 -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60" cy="60" r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-dark-700"
            />
            <circle
              cx="60" cy="60" r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeLinecap="round"
              className={colors.ring}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{ transition: 'stroke-dashoffset 1.2s ease-out' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-white">{Math.round(animatedScore)}</span>
            <span className={`text-xs font-semibold ${colors.ring}`}>{t('score_grade')} {grade}</span>
          </div>
        </div>
        <p className="text-sm text-slate-300 text-center mt-3 max-w-xs">{interpretation}</p>
      </div>

      <div className="space-y-2.5">
        {Object.entries(breakdown).map(([key, value]) => (
          <div key={key}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">{t(LABEL_KEYS[key]) || key}</span>
              <span className="text-slate-300 font-medium">{Math.round(value)}%</span>
            </div>
            <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ease-out ${colors.bg}`}
                style={{ width: `${value}%`, opacity: 0.7 }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
