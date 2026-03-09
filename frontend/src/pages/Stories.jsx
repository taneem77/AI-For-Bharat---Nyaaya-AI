import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPin, CheckCircle, Clock, AlertTriangle, Lightbulb, Users, Loader } from 'lucide-react'
import Header from '../components/Header'
import { postStories } from '../api/client'
import { useLanguage } from '../context/LanguageContext'

const FALLBACK_STORIES = [
  {
    id: 1, name: 'Savitri D.', district: 'Pune', state: 'Maharashtra', age: '40-49',
    scheme: 'Widow Pension Scheme', status: 'approved', weeks: 8, approval_rate: 91,
    blockers: ['Death certificate had spelling mismatch with Aadhaar name'],
    tips: ['Get name corrected on death certificate BEFORE applying', 'Carry 3 photocopies of every document', 'Apply through Gram Sevak — faster than CSC'],
  },
  {
    id: 2, name: 'Kamla R.', district: 'Jaipur', state: 'Rajasthan', age: '50-59',
    scheme: 'Widow Pension Scheme', status: 'approved', weeks: 10, approval_rate: 87,
    blockers: ['BPL card had expired, Gram Sabha delayed verification'],
    tips: ['Renew BPL card first — it takes 2-3 weeks', 'Get the Sarpanch signature early', 'Follow up at BDO office every 2 weeks'],
  },
  {
    id: 3, name: 'Raju M.', district: 'Nagpur', state: 'Maharashtra', age: '30-39',
    scheme: 'Disability Allowance', status: 'approved', weeks: 7, approval_rate: 85,
    blockers: ['Private hospital disability cert was rejected'],
    tips: ['ONLY get certificate from Govt District Hospital', 'Medical board meets on fixed days — call ahead', 'Bring 2 passport photos + Aadhaar original'],
  },
  {
    id: 4, name: 'Balaji N.', district: 'Nashik', state: 'Maharashtra', age: '30-39',
    scheme: 'NREGA Employment Guarantee', status: 'approved', weeks: 3, approval_rate: 78,
    blockers: [],
    tips: ['Apply at Gram Panchayat office directly', 'Job Card is issued within 15 days', 'You choose which days to work'],
  },
  {
    id: 5, name: 'Reshma J.', district: 'Jaisalmer', state: 'Rajasthan', age: '40-49',
    scheme: 'National Family Benefit', status: 'rejected', weeks: 6, approval_rate: 72,
    blockers: ['Applied more than 1 year after death — missed deadline'],
    tips: ['CRITICAL: Apply within 12 months of death', 'This deadline is strictly enforced', 'Start the process immediately — don\'t wait'],
  },
  {
    id: 6, name: 'Priya S.', district: 'Lucknow', state: 'Uttar Pradesh', age: '30-39',
    scheme: 'PM Ujjwala Yojana (Free LPG)', status: 'approved', weeks: 4, approval_rate: 94,
    blockers: [],
    tips: ['Apply at nearest LPG distributor with BPL card', 'Free connection + first refill included', 'Subsidy comes directly to bank account via DBT'],
  },
]

