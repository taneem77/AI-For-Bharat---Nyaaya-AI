import { X, CheckCircle, Clock, TrendingUp, FileText } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

export default function SchemeCompare({ schemes, onClose }) {
  const { t, formatINR } = useLanguage()

  if (!schemes || schemes.length < 2) return null

  const rows = [
    {
      label: t('scheme_monthly'),
      icon: <TrendingUp size={14} className="text-teal-400" />,
      render: s => s.benefit_monthly > 0 ? formatINR(s.benefit_monthly) : '-',
    },
    {
      label: t('scheme_onetime'),
      icon: <TrendingUp size={14} className="text-teal-400" />,
      render: s => s.benefit_onetime > 0 ? formatINR(s.benefit_onetime) : '-',
    },
    {
      label: t('results_first_year'),
      icon: <TrendingUp size={14} className="text-teal-400" />,
      render: s => {
        const annual = (s.benefit_monthly || 0) * 12 + (s.benefit_onetime || 0)
        return annual > 0 ? formatINR(annual) : '-'
      },
    },
    {
      label: t('scheme_processing'),
      icon: <Clock size={14} className="text-slate-400" />,
      render: s => `${s.processing_weeks} ${t('scheme_weeks')}`,
    },
    {
      label: t('scheme_approval'),
      icon: <CheckCircle size={14} className="text-teal-400" />,
      render: s => `${Math.round((s.approval_rate || 0) * 100)}%`,
    },
    {
      label: t('scheme_confidence'),
      icon: <CheckCircle size={14} className="text-slate-400" />,
      render: s => `${Math.round((s.confidence || 0) * 100)}%`,
    },
    {
      label: t('scheme_docs'),
      icon: <FileText size={14} className="text-slate-400" />,
      render: s => `${s.required_documents?.length || 0}`,
    },
  ]

  return (
    <div className="fixed inset-0 z-[200] flex items-end sm:items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative bg-dark-900 rounded-t-2xl sm:rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-fade-slide-up border border-dark-700"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 px-5 py-4 border-b border-dark-700 bg-dark-800 rounded-t-2xl flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">{t('compare_title')}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-dark-700 text-slate-400 hover:text-white transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label={t('scheme_close')}
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-4 py-4 overflow-x-auto">
          <table className="w-full text-sm">
            {/* Scheme names header */}
            <thead>
              <tr>
                <th className="text-left py-3 pr-3 text-xs text-slate-500 font-medium w-28" />
                {schemes.map(s => (
                  <th key={s.scheme_id} className="text-center py-3 px-2">
                    <div className="text-white font-semibold text-sm leading-tight">{s.scheme_name}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-dark-800/50' : ''}>
                  <td className="py-3 pr-3 text-xs text-slate-400 font-medium">
                    <div className="flex items-center gap-1.5">
                      {row.icon}
                      {row.label}
                    </div>
                  </td>
                  {schemes.map(s => {
                    const val = row.render(s)
                    return (
                      <td key={s.scheme_id} className="py-3 px-2 text-center text-white font-medium">
                        {val}
                      </td>
                    )
                  })}
                </tr>
              ))}
              {/* Why this scheme row */}
              <tr className="bg-dark-800/50">
                <td className="py-3 pr-3 text-xs text-slate-400 font-medium align-top">
                  {t('scheme_why')}
                </td>
                {schemes.map(s => (
                  <td key={s.scheme_id} className="py-3 px-2 text-xs text-slate-300 leading-relaxed">
                    {s.reason}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
