import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageCircle, Shield, Zap, Users, ChevronRight } from 'lucide-react'
import Header from '../components/Header'
import { useLanguage } from '../context/LanguageContext'

const FEATURES = [
  { icon: MessageCircle, key: 'feat_talk', descKey: 'feat_talk_desc' },
  { icon: Shield, key: 'feat_zero', descKey: 'feat_zero_desc' },
  { icon: Zap, key: 'feat_instant', descKey: 'feat_instant_desc' },
  { icon: Users, key: 'feat_peer', descKey: 'feat_peer_desc' },
]

const IMPACT_STATS = [
  { value: '19', key: 'stat_schemes' },
  { value: '36', key: 'stat_states' },
  { value: '24/7', key: 'stat_available' },
]

export default function Welcome() {
  const navigate = useNavigate()
  const { t } = useLanguage()

  useEffect(() => {
    sessionStorage.removeItem('nyaaya_session')
    sessionStorage.removeItem('nyaaya_results')
    sessionStorage.removeItem('nyaaya_profile')
  }, [])

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main id="main-content" className="flex-1 flex flex-col items-center px-4 pt-6 pb-6 max-w-lg mx-auto w-full" role="main" aria-label={t('a11y_main')}>
        {/* Hero */}
        <div className="text-center mb-6 animate-fade-slide-up">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-teal-600/30 to-teal-800/30 flex items-center justify-center mx-auto mb-4 border border-teal-600/20">
            <Shield size={36} className="text-teal-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {t('welcome_hero_1')}<br />
            <span className="text-teal-400">{t('welcome_hero_2')}</span>
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xs mx-auto">
            {t('tagline_sub')}
          </p>
        </div>

        {/* Impact stats */}
        <div className="animate-fade-slide-up flex justify-center gap-6 mb-6 w-full" style={{ animationDelay: '100ms' }}>
          {IMPACT_STATS.map(({ value, key }) => (
            <div key={key} className="text-center">
              <div className="text-xl font-bold text-teal-400">{value}</div>
              <div className="text-[10px] text-slate-500 mt-0.5">{t(key)}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <div className="grid grid-cols-2 gap-3 w-full mb-6 animate-fade-slide-up" style={{ animationDelay: '200ms' }}>
          {FEATURES.map(({ icon: Icon, key, descKey }) => (
            <div key={key} className="bg-dark-800 rounded-xl p-3 border border-dark-700 hover:border-teal-700/50 transition-colors">
              <Icon size={20} className="text-teal-400 mb-2" />
              <p className="text-sm font-medium text-white">{t(key)}</p>
              <p className="text-xs text-slate-400 mt-0.5">{t(descKey)}</p>
            </div>
          ))}
        </div>

        {/* How it works */}
        <div className="w-full mb-6 animate-fade-slide-up" style={{ animationDelay: '300ms' }}>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            {t('welcome_how')}
          </h3>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-600/20 text-teal-400 font-bold text-[10px]">1</span>
            <span>{t('welcome_step1')}</span>
            <ChevronRight size={14} className="text-dark-600" />
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-600/20 text-teal-400 font-bold text-[10px]">2</span>
            <span>{t('welcome_step2')}</span>
            <ChevronRight size={14} className="text-dark-600" />
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-600/20 text-teal-400 font-bold text-[10px]">3</span>
            <span>{t('welcome_step3')}</span>
          </div>
        </div>

        {/* CTA */}
        <button
          onClick={() => navigate('/interview')}
          className="w-full bg-teal-600 hover:bg-teal-500 text-white font-semibold py-3.5 rounded-xl transition-all text-base shadow-lg shadow-teal-600/20 hover:shadow-teal-500/30 animate-fade-slide-up min-h-[44px] focus:outline-2 focus:outline-teal-400"
          style={{ animationDelay: '400ms' }}
        >
          {t('welcome_cta')}
        </button>
        <p className="text-xs text-slate-500 mt-3 text-center">
          {t('welcome_cta_sub')}
        </p>

        {/* AWS badge */}
        <div className="mt-6 flex items-center gap-2 text-[10px] text-slate-600">
          <span>{t('powered_by')}</span>
          <span className="font-semibold text-slate-500">Amazon Bedrock</span>
          <span className="text-dark-600">|</span>
          <span className="font-semibold text-slate-500">DynamoDB</span>
          <span className="text-dark-600">|</span>
          <span className="font-semibold text-slate-500">Lambda</span>
        </div>
      </main>
    </div>
  )
}