export default function Stories() {
  const navigate = useNavigate()
  const { t } = useLanguage()
  const [filter, setFilter] = useState('all')
  const [stories, setStories] = useState(FALLBACK_STORIES)
  const [loading, setLoading] = useState(false)
  const [aiGenerated, setAiGenerated] = useState(false)
  const profile = JSON.parse(sessionStorage.getItem('nyaaya_profile') || '{}')
  const results = JSON.parse(sessionStorage.getItem('nyaaya_results') || '{}')

  useEffect(() => {
    if (!profile.state) return
    const eligible = results.eligible_schemes?.filter(s => s.eligible) ?? []
    const schemeIds = eligible.map(s => s.scheme_id)
    if (schemeIds.length === 0) return

    setLoading(true)
    postStories(profile.state, profile.district || '', schemeIds)
      .then(res => {
        if (res.stories && res.stories.length > 0) {
          const withIds = res.stories.map((s, i) => ({ ...s, id: `ai_${i}` }))
          setStories(withIds)
          setAiGenerated(true)
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const sorted = [...stories].sort((a, b) => {
    const aMatch = a.state === profile.state ? 1 : 0
    const bMatch = b.state === profile.state ? 1 : 0
    if (aMatch !== bMatch) return bMatch - aMatch
    return (b.approval_rate || 0) - (a.approval_rate || 0)
  })

  const filtered = filter === 'all'
    ? sorted
    : sorted.filter(s => s.status === filter)

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main id="main-content" className="flex-1 px-4 py-6 max-w-lg mx-auto w-full" role="main" aria-label={t('a11y_main')}>
        <div className="animate-fade-slide-up mb-4">
          <div className="flex items-center gap-2 mb-1">
            <Users size={20} className="text-teal-400" />
            <h2 className="text-xl font-bold text-white">{t('stories_title')}</h2>
          </div>
          <p className="text-sm text-slate-400">
            {aiGenerated ? t('stories_ai') : t('stories_real')}
            {profile.state && <span className="text-teal-400"> {t('stories_your_state')}: {profile.state}</span>}
          </p>
          {aiGenerated && (
            <span className="inline-block mt-1 text-[10px] bg-teal-600/20 text-teal-400 px-2 py-0.5 rounded-full">
              {t('powered_by')} Amazon Bedrock
            </span>
          )}
        </div>

        <div className="flex gap-2 mb-5 overflow-x-auto animate-fade-slide-up" role="tablist">
          {[
            { key: 'all', label: t('stories_all') },
            { key: 'approved', label: t('stories_approved') },
            { key: 'rejected', label: t('stories_rejected') },
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              role="tab"
              aria-selected={filter === f.key}
              className={`text-xs font-medium px-3 py-1.5 rounded-full whitespace-nowrap transition-colors min-h-[44px] focus:outline-2 focus:outline-teal-400 ${
                filter === f.key
                  ? 'bg-teal-600 text-white'
                  : 'bg-dark-700 text-slate-400 hover:bg-dark-600'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {loading && (
          <div className="flex items-center justify-center gap-2 py-8 text-slate-400">
            <Loader size={18} className="animate-spin" />
            <span className="text-sm">{t('stories_loading')}</span>
          </div>
        )}

        <div className="space-y-4">
          {filtered.map((story, i) => (
            <div
              key={story.id}
              className="animate-fade-slide-up bg-dark-800 rounded-2xl border border-dark-700 p-4"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">{story.name}</span>
                    <span className="text-[10px] text-slate-500">{story.age} yrs</span>
                  </div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <MapPin size={11} className="text-slate-500" />
                    <span className="text-xs text-slate-400">{story.district}, {story.state}</span>
                    {story.state === profile.state && (
                      <span className="text-[9px] bg-teal-600/20 text-teal-400 px-1.5 py-0.5 rounded-full ml-1">
                        {t('stories_your_state')}
                      </span>
                    )}
                  </div>
                </div>
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                  story.status === 'approved'
                    ? 'bg-teal-500/20 text-teal-300'
                    : 'bg-red-500/20 text-red-300'
                }`}>
                  {story.status === 'approved' ? t('stories_approved') : t('stories_rejected')}
                </span>
              </div>

              <div className="text-xs text-slate-300 mb-2">{story.scheme}</div>
              <div className="flex items-center gap-4 text-xs text-slate-500 mb-3">
                <span className="flex items-center gap-1">
                  <Clock size={11} /> {story.weeks} {t('scheme_weeks')}
                </span>
                {story.approval_rate && (
                  <span className="flex items-center gap-1">
                    <CheckCircle size={11} /> {story.approval_rate}% {t('scheme_approval')}
                  </span>
                )}
              </div>

              {story.blockers?.length > 0 && (
                <div className="mb-3">
                  <div className="flex items-center gap-1 mb-1">
                    <AlertTriangle size={12} className="text-amber-400" />
                    <span className="text-[10px] font-medium text-amber-400">{t('stories_blockers')}</span>
                  </div>
                  {story.blockers.map((b, j) => (
                    <p key={j} className="text-xs text-slate-400 pl-4">- {b}</p>
                  ))}
                </div>
              )}

              {story.tips?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1 mb-1">
                    <Lightbulb size={12} className="text-teal-400" />
                    <span className="text-[10px] font-medium text-teal-400">{t('stories_tips')}</span>
                  </div>
                  {story.tips.map((tip, j) => (
                    <p key={j} className="text-xs text-slate-300 pl-4 mb-0.5">- {tip}</p>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 space-y-3">
          <button
            onClick={() => navigate('/results')}
            className="w-full text-sm text-slate-500 hover:text-slate-300 py-2 transition-colors min-h-[44px] focus:outline-2 focus:outline-teal-400"
          >
            {t('stories_back')}
          </button>
        </div>
      </main>
    </div>
  )
}
