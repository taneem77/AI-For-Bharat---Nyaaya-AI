import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, ArrowRight, Share2, Download, FileText, Loader, GitCompare } from 'lucide-react'
import Header from '../components/Header'
import SchemeCard from '../components/SchemeCard'
import SchemeDetail from '../components/SchemeDetail'
import SchemeCompare from '../components/SchemeCompare'
import NyaayaScore from '../components/NyaayaScore'
import { useLanguage } from '../context/LanguageContext'
import { postReport } from '../api/client'

export default function Results() {
  const navigate = useNavigate()
  const { t, formatINR } = useLanguage()
  const [data, setData] = useState(null)
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [selectedScheme, setSelectedScheme] = useState(null)
  const [showCompare, setShowCompare] = useState(false)
  const [selectedSchemes, setSelectedSchemes] = useState(() => {
    const saved = sessionStorage.getItem('nyaaya_selected_schemes')
    return saved ? JSON.parse(saved) : []
  })

  useEffect(() => {
    const raw = sessionStorage.getItem('nyaaya_results')
    if (!raw) {
      navigate('/interview')
      return
    }
    setData(JSON.parse(raw))
  }, [navigate])

  if (!data) return null

  const eligible = data.eligible_schemes?.filter(s => s.eligible) ?? []
  const ineligible = data.eligible_schemes?.filter(s => !s.eligible) ?? []
  const summary = data.summary
  const nyaayaScore = summary?.nyaaya_score
  const strategy = data.strategy ?? []

  const selectedEligible = eligible.filter(s => selectedSchemes.includes(s.scheme_id))

  function handleShare() {
    const text = [
      `Nyaaya.ai Results`,
      `Nyaaya Score: ${nyaayaScore?.score ?? '-'}/100 (Grade ${nyaayaScore?.grade ?? '-'})`,
      `Eligible for ${eligible.length} scheme(s)`,
      `Monthly benefit: ${formatINR(summary?.total_monthly_benefit ?? 0)}`,
      `First year total: ${formatINR(summary?.first_year_total ?? 0)}`,
      `\nSchemes: ${eligible.map(s => s.scheme_name).join(', ') || 'None'}`,
      `\nCheck your eligibility at Nyaaya.ai`,
    ].join('\n')

    if (navigator.share) {
      navigator.share({ title: 'My Nyaaya.ai Results', text })
    } else {
      navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  async function handleDownloadPDF() {
    const profile = JSON.parse(sessionStorage.getItem('nyaaya_profile') || '{}')
    setDownloading(true)
    try {
      const blob = await postReport(profile, data)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'nyaaya-eligibility-report.pdf'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      const report = {
        generated: new Date().toISOString(),
        profile: JSON.parse(sessionStorage.getItem('nyaaya_profile') || '{}'),
        nyaaya_score: nyaayaScore,
        eligible_schemes: eligible,
        ineligible_schemes: ineligible,
        strategy,
        summary,
      }
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'nyaaya-eligibility-report.json'
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloading(false)
    }
  }

  function handleSelectScheme(schemeId) {
    setSelectedSchemes(prev => {
      const next = prev.includes(schemeId)
        ? prev.filter(id => id !== schemeId)
        : [...prev, schemeId]
      sessionStorage.setItem('nyaaya_selected_schemes', JSON.stringify(next))
      return next
    })
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main id="main-content" className="flex-1 px-4 py-6 max-w-lg mx-auto w-full" role="main" aria-label={t('a11y_main')}>
        {nyaayaScore && (
          <div className="animate-fade-slide-up bg-gradient-to-br from-dark-800 to-dark-900 rounded-2xl border border-dark-700 p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">{t('results_title')}</h2>
              <div className="flex gap-2">
                <button
                  onClick={handleShare}
                  className="p-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-teal-400 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center focus:outline-2 focus:outline-teal-400"
                  title={t('results_share')}
                  aria-label={t('results_share')}
                >
                  <Share2 size={16} />
                </button>
                <button
                  onClick={handleDownloadPDF}
                  disabled={downloading}
                  className="p-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-teal-400 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center focus:outline-2 focus:outline-teal-400 disabled:opacity-50"
                  title={t('results_download')}
                  aria-label={t('results_download')}
                >
                  {downloading ? <Loader size={16} className="animate-spin" /> : <Download size={16} />}
                </button>
              </div>
            </div>
            {copied && (
              <div className="text-xs text-teal-400 text-center mb-2 animate-fade-slide-up">
                {t('results_copied')}
              </div>
            )}
            <NyaayaScore scoreData={nyaayaScore} />
          </div>
        )}

        <div className="animate-fade-slide-up bg-gradient-to-br from-teal-900/50 to-dark-800 rounded-2xl border border-teal-700/40 p-5 mb-6" style={{ animationDelay: '150ms' }}>
          <h2 className="text-lg font-bold text-white mb-1">{t('results_summary')}</h2>
          <p className="text-sm text-slate-300 mb-4">
            {t('results_match', { count: eligible.length, total: eligible.length + ineligible.length })}
          </p>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-teal-400">{summary?.schemes_count ?? eligible.length}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{t('results_schemes_eligible')}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-teal-300">{formatINR(summary?.total_monthly_benefit ?? 0)}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{t('results_per_month')}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{formatINR(summary?.first_year_total ?? 0)}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{t('results_first_year')}</div>
            </div>
          </div>
        </div>

        <button
          onClick={handleDownloadPDF}
          disabled={downloading}
          className="animate-fade-slide-up w-full flex items-center justify-center gap-2 bg-gradient-to-r from-teal-600 to-teal-700 hover:from-teal-500 hover:to-teal-600 text-white font-semibold py-3 rounded-xl transition-all mb-6 shadow-md min-h-[44px] focus:outline-2 focus:outline-teal-400 disabled:opacity-60"
          style={{ animationDelay: '200ms' }}
        >
          {downloading ? <Loader size={18} className="animate-spin" /> : <FileText size={18} />}
          {t('results_download')} (PDF)
        </button>

        {eligible.length > 0 && (
          <section className="mb-6" aria-label={t('results_eligible')}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <CheckCircle size={18} className="text-teal-400" />
                <h3 className="font-semibold text-white">{t('results_eligible')} ({eligible.length})</h3>
              </div>
              {selectedSchemes.length >= 2 && (
                <button
                  onClick={() => setShowCompare(true)}
                  className="flex items-center gap-1.5 text-xs font-medium text-teal-400 hover:text-teal-300 bg-teal-900/30 hover:bg-teal-900/50 px-3 py-1.5 rounded-lg transition-colors"
                >
                  <GitCompare size={14} />
                  {t('compare_btn')} ({selectedSchemes.length})
                </button>
              )}
            </div>
            <p className="text-xs text-slate-400 mb-3">{t('results_select_hint')}</p>
            <div className="space-y-3">
              {eligible.map(s => (
                <SchemeCard
                  key={s.scheme_id}
                  scheme={s}
                  onClick={() => setSelectedScheme(s)}
                  isSelected={selectedSchemes.includes(s.scheme_id)}
                  onSelect={() => handleSelectScheme(s.scheme_id)}
                />
              ))}
            </div>
          </section>
        )}

        {ineligible.length > 0 && (
          <section className="mb-6" aria-label={t('results_ineligible')}>
            <div className="flex items-center gap-2 mb-3">
              <XCircle size={18} className="text-slate-500" />
              <h3 className="font-semibold text-slate-400">{t('results_ineligible')} ({ineligible.length})</h3>
            </div>
            <div className="space-y-3">
              {ineligible.map(s => (
                <SchemeCard
                  key={s.scheme_id}
                  scheme={s}
                  onClick={() => setSelectedScheme(s)}
                />
              ))}
            </div>
          </section>
        )}

        {summary?.documents_to_obtain?.length > 0 && (
          <section className="mb-6 animate-fade-slide-up" aria-label={t('results_docs')}>
            <h3 className="font-semibold text-white mb-3">{t('results_docs')}</h3>
            <div className="bg-dark-800 rounded-xl border border-dark-700 divide-y divide-dark-700">
              {summary.documents_to_obtain.map(doc => (
                <div key={doc} className="px-4 py-2.5 text-sm text-slate-300 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  {doc.replace(/_/g, ' ')}
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="space-y-3 mt-6">
          <button
            onClick={() => navigate('/strategy')}
            className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-500 text-white font-semibold py-3 rounded-xl transition-colors min-h-[44px] focus:outline-2 focus:outline-teal-400"
          >
            {selectedSchemes.length > 0
              ? t('results_strategy_selected', { count: selectedSchemes.length })
              : t('results_strategy_btn')
            } <ArrowRight size={18} />
          </button>
          <button
            onClick={() => navigate('/stories')}
            className="w-full flex items-center justify-center gap-2 bg-dark-700 hover:bg-dark-600 text-slate-300 font-medium py-3 rounded-xl border border-dark-600 transition-colors min-h-[44px] focus:outline-2 focus:outline-teal-400"
          >
            {t('results_stories_btn')}
          </button>
        </div>
      </main>

      {selectedScheme && (
        <SchemeDetail
          scheme={selectedScheme}
          strategy={strategy}
          onClose={() => setSelectedScheme(null)}
          onSelect={selectedScheme.eligible ? handleSelectScheme : undefined}
          isSelected={selectedSchemes.includes(selectedScheme.scheme_id)}
        />
      )}

      {showCompare && (
        <SchemeCompare
          schemes={selectedEligible}
          onClose={() => setShowCompare(false)}
        />
      )}
    </div>
  )
}
