import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, TrendingUp, Clock, ArrowRight, FileText } from 'lucide-react'
import Header from '../components/Header'

export default function Strategy() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)

  useEffect(() => {
    const raw = sessionStorage.getItem('nyaaya_results')
    if (!raw) { navigate('/interview'); return }
    setData(JSON.parse(raw))
  }, [navigate])

  if (!data) return null

  const strategy = data.strategy ?? []
  const summary = data.summary ?? {}
  const eligible = data.eligible_schemes?.filter(s => s.eligible) ?? []

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 px-4 py-6 max-w-lg mx-auto w-full">
        {/* Header */}
        <div className="animate-fade-slide-up mb-6">
          <h2 className="text-xl font-bold text-white mb-1">Your Application Strategy</h2>
          <p className="text-sm text-slate-400">
            Step-by-step plan to maximize your benefits.
            Apply in this order for the fastest results.
          </p>
        </div>

        {/* Summary cards */}
        <div className="animate-fade-slide-up grid grid-cols-2 gap-3 mb-6">
          <div className="bg-dark-800 rounded-xl border border-dark-700 p-4 text-center">
            <TrendingUp size={20} className="text-teal-400 mx-auto mb-1" />
            <div className="text-xl font-bold text-white">{'\u20B9'}{(summary.first_year_total ?? 0).toLocaleString()}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">First Year Total</div>
          </div>
          <div className="bg-dark-800 rounded-xl border border-dark-700 p-4 text-center">
            <Clock size={20} className="text-teal-400 mx-auto mb-1" />
            <div className="text-xl font-bold text-white">{summary.estimated_total_timeline_weeks ?? '—'}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Weeks Total</div>
          </div>
        </div>

        {/* Timeline */}
        <div className="relative mb-8">
          {/* Vertical line */}
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-dark-600" />

          {strategy.map((step, i) => {
            const scheme = eligible.find(s => s.scheme_id === step.scheme_id)
            return (
              <div
                key={step.scheme_id}
                className="animate-fade-slide-up relative pl-12 pb-8"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                {/* Circle on timeline */}
                <div className="absolute left-3 top-1 w-5 h-5 rounded-full bg-teal-600 border-2 border-dark-950 flex items-center justify-center">
                  <span className="text-[10px] font-bold text-white">{step.rank}</span>
                </div>

                {/* Card */}
                <div className="bg-dark-800 rounded-xl border border-dark-700 p-4">
                  {/* Week badge */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Calendar size={14} className="text-teal-400" />
                      <span className="text-xs font-medium text-teal-300">Week {step.apply_week}</span>
                    </div>
                    <span className="text-xs bg-teal-600/20 text-teal-300 px-2 py-0.5 rounded-full">
                      {'\u20B9'}{step.total_benefit.toLocaleString()}/yr
                    </span>
                  </div>

                  {/* Scheme name */}
                  <h4 className="font-semibold text-white text-sm mb-1">
                    {scheme?.scheme_name ?? step.scheme_id.replace(/_/g, ' ')}
                  </h4>

                  {/* Reasoning */}
                  <p className="text-xs text-slate-400 leading-relaxed mb-3">{step.reasoning}</p>

                  {/* Processing time */}
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock size={12} /> {step.timeline_weeks} weeks processing
                    </span>
                    {scheme && (
                      <span className="flex items-center gap-1">
                        <TrendingUp size={12} /> {Math.round(scheme.approval_rate * 100)}% approval
                      </span>
                    )}
                  </div>

                  {/* Documents */}
                  {scheme?.required_documents?.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-dark-700">
                      <div className="flex items-center gap-1 mb-1.5">
                        <FileText size={12} className="text-slate-500" />
                        <span className="text-[10px] text-slate-500 font-medium">Documents needed</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {scheme.required_documents.map(doc => (
                          <span key={doc} className="text-[10px] bg-dark-700 text-slate-400 px-1.5 py-0.5 rounded">
                            {doc.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Gantt-like visualization */}
        {strategy.length > 0 && (
          <div className="animate-fade-slide-up bg-dark-800 rounded-xl border border-dark-700 p-4 mb-6">
            <h4 className="text-sm font-medium text-white mb-3">Timeline Overview</h4>
            <div className="space-y-2">
              {strategy.map((step) => {
                const maxWeek = summary.estimated_total_timeline_weeks || 16
                const left = ((step.apply_week - 1) / maxWeek) * 100
                const width = Math.max((step.timeline_weeks / maxWeek) * 100, 15)
                const scheme = eligible.find(s => s.scheme_id === step.scheme_id)
                return (
                  <div key={step.scheme_id}>
                    <div className="text-[10px] text-slate-400 mb-0.5">
                      {scheme?.scheme_name ?? step.scheme_id}
                    </div>
                    <div className="relative h-6 bg-dark-700 rounded-lg overflow-hidden">
                      <div
                        className="absolute top-0 h-full bg-teal-600/60 rounded-lg flex items-center px-2"
                        style={{ left: `${left}%`, width: `${width}%` }}
                      >
                        <span className="text-[9px] text-white font-medium whitespace-nowrap">
                          W{step.apply_week}-{step.apply_week + step.timeline_weeks}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
              {/* Week markers */}
              <div className="flex justify-between text-[9px] text-slate-600 mt-1 px-0.5">
                <span>Week 1</span>
                <span>Week {Math.ceil((summary.estimated_total_timeline_weeks || 12) / 2)}</span>
                <span>Week {summary.estimated_total_timeline_weeks || 12}</span>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={() => navigate('/stories')}
            className="w-full flex items-center justify-center gap-2 bg-dark-700 hover:bg-dark-600 text-slate-300 font-medium py-3 rounded-xl border border-dark-600 transition-colors"
          >
            See Peer Success Stories <ArrowRight size={16} />
          </button>
          <button
            onClick={() => navigate('/results')}
            className="w-full text-sm text-slate-500 hover:text-slate-300 py-2 transition-colors"
          >
            Back to Results
          </button>
        </div>
      </main>
    </div>
  )
}
