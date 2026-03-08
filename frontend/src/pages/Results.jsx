import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, ArrowRight, Share2, Download } from 'lucide-react'
import Header from '../components/Header'
import SchemeCard from '../components/SchemeCard'
import NyaayaScore from '../components/NyaayaScore'

export default function Results() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [showShare, setShowShare] = useState(false)
  const [copied, setCopied] = useState(false)

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

  function handleShare() {
    const text = [
      `Nyaaya.ai Results`,
      `Nyaaya Score: ${nyaayaScore?.score ?? '—'}/100 (Grade ${nyaayaScore?.grade ?? '—'})`,
      `Eligible for ${eligible.length} scheme(s)`,
      `Monthly benefit: Rs.${summary?.total_monthly_benefit ?? 0}`,
      `First year total: Rs.${summary?.first_year_total ?? 0}`,
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

  function handleDownload() {
    const profile = JSON.parse(sessionStorage.getItem('nyaaya_profile') || '{}')
    const report = {
      generated: new Date().toISOString(),
      profile,
      nyaaya_score: nyaayaScore,
      eligible_schemes: eligible,
      ineligible_schemes: ineligible,
      strategy: data.strategy,
      summary,
    }
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'nyaaya-eligibility-report.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 px-4 py-6 max-w-lg mx-auto w-full">
        {/* Nyaaya Score — the hero */}
        {nyaayaScore && (
          <div className="animate-fade-slide-up bg-gradient-to-br from-dark-800 to-dark-900 rounded-2xl border border-dark-700 p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">Your Nyaaya Score</h2>
              <div className="flex gap-2">
                <button
                  onClick={handleShare}
                  className="p-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-teal-400 transition-colors"
                  title="Share results"
                >
                  <Share2 size={16} />
                </button>
                <button
                  onClick={handleDownload}
                  className="p-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-teal-400 transition-colors"
                  title="Download report"
                >
                  <Download size={16} />
                </button>
              </div>
            </div>
            {copied && (
              <div className="text-xs text-teal-400 text-center mb-2 animate-fade-slide-up">
                Copied to clipboard!
              </div>
            )}
            <NyaayaScore scoreData={nyaayaScore} />
          </div>
        )}

        {/* Summary banner */}
        <div className="animate-fade-slide-up bg-gradient-to-br from-teal-900/50 to-dark-800 rounded-2xl border border-teal-700/40 p-5 mb-6" style={{ animationDelay: '150ms' }}>
          <h2 className="text-lg font-bold text-white mb-1">Eligibility Summary</h2>
          <p className="text-sm text-slate-300 mb-4">
            {eligible.length} of {(eligible.length + ineligible.length)} schemes match your profile.
          </p>

          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-teal-400">{summary?.schemes_count ?? eligible.length}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Schemes Eligible</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-teal-300">
                {'\u20B9'}{(summary?.total_monthly_benefit ?? 0).toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">Per Month</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">
                {'\u20B9'}{(summary?.first_year_total ?? 0).toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">First Year Total</div>
            </div>
          </div>
        </div>

        {/* Eligible schemes */}
        {eligible.length > 0 && (
          <section className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle size={18} className="text-teal-400" />
              <h3 className="font-semibold text-white">Eligible Schemes ({eligible.length})</h3>
            </div>
            <div className="space-y-3">
              {eligible.map(s => <SchemeCard key={s.scheme_id} scheme={s} showDetails />)}
            </div>
          </section>
        )}

        {/* Ineligible schemes */}
        {ineligible.length > 0 && (
          <section className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <XCircle size={18} className="text-slate-500" />
              <h3 className="font-semibold text-slate-400">Not Eligible ({ineligible.length})</h3>
            </div>
            <div className="space-y-3">
              {ineligible.map(s => <SchemeCard key={s.scheme_id} scheme={s} />)}
            </div>
          </section>
        )}

        {/* Documents list */}
        {summary?.documents_to_obtain?.length > 0 && (
          <section className="mb-6 animate-fade-slide-up">
            <h3 className="font-semibold text-white mb-3">Documents You'll Need</h3>
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

        {/* Action buttons */}
        <div className="space-y-3 mt-6">
          <button
            onClick={() => navigate('/strategy')}
            className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-500 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            View Application Strategy <ArrowRight size={18} />
          </button>
          <button
            onClick={() => navigate('/stories')}
            className="w-full flex items-center justify-center gap-2 bg-dark-700 hover:bg-dark-600 text-slate-300 font-medium py-3 rounded-xl border border-dark-600 transition-colors"
          >
            See Peer Success Stories
          </button>
        </div>
      </main>
    </div>
  )
}
