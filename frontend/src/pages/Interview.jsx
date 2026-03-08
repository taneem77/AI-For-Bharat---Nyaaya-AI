import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send } from 'lucide-react'
import Header from '../components/Header'
import ChatBubble from '../components/ChatBubble'
import TypingIndicator from '../components/TypingIndicator'
import ProgressBar from '../components/ProgressBar'
import VoiceButton from '../components/VoiceButton'
import { postInterview, postEvaluate } from '../api/client'

function generateSessionId() {
  return 'sess_' + crypto.randomUUID().slice(0, 12)
}

const GREETING = 'Namaste! Main Nyaaya hoon. Aapki kya situation hai? Hindi, English, Hinglish — jo bhi comfortable ho, bataiye.'

export default function Interview() {
  const navigate = useNavigate()
  const [sessionId] = useState(() => {
    const existing = sessionStorage.getItem('nyaaya_session')
    if (existing) return existing
    const id = generateSessionId()
    sessionStorage.setItem('nyaaya_session', id)
    return id
  })
  const [messages, setMessages] = useState([{ role: 'bot', text: GREETING }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [extractedProfile, setExtractedProfile] = useState({})
  const [complete, setComplete] = useState(false)
  const [turn, setTurn] = useState(0)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend(text) {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')

    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setLoading(true)

    try {
      const res = await postInterview(sessionId, msg)
      setTurn(res.turn)

      // Merge extracted data
      if (res.extracted_so_far) {
        setExtractedProfile(prev => ({ ...prev, ...res.extracted_so_far }))
      }

      setMessages(prev => [...prev, { role: 'bot', text: res.next_question }])

      if (res.interview_complete) {
        setComplete(true)
        // Auto-evaluate after a short pause
        setTimeout(() => runEvaluation(res.extracted_so_far), 1200)
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'bot', text: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  async function runEvaluation(profile) {
    // Build the evaluate request from extracted profile
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
      // Store results and navigate
      sessionStorage.setItem('nyaaya_results', JSON.stringify(results))
      sessionStorage.setItem('nyaaya_profile', JSON.stringify(evalProfile))
      navigate('/results')
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'bot', text: 'Results ready! But there was a small issue loading them. Let me try the evaluation directly.' },
      ])
    }
  }

  function handleQuickAction(text) {
    handleSend(text)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickPrompts = turn === 0 ? [
    'Mera husband guzar gaye',
    'I have a disability',
    'Mujhe rozgar chahiye',
    'Main ek kisan hoon',
  ] : null

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <ProgressBar fields={extractedProfile} />

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-lg mx-auto">
          {messages.map((m, i) => (
            <ChatBubble key={i} role={m.role} text={m.text} delay={m.role === 'bot' ? 100 : 0} />
          ))}

          {loading && <TypingIndicator />}

          {/* Quick prompts — only on first turn */}
          {quickPrompts && !loading && turn === 0 && (
            <div className="flex flex-wrap gap-2 mt-2 mb-4 animate-fade-slide-up" style={{ animationDelay: '300ms' }}>
              {quickPrompts.map((q) => (
                <button
                  key={q}
                  onClick={() => handleQuickAction(q)}
                  className="text-xs bg-dark-700 hover:bg-dark-600 text-slate-300 px-3 py-1.5 rounded-full border border-dark-600 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Complete state */}
          {complete && (
            <div className="animate-fade-slide-up text-center py-6">
              <div className="text-teal-400 font-medium mb-2">Checking your eligibility...</div>
              <div className="w-8 h-8 border-2 border-teal-400 border-t-transparent rounded-full animate-spin mx-auto" />
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </div>

      {/* Input bar */}
      {!complete && (
        <div className="border-t border-dark-700 bg-dark-900 px-4 py-3">
          <div className="max-w-lg mx-auto flex items-end gap-2">
            <VoiceButton onTranscript={(text) => setInput(prev => prev + text)} />
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type or speak in Hindi/English..."
                rows={1}
                className="w-full bg-dark-700 text-slate-200 placeholder-slate-500 rounded-xl px-4 py-2.5 text-sm resize-none border border-dark-600 focus:border-teal-600 focus:outline-none transition-colors"
              />
            </div>
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="p-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-40 disabled:hover:bg-teal-600 text-white transition-colors"
            >
              <Send size={20} />
            </button>
          </div>
          <div className="max-w-lg mx-auto text-center mt-1.5">
            <span className="text-[10px] text-slate-600">Turn {turn + 1} | Session: {sessionId.slice(-8)}</span>
          </div>
        </div>
      )}
    </div>
  )
}
