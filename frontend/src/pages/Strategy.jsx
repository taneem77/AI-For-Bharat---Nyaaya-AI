import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, TrendingUp, Clock, ArrowRight, FileText, AlertCircle } from 'lucide-react'
import Header from '../components/Header'
import { useLanguage } from '../context/LanguageContext'

export default function Strategy() {
  const navigate = useNavigate()
  const { t, formatINR } = useLanguage()
  const [data, setData] = useState(null)

  useEffect(() => {
    const raw = sessionStorage.getItem('nyaaya_results')
    if (!raw) { navigate('/interview'); return }
    setData(JSON.parse(raw))
  }, [navigate])

  if (!data) return null

  const allStrategy = data.strategy ?? []
  const summary = data.summary ?? {}
  const eligible = data.eligible_schemes?.filter(s => s.eligible) ?? []

  // Filter strategy by user-selected schemes
  const savedSelection = sessionStorage.getItem('nyaaya_selected_schemes')
  const selectedIds = savedSelection ? JSON.parse(savedSelection) : []
  const hasSelection = selectedIds.length > 0

  const strategy = hasSelection
    ? allStrategy.filter(s => selectedIds.includes(s.scheme_id))
    : allStrategy

  // Recalculate totals for selected schemes
  const selectedEligible = hasSelection
    ? eligible.filter(s => selectedIds.includes(s.scheme_id))
    : eligible

  const totalMonthly = selectedEligible.reduce((sum, s) => sum + (s.benefit_monthly || 0), 0)
  const totalOnetime = selectedEligible.reduce((sum, s) => sum + (s.benefit_onetime || 0), 0)
  const firstYearTotal = totalMonthly * 12 + totalOnetime
  const maxWeeks = strategy.length > 0
    ? Math.max(...strategy.map(s => (s.apply_week || 0) + (s.timeline_weeks || 0)))
    : summary.estimated_total_timeline_weeks || 0

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main id="main-content" className="flex-1 px-4 py-6 max-w-lg mx-auto w-full" role="main" aria-label={t('a11y_main')}>
        <div className="animate-fade-slide-up mb-6">
          <h2 className="text-xl font-bold text-white mb-1">{t('strategy_title')}</h2>
          <p className="text-sm text-slate-400">{t('strategy_sub')}</p>
        </div>

        {hasSelection && (
          <div className="animate-fade-slide-up flex items-center gap-2 bg-teal-900/30 border border-teal-700/40 rounded-xl px-4 py-2.5 mb-4">
            <AlertCircle size={14} className="text-teal-400 flex-shrink-0" />
            <span className="text-xs text-teal-300">
              {t('strategy_filtered', { count: selectedIds.length })}
            </span>
            <button
              onClick={() => {
                sessionStorage.removeItem('nyaaya_selected_schemes')
                window.location.reload()
              }}
              className="ml-auto text-xs text-teal-400 hover:text-teal-300 underline"
            >
              {t('strategy_show_all')}
            </button>
          </div>
        )}

        <div className="animate-fade-slide-up grid grid-cols-2 gap-3 mb-6">
          <div className="bg-dark-800 rounded-xl border border-dark-700 p-4 text-center">
            <TrendingUp size={20} className="text-teal-400 mx-auto mb-1" />
            <div className="text-xl font-bold text-white">{formatINR(firstYearTotal)}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">{t('strategy_first_year')}</div>
          </div>
          <div className="bg-dark-800 rounded-xl border border-dark-700 p-4 text-center">
            <Clock size={20} className="text-teal-400 mx-auto mb-1" />
            <div className="text-xl font-bold text-white">{maxWeeks || '-'}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">{t('strategy_weeks')}</div>
          </div>
        </div>

        {strategy.length === 0 && (
          <div className="animate-fade-slide-up bg-dark-800 rounded-xl border border-dark-700 p-6 text-center mb-6">
            <p className="text-sm text-slate-400">{t('strategy_none')}</p>
            <button
              onClick={() => navigate('/results')}
              className="mt-3 text-sm text-teal-400 hover:text-teal-300 font-medium"
            >
              {t('strategy_back')}
            </button>
          </div>
        )}

        <div className="relative mb-8">
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-dark-600" />
          {strategy.map((step, i) => {
            const scheme = eligible.find(s => s.scheme_id === step.scheme_id)
            return (
              <div
                key={step.scheme_id}
                className="animate-fade-slide-up relative pl-12 pb-8"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                <div className="absolute left-3 top-1 w-5 h-5 rounded-full bg-teal-600 border-2 border-dark-950 flex items-center justify-center">
                  <span className="text-[10px] font-bold text-white">{i + 1}</span>
                </div>
                <div className="bg-dark-800 rounded-xl border border-dark-700 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Calendar size={14} className="text-teal-400" />
                      <span className="text-xs font-medium text-teal-300">{t('strategy_week')} {step.apply_week}</span>
                    </div>
                    <span className="text-xs bg-teal-600/20 text-teal-300 px-2 py-0.5 rounded-full">
                      {formatINR(step.total_benefit)}/yr
                    </span>
                  </div>
                  <h4 className="font-semibold text-white text-sm mb-1">
                    {scheme?.scheme_name ?? step.scheme_id.replace(/_/g, ' ')}
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed mb-3">{step.reasoning}</p>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock size={12} /> {step.timeline_weeks} {t('scheme_weeks')}
                    </span>
                    {scheme && (
                      <span className="flex items-center gap-1">
                        <TrendingUp size={12} /> {Math.round(scheme.approval_rate * 100)}% {t('scheme_approval')}
                      </span>
                    )}
                  </div>
                  {scheme?.required_documents?.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-dark-700">
                      <div className="flex items-center gap-1 mb-1.5">
                        <FileText size={12} className="text-slate-500" />
                        <span className="text-[10px] text-slate-500 font-medium">{t('scheme_docs')}</span>
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

        {strategy.length > 0 && (
          <div className="animate-fade-slide-up bg-dark-800 rounded-xl border border-dark-700 p-4 mb-6">
            <h4 className="text-sm font-medium text-white mb-3">{t('strategy_timeline')}</h4>
            <div className="space-y-2">
              {strategy.map((step) => {
                const tMax = maxWeeks || 16
                const left = ((step.apply_week - 1) / tMax) * 100
                const width = Math.max((step.timeline_weeks / tMax) * 100, 15)
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
              <div className="flex justify-between text-[9px] text-slate-600 mt-1 px-0.5">
                <span>{t('strategy_week')} 1</span>
                <span>{t('strategy_week')} {Math.ceil((maxWeeks || 16) / 2)}</span>
                <span>{t('strategy_week')} {maxWeeks || 16}</span>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={() => navigate('/stories')}
            className="w-full flex items-center justify-center gap-2 bg-dark-700 hover:bg-dark-600 text-slate-300 font-medium py-3 rounded-xl border border-dark-600 transition-colors min-h-[44px] focus:outline-2 focus:outline-teal-400"
          >
            {t('strategy_stories_btn')} <ArrowRight size={16} />
          </button>
          <button
            onClick={() => navigate('/results')}
            className="w-full text-sm text-slate-500 hover:text-slate-300 py-2 transition-colors min-h-[44px] focus:outline-2 focus:outline-teal-400"
          >
            {t('strategy_back')}
          </button>
        </div>
      </main>
    </div>
  )
}
