import { useState } from 'react'
import { CheckCircle, XCircle, Clock, TrendingUp, ChevronRight, ChevronDown, Check } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

export default function SchemeCard({ scheme, onClick, isSelected, onSelect }) {
  const { t, formatINR } = useLanguage()
  const [showWhy, setShowWhy] = useState(false)
  const eligible = scheme.eligible

  function handleWhyClick(e) {
    e.stopPropagation()
    setShowWhy(v => !v)
  }

  function handleSelectClick(e) {
    e.stopPropagation()
    onSelect?.()
  }

  return (
    <div
      className={`animate-fade-slide-up rounded-2xl border p-4 transition-colors ${
        eligible
          ? 'bg-teal-900/20 border-teal-700/50'
          : 'bg-dark-800 border-dark-600'
      } ${onClick ? 'cursor-pointer hover:border-teal-500/60' : ''} ${
        isSelected ? 'ring-2 ring-teal-500' : ''
      }`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-white text-base">{scheme.scheme_name}</h3>
          <span className={`inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full ${
            eligible
              ? 'bg-teal-500/20 text-teal-300'
              : 'bg-dark-600 text-slate-400'
          }`}>
            {eligible ? t('scheme_eligible') : t('scheme_ineligible')}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {eligible && onSelect && (
            <button
              onClick={handleSelectClick}
              className={`w-6 h-6 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                isSelected ? 'bg-teal-600 border-teal-600' : 'border-dark-500 hover:border-teal-500'
              }`}
              aria-label={isSelected ? t('scheme_selected') : t('scheme_select')}
            >
              {isSelected && <Check size={14} className="text-white" />}
            </button>
          )}
          <div className={`p-2 rounded-xl ${eligible ? 'bg-teal-600/20' : 'bg-dark-700'}`}>
            {eligible
              ? <CheckCircle size={22} className="text-teal-400" />
              : <XCircle size={22} className="text-slate-500" />}
          </div>
          {onClick && <ChevronRight size={16} className="text-slate-500" />}
        </div>
      </div>

      <p className="text-sm text-slate-300 leading-relaxed mb-3 line-clamp-2">{scheme.reason}</p>

      {eligible && (
        <div className="flex flex-wrap gap-3 mb-3">
          {scheme.benefit_monthly > 0 && (
            <div className="flex items-center gap-1.5 text-sm">
              <TrendingUp size={14} className="text-teal-400" />
              <span className="text-teal-300 font-medium">{formatINR(scheme.benefit_monthly)}/{t('scheme_monthly')}</span>
            </div>
          )}
          {scheme.benefit_onetime > 0 && (
            <div className="flex items-center gap-1.5 text-sm">
              <TrendingUp size={14} className="text-teal-400" />
              <span className="text-teal-300 font-medium">{formatINR(scheme.benefit_onetime)} {t('scheme_onetime')}</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 text-sm text-slate-400">
            <Clock size={14} />
            <span>{scheme.processing_weeks} {t('scheme_weeks')}</span>
          </div>
        </div>
      )}

      {eligible && (
        <div className="flex gap-4 mb-1">
          <div className="text-xs text-slate-400">
            {t('scheme_confidence')}: <span className="text-teal-300 font-medium">{Math.round(scheme.confidence * 100)}%</span>
          </div>
          <div className="text-xs text-slate-400">
            {t('scheme_approval')}: <span className="text-teal-300 font-medium">{Math.round(scheme.approval_rate * 100)}%</span>
          </div>
        </div>
      )}

      {/* Why this scheme toggle */}
      <button
        onClick={handleWhyClick}
        className="mt-2 flex items-center gap-1 text-xs text-teal-400 hover:text-teal-300 font-medium transition-colors"
      >
        {t('scheme_why')}
        <ChevronDown size={14} className={`transition-transform ${showWhy ? 'rotate-180' : ''}`} />
      </button>

      {showWhy && (
        <div className="mt-2 p-3 bg-dark-800/80 rounded-xl border border-dark-700 animate-fade-slide-up">
          <p className="text-xs text-slate-300 leading-relaxed">{scheme.reason}</p>
          {eligible && scheme.required_documents?.length > 0 && (
            <div className="mt-2 pt-2 border-t border-dark-700">
              <div className="text-[10px] text-slate-500 font-medium mb-1">{t('scheme_docs')}:</div>
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
      )}
    </div>
  )
}
