import { useNavigate, useLocation } from 'react-router-dom'
import { Scale, ArrowLeft, Volume2, VolumeX } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { useTTS } from '../context/TTSContext'

export default function Header({ whatsappMode = false }) {
  const navigate = useNavigate()
  const location = useLocation()
  const isHome = location.pathname === '/'
  const { lang, toggleLang, t } = useLanguage()
  const { muted, toggleMute } = useTTS()

  const bgClass = whatsappMode
    ? 'bg-transparent'
    : 'sticky top-0 z-50 bg-dark-900/80 backdrop-blur-md border-b border-dark-700'

  const btnClass = whatsappMode
    ? 'bg-white/10 hover:bg-white/20 text-white'
    : 'bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-teal-400'

  return (
    <header
      className={bgClass}
      role="banner"
      aria-label={t('a11y_nav')}
    >
      <div className="max-w-lg mx-auto flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          {!isHome && (
            <button
              onClick={() => navigate(-1)}
              className={`p-1 rounded-lg transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center focus:outline-2 focus:outline-teal-400 ${
                whatsappMode ? 'hover:bg-white/10 text-white' : 'hover:bg-dark-700 text-slate-400'
              }`}
              aria-label="Go back"
            >
              <ArrowLeft size={20} />
            </button>
          )}
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => navigate('/')}
            role="link"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && navigate('/')}
            aria-label="Nyaaya.ai home"
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${whatsappMode ? 'bg-white/20' : 'bg-teal-600'}`}>
              <Scale size={18} className="text-white" />
            </div>
            <span className="font-bold text-lg text-white">
              Nyaaya<span className={whatsappMode ? 'text-teal-200' : 'text-teal-400'}>.ai</span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleMute}
            className={`p-2 rounded-lg transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center focus:outline-2 focus:outline-teal-400 ${btnClass}`}
            aria-label={muted ? t('tts_unmute') : t('tts_mute')}
            title={muted ? t('tts_unmute') : t('tts_mute')}
          >
            {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>

          <button
            onClick={toggleLang}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors min-h-[44px] flex items-center focus:outline-2 focus:outline-teal-400 ${
              whatsappMode
                ? 'bg-white/10 hover:bg-white/20 text-white border-white/20'
                : 'bg-dark-700 hover:bg-dark-600 text-teal-400 border-dark-600'
            }`}
            aria-label={`Switch to ${lang === 'hi' ? 'English' : 'Hindi'}`}
          >
            {lang === 'hi' ? 'En' : '\u0939\u093F\u0902'}
          </button>
        </div>
      </div>
    </header>
  )
}
