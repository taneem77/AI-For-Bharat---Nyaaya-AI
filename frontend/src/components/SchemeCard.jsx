import { CheckCircle, XCircle, FileText, Clock, TrendingUp } from 'lucide-react'

export default function SchemeCard({ scheme, showDetails = false }) {
  const eligible = scheme.eligible

  return (
    <div className={`animate-fade-slide-up rounded-2xl border p-4 ${
      eligible
        ? 'bg-teal-900/20 border-teal-700/50'
        : 'bg-dark-800 border-dark-600'
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-white text-base">{scheme.scheme_name}</h3>
          <span className={`inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full ${
            eligible
              ? 'bg-teal-500/20 text-teal-300'
              : 'bg-dark-600 text-slate-400'
          }`}>
            {eligible ? 'Eligible' : 'Not Eligible'}
          </span>
        </div>
        <div className={`p-2 rounded-xl ${eligible ? 'bg-teal-600/20' : 'bg-dark-700'}`}>
          {eligible
            ? <CheckCircle size={22} className="text-teal-400" />
            : <XCircle size={22} className="text-slate-500" />}
        </div>
      </div>

      {/* Reason */}
      <p className="text-sm text-slate-300 leading-relaxed mb-3">{scheme.reason}</p>

      {/* Benefits */}
      {eligible && (
        <div className="flex flex-wrap gap-3 mb-3">
          {scheme.benefit_monthly > 0 && (
            <div className="flex items-center gap-1.5 text-sm">
              <TrendingUp size={14} className="text-teal-400" />
              <span className="text-teal-300 font-medium">{'\u20B9'}{scheme.benefit_monthly.toLocaleString()}/mo</span>
            </div>
          )}
          {scheme.benefit_onetime > 0 && (
            <div className="flex items-center gap-1.5 text-sm">
              <TrendingUp size={14} className="text-teal-400" />
              <span className="text-teal-300 font-medium">{'\u20B9'}{scheme.benefit_onetime.toLocaleString()} one-time</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 text-sm text-slate-400">
            <Clock size={14} />
            <span>{scheme.processing_weeks} weeks</span>
          </div>
        </div>
      )}

      {/* Confidence + Approval */}
      {eligible && (
        <div className="flex gap-4 mb-3">
          <div className="text-xs text-slate-400">
            Confidence: <span className="text-teal-300 font-medium">{Math.round(scheme.confidence * 100)}%</span>
          </div>
          <div className="text-xs text-slate-400">
            Approval rate: <span className="text-teal-300 font-medium">{Math.round(scheme.approval_rate * 100)}%</span>
          </div>
        </div>
      )}

      {/* Documents */}
      {showDetails && eligible && scheme.required_documents?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-dark-600">
          <div className="flex items-center gap-1.5 mb-2">
            <FileText size={14} className="text-slate-400" />
            <span className="text-xs font-medium text-slate-400">Required Documents</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {scheme.required_documents.map((doc) => (
              <span key={doc} className="text-xs bg-dark-700 text-slate-300 px-2 py-1 rounded-lg">
                {doc.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
