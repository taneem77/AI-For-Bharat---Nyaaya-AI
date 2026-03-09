import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send } from 'lucide-react'
import Header from '../components/Header'
import ChatBubble from '../components/ChatBubble'
import TypingIndicator from '../components/TypingIndicator'
import ProgressBar from '../components/ProgressBar'
import VoiceButton from '../components/VoiceButton'
import { postInterview, postEvaluate } from '../api/client'
import { useLanguage } from '../context/LanguageContext'
import { useTTS } from '../context/TTSContext'

function generateSessionId() {
  return 'sess_' + crypto.randomUUID().slice(0, 12)
}

function getTimestamp() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function Interview() {
  const navigate = useNavigate()
  const { t, lang } = useLanguage()
  const { speak } = useTTS()
  const [sessionId] = useState(() => {
    const existing = sessionStorage.getItem('nyaaya_session')
    if (existing) return existing
    const id = generateSessionId()
    sessionStorage.setItem('nyaaya_session', id)
    return id
  })
  const [messages, setMessages] = useState(() => [
    { role: 'bot', text: t('interview_greeting'), timestamp: getTimestamp(), isGreeting: true }
  ])
  const [input, setInput] = useState('')
  const [interimText, setInterimText] = useState('')
  const [loading, setLoading] = useState(false)
  const [extractedProfile, setExtractedProfile] = useState({})
  const [complete, setComplete] = useState(false)
  const [turn, setTurn] = useState(0)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Speak the first greeting
  useEffect(() => {
    if (messages.length === 1 && messages[0].role === 'bot') {
      speak(messages[0].text)
    }
  }, [])

  // Update greeting when language changes (only if no turns yet)
  useEffect(() => {
    if (turn === 0) {
      setMessages(prev => {
        if (prev.length === 1 && prev[0].isGreeting) {
          return [{ ...prev[0], text: t('interview_greeting') }]
        }
        return prev
      })
    }
  }, [lang])

  async function handleSend(text) {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setInterimText('')

    setMessages(prev => [...prev, { role: 'user', text: msg, timestamp: getTimestamp() }])
    setLoading(true)

    try {
      const res = await postInterview(sessionId, msg, lang)
      setTurn(res.turn)

      if (res.extracted_so_far) {
        setExtractedProfile(prev => ({ ...prev, ...res.extracted_so_far }))
      }

      const botMsg = { role: 'bot', text: res.next_question, timestamp: getTimestamp() }
      setMessages(prev => [...prev, botMsg])
      speak(res.next_question)

      if (res.interview_complete) {
        setComplete(true)
        setTimeout(() => runEvaluation(res.extracted_so_far), 1200)
      }
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'bot', text: t('interview_error'), timestamp: getTimestamp() },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  async function runEvaluation(profile) {
    const evalProfile = {
      age: profile.age ?? 30,
      income: profile.income ?? 10000,
      marital_status: profile.marital_status ?? 'single',
      dependents: profile.dependents ?? 0,
      state: profile.state ?? 'Maharashtra',
      district: profile.district ?? 'Mumbai',
      has_disability_cert: profile.has_disability_cert ?? false,
      disability_percentage: profile.disability_percentage ?? null,
      life_event: profile.life_event ?? 'none',
      is_rural: profile.is_rural ?? true,
      has_aadhaar: profile.has_aadhaar ?? true,
    }

    try {
      const results = await postEvaluate(evalProfile)
      sessionStorage.setItem('nyaaya_results', JSON.stringify(results))
      sessionStorage.setItem('nyaaya_profile', JSON.stringify(evalProfile))
      navigate('/results')
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'bot', text: t('interview_error'), timestamp: getTimestamp() },
      ])
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const displayValue = interimText || input

  const quickPrompts = turn === 0 ? [
    { key: 'quick_widow', text: t('quick_widow') },
    { key: 'quick_disability', text: t('quick_disability') },
    { key: 'quick_employment', text: t('quick_employment') },
    { key: 'quick_farmer', text: t('quick_farmer') },
  ] : null

  return (
    <div className="flex flex-col h-screen">
      {/* WhatsApp-style green header */}
      <div className="sticky top-0 z-50 bg-[#075E54] shadow-md">
        <Header whatsappMode />
      </div>

      <ProgressBar fields={extractedProfile} />

      {/* Chat area with WhatsApp background */}
      <div
        className="flex-1 overflow-y-auto px-4 py-4 whatsapp-bg"
        role="list"
        aria-label={t('a11y_main')}
        id="main-content"
      >
        <div className="max-w-lg mx-auto">
          {messages.map((m, i) => (
            <ChatBubble
              key={i}
              role={m.role}
              text={m.text}
              delay={m.role === 'bot' ? 100 : 0}
              timestamp={m.timestamp}
            />
          ))}

          {loading && <TypingIndicator />}

          {quickPrompts && !loading && turn === 0 && (
            <div className="flex flex-wrap gap-2 mt-2 mb-4 animate-fade-slide-up" style={{ animationDelay: '300ms' }}>
              {quickPrompts.map((q) => (
                <button
                  key={q.key}
                  onClick={() => handleSend(q.text)}
                  className="text-xs bg-white hover:bg-slate-50 text-dark-900 px-3 py-1.5 rounded-full border border-slate-200 transition-colors shadow-sm min-h-[44px] focus:outline-2 focus:outline-teal-400"
                >
                  {q.text}
                </button>
              ))}
            </div>
          )}

          {complete && (
            <div className="animate-fade-slide-up text-center py-6">
              <div className="text-teal-600 font-medium mb-2">{t('interview_checking')}</div>
              <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </div>

      {/* WhatsApp-style input bar */}
      {!complete && (
        <div className="bg-[#f0f0f0] border-t border-slate-200 px-3 py-2">
          <div className="max-w-lg mx-auto flex items-end gap-2">
            <VoiceButton
              onTranscript={(text) => {
                setInput(prev => prev + text)
                setInterimText('')
              }}
              onInterim={(text) => setInterimText(text)}
            />
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={displayValue}
                onChange={(e) => {
                  setInput(e.target.value)
                  setInterimText('')
                }}
                onKeyDown={handleKeyDown}
                placeholder={t('interview_placeholder')}
                rows={1}
                className="w-full bg-white text-dark-900 placeholder-slate-400 rounded-2xl px-4 py-2.5 text-sm resize-none border border-slate-200 focus:border-teal-500 focus:outline-none transition-colors shadow-sm"
                aria-label={t('interview_placeholder')}
              />
            </div>
            {displayValue.trim() ? (
              <button
                onClick={() => handleSend()}
                disabled={loading}
                className="p-2.5 rounded-full bg-[#075E54] hover:bg-[#064E46] disabled:opacity-40 text-white transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center focus:outline-2 focus:outline-teal-400"
                aria-label="Send message"
              >
                <Send size={20} />
              </button>
            ) : null}
          </div>
          <div className="max-w-lg mx-auto text-center mt-1">
            <span className="text-[10px] text-slate-400">
              {t('interview_turn')} {turn + 1} | {t('interview_session')}: {sessionId.slice(-8)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
