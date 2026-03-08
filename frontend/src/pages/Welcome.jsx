import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageCircle, Shield, Zap, Globe, Users, IndianRupee, ChevronRight } from 'lucide-react'
import Header from '../components/Header'
import LanguageToggle from '../components/LanguageToggle'

const features = [
  { icon: MessageCircle, title: 'Talk naturally', titleHi: 'Apni bhasha mein baat karein', desc: 'Hindi, English, or Hinglish — just tell your story', descHi: 'Hindi, English, ya Hinglish — apni kahani bataiye' },
  { icon: Shield, title: 'Zero guesswork', titleHi: 'Sahi jaankari', desc: 'Deterministic rules ensure accurate eligibility', descHi: 'Pakka rules se sahi eligibility check hoti hai' },
  { icon: Zap, title: 'Instant strategy', titleHi: 'Turant yojana', desc: 'Week-by-week plan to get your benefits faster', descHi: 'Hafte-dar-hafte plan se jaldi benefit milega' },
  { icon: Users, title: 'Peer stories', titleHi: 'Logon ki kahaniyaan', desc: 'See how people in your district got approved', descHi: 'Dekhiye aapke jile ke logon ko kaise mila' },
]

const IMPACT_STATS = [
  { value: '6', label: 'Schemes', labelHi: 'Yojanayen' },
  { value: '3', label: 'States', labelHi: 'Rajya' },
  { value: '24/7', label: 'Available', labelHi: 'Uplabdh' },
]

export default function Welcome() {
  const navigate = useNavigate()
  const [lang, setLang] = useState('en')
  const hi = lang === 'hi' || lang === 'mr'

  // Clear previous session on landing
  useEffect(() => {
    sessionStorage.removeItem('nyaaya_session')
    sessionStorage.removeItem('nyaaya_results')
    sessionStorage.removeItem('nyaaya_profile')
  }, [])

  return (
    <div className="flex flex-col min-h-screen">
      <Header rightSlot={<LanguageToggle value={lang} onChange={setLang} />} />
      <main className="flex-1 flex flex-col items-center px-4 pt-6 pb-6 max-w-lg mx-auto w-full">
        {/* Hero */}
        <div className="text-center mb-6 animate-fade-slide-up">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-teal-600/30 to-teal-800/30 flex items-center justify-center mx-auto mb-4 border border-teal-600/20">
            <Shield size={36} className="text-teal-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {hi ? (
              <>Aapke welfare benefits,<br /><span className="text-teal-400">aasan.</span></>
            ) : (
              <>Your welfare benefits,<br /><span className="text-teal-400">simplified.</span></>
            )}
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xs mx-auto">
            {hi
              ? 'Apni situation bataiye apne shabdon mein. Hum har sarkari yojana dhundhenge jismein aap eligible hain.'
              : 'Tell us about your situation in your own words. We\'ll find every government scheme you qualify for.'
            }
          </p>
        </div>

        {/* Impact stats */}
        <div className="animate-fade-slide-up flex justify-center gap-6 mb-6 w-full" style={{ animationDelay: '100ms' }}>
          {IMPACT_STATS.map(({ value, label, labelHi }) => (
            <div key={label} className="text-center">
              <div className="text-xl font-bold text-teal-400">{value}</div>
              <div className="text-[10px] text-slate-500 mt-0.5">{hi ? labelHi : label}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <div className="grid grid-cols-2 gap-3 w-full mb-6 animate-fade-slide-up" style={{ animationDelay: '200ms' }}>
          {features.map(({ icon: Icon, title, titleHi, desc, descHi }) => (
            <div key={title} className="bg-dark-800 rounded-xl p-3 border border-dark-700 hover:border-teal-700/50 transition-colors">
              <Icon size={20} className="text-teal-400 mb-2" />
              <p className="text-sm font-medium text-white">{hi ? titleHi : title}</p>
              <p className="text-xs text-slate-400 mt-0.5">{hi ? descHi : desc}</p>
            </div>
          ))}
        </div>

        {/* How it works */}
        <div className="w-full mb-6 animate-fade-slide-up" style={{ animationDelay: '300ms' }}>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            {hi ? 'Kaise kaam karta hai' : 'How it works'}
          </h3>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-600/20 text-teal-400 font-bold text-[10px]">1</span>
            <span>{hi ? 'Apni kahani bataiye' : 'Tell your story'}</span>
            <ChevronRight size={14} className="text-dark-600" />
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-600/20 text-teal-400 font-bold text-[10px]">2</span>
            <span>{hi ? 'AI check karega' : 'AI checks eligibility'}</span>
            <ChevronRight size={14} className="text-dark-600" />
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-600/20 text-teal-400 font-bold text-[10px]">3</span>
            <span>{hi ? 'Plan milega' : 'Get your plan'}</span>
          </div>
        </div>

        {/* CTA */}
        <button
          onClick={() => navigate('/interview')}
          className="w-full bg-teal-600 hover:bg-teal-500 text-white font-semibold py-3.5 rounded-xl transition-all text-base shadow-lg shadow-teal-600/20 hover:shadow-teal-500/30 animate-fade-slide-up"
          style={{ animationDelay: '400ms' }}
        >
          {hi ? 'Interview Shuru Karein' : 'Start My Interview'}
        </button>
        <p className="text-xs text-slate-500 mt-3 text-center">
          {hi ? '2-3 minute lagenge. Bolein ya type karein.' : 'Takes 2-3 minutes. Speak or type in any language.'}
        </p>

        {/* AWS badge */}
        <div className="mt-6 flex items-center gap-2 text-[10px] text-slate-600">
          <span>Powered by</span>
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
