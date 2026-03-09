import { useState, useEffect } from 'react'
import { X, CheckCircle, XCircle, Clock, TrendingUp, FileText, MapPin, ExternalLink, Check } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { postChecklist } from '../api/client'

const DIFFICULTY_COLORS = {
  easy: 'bg-emerald-500/20 text-emerald-300',
  medium: 'bg-yellow-500/20 text-yellow-300',
  hard: 'bg-red-500/20 text-red-300',
}

export default function SchemeDetail({ scheme, strategy, onClose, onSelect, isSelected }) {
  const { t, formatINR, lang } = useLanguage()
  const [checklist, setChecklist] = useState(null)
  const [checked, setChecked] = useState(() => {
    const saved = localStorage.getItem(`nyaaya_docs_${scheme.scheme_id}`)
    return saved ? JSON.parse(saved) : {}
  })

  useEffect(() => {
    if (scheme.eligible && scheme.scheme_id) {
      postChecklist([scheme.scheme_id])
        .then(res => setChecklist(res.checklist || []))
        .catch(() => {})
    }
  }, [scheme.scheme_id])

  function toggleDoc(doc) {
    setChecked(prev => {
      const next = { ...prev, [doc]: !prev[doc] }
      localStorage.setItem(`nyaaya_docs_${scheme.scheme_id}`, JSON.stringify(next))
      return next
    })
  }

  const eligible = scheme.eligible
  const stepInfo = strategy?.find(s => s.scheme_id === scheme.scheme_id)
  const checkedCount = Object.values(checked).filter(Boolean).length
  const totalDocs = checklist?.length || scheme.required_documents?.length || 0

  return (
    <div className="fixed inset-0 z-[200] flex items-end sm:items-center justify-center" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative bg-dark-900 rounded-t-2xl sm:rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto animate-fade-slide-up border border-dark-700"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`sticky top-0 z-10 px-5 py-4 border-b border-dark-700 ${eligible ? 'bg-teal-900/30' : 'bg-dark-800'} rounded-t-2xl`}>
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <h2 className="text-lg font-bold text-white">{scheme.scheme_name}</h2>
              <span className={`inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                eligible ? 'bg-teal-500/20 text-teal-300' : 'bg-dark-600 text-slate-400'
              }`}>
                {eligible ? t('scheme_eligible') : t('scheme_ineligible')}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-dark-700 text-slate-400 hover:text-white transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label={t('scheme_close')}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Reason */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{t('scheme_reason_title')}</h3>
            <p className="text-sm text-slate-300 leading-relaxed">{scheme.reason}</p>
          </div>

          {/* Benefits + Stats */}
          {eligible && (
            <div className="grid grid-cols-2 gap-3">
              {scheme.benefit_monthly > 0 && (
                <div className="bg-dark-800 rounded-xl p-3 border border-dark-700">
                  <TrendingUp size={16} className="text-teal-400 mb-1" />
                  <div className="text-lg font-bold text-teal-300">{formatINR(scheme.benefit_monthly)}</div>
                  <div className="text-[10px] text-slate-400">{t('scheme_monthly')}</div>
                </div>
              )}
              {scheme.benefit_onetime > 0 && (
                <div className="bg-dark-800 rounded-xl p-3 border border-dark-700">
                  <TrendingUp size={16} className="text-teal-400 mb-1" />
                  <div className="text-lg font-bold text-teal-300">{formatINR(scheme.benefit_onetime)}</div>
                  <div className="text-[10px] text-slate-400">{t('scheme_onetime')}</div>
                </div>
              )}
              <div className="bg-dark-800 rounded-xl p-3 border border-dark-700">
                <Clock size={16} className="text-teal-400 mb-1" />
                <div className="text-lg font-bold text-white">{scheme.processing_weeks} {t('scheme_weeks')}</div>
                <div className="text-[10px] text-slate-400">{t('scheme_processing')}</div>
              </div>
              <div className="bg-dark-800 rounded-xl p-3 border border-dark-700">
                <CheckCircle size={16} className="text-teal-400 mb-1" />
                <div className="text-lg font-bold text-white">{Math.round(scheme.approval_rate * 100)}%</div>
                <div className="text-[10px] text-slate-400">{t('scheme_approval')}</div>
              </div>
            </div>
          )}

          {/* Strategy step info */}
          {stepInfo && (
            <div className="bg-teal-900/20 rounded-xl p-4 border border-teal-700/40">
              <div className="flex items-center gap-2 mb-2">
                <MapPin size={14} className="text-teal-400" />
                <span className="text-xs font-medium text-teal-300">
                  {t('strategy_week')} {stepInfo.apply_week} — {formatINR(stepInfo.total_benefit)}/yr
                </span>
              </div>
              <p className="text-xs text-slate-400">{stepInfo.reasoning}</p>
            </div>
          )}

          {/* How to apply */}
          {eligible && (
            <div>
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{t('scheme_how_to_apply')}</h3>
              <p className="text-sm text-slate-300">{t('scheme_how_to_apply_desc')}</p>
            </div>
          )}

          {/* Document Checklist */}
          {eligible && (checklist || scheme.required_documents?.length > 0) && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{t('scheme_docs')}</h3>
                {totalDocs > 0 && (
                  <span className="text-xs text-teal-400 font-medium">
                    {checkedCount}/{totalDocs}
                  </span>
                )}
              </div>
              {/* Progress bar */}
              {totalDocs > 0 && (
                <div className="w-full h-1.5 bg-dark-700 rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-teal-500 rounded-full transition-all duration-300"
                    style={{ width: `${(checkedCount / totalDocs) * 100}%` }}
                  />
                </div>
              )}
              <div className="space-y-2">
                {(checklist || scheme.required_documents.map(d => ({ document: d.replace(/_/g, ' '), document_hi: '', timeline_week: 2, difficulty: 'medium' }))).map((item) => {
                  const docKey = typeof item === 'string' ? item : item.document
                  const isChecked = checked[docKey]
                  const difficulty = item.difficulty || 'medium'
                  const diffKey = `scheme_difficulty_${difficulty}`
                  return (
                    <button
                      key={docKey}
                      onClick={() => toggleDoc(docKey)}
                      className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-colors text-left ${
                        isChecked
                          ? 'bg-teal-900/20 border-teal-700/50'
                          : 'bg-dark-800 border-dark-700 hover:border-dark-600'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 ${
                        isChecked ? 'bg-teal-600 border-teal-600' : 'border-dark-500'
                      }`}>
                        {isChecked && <Check size={12} className="text-white" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm font-medium ${isChecked ? 'text-teal-300 line-through' : 'text-white'}`}>
                          {docKey}
                        </div>
                        {item.document_hi && lang === 'hi' && (
                          <div className="text-xs text-slate-400">{item.document_hi}</div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {item.timeline_week && (
                          <span className="text-[10px] text-slate-500">
                            {t('scheme_checklist_week', { n: item.timeline_week })}
                          </span>
                        )}
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${DIFFICULTY_COLORS[difficulty]}`}>
                          {t(diffKey)}
                        </span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Bottom action */}
        {eligible && onSelect && (
          <div className="sticky bottom-0 px-5 py-4 border-t border-dark-700 bg-dark-900">
            <button
              onClick={() => onSelect(scheme.scheme_id)}
              className={`w-full py-3 rounded-xl font-semibold transition-all min-h-[44px] flex items-center justify-center gap-2 ${
                isSelected
                  ? 'bg-teal-700 text-teal-200 border border-teal-600'
                  : 'bg-teal-600 hover:bg-teal-500 text-white'
              }`}
            >
              {isSelected ? (
                <><CheckCircle size={18} /> {t('scheme_selected')}</>
              ) : (
                t('scheme_select')
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
