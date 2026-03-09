import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'

const TTSContext = createContext()

// Pick the best voice for a given language
function getBestVoice(lang) {
  const voices = window.speechSynthesis?.getVoices() || []
  const langPrefix = lang === 'hi' ? 'hi' : 'en'
  const regionCode = lang === 'hi' ? 'hi-IN' : 'en-IN'

  // Prefer Google voices (higher quality), then any matching voice
  const candidates = voices.filter(v => v.lang.startsWith(langPrefix))

  // 1. Exact region + Google
  const googleRegion = candidates.find(v => v.lang === regionCode && v.name.includes('Google'))
  if (googleRegion) return googleRegion

  // 2. Any Google voice for this language
  const google = candidates.find(v => v.name.includes('Google'))
  if (google) return google

  // 3. Exact region match
  const region = candidates.find(v => v.lang === regionCode)
  if (region) return region

  // 4. Any voice for this language
  if (candidates.length > 0) return candidates[0]

  // 5. Fallback — let browser pick
  return null
}

export function TTSProvider({ children }) {
  const [muted, setMuted] = useState(() => localStorage.getItem('nyaaya_tts_muted') === 'true')
  const [speaking, setSpeaking] = useState(false)
  const [voicesLoaded, setVoicesLoaded] = useState(false)
  const utteranceRef = useRef(null)

  // Voices load asynchronously in most browsers
  useEffect(() => {
    function onVoicesChanged() {
      setVoicesLoaded(true)
    }
    window.speechSynthesis?.addEventListener?.('voiceschanged', onVoicesChanged)
    // Try loading immediately (some browsers have them ready)
    if (window.speechSynthesis?.getVoices()?.length > 0) {
      setVoicesLoaded(true)
    }
    return () => window.speechSynthesis?.removeEventListener?.('voiceschanged', onVoicesChanged)
  }, [])

  const speak = useCallback((text, lang = 'hi') => {
    if (muted || !window.speechSynthesis || !text) return

    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)

    // Detect language from text content — if mostly ASCII, use English
    const hasDevanagari = /[\u0900-\u097F]/.test(text)
    const effectiveLang = hasDevanagari ? 'hi' : lang

    const voice = getBestVoice(effectiveLang)
    if (voice) {
      utterance.voice = voice
      utterance.lang = voice.lang
    } else {
      utterance.lang = effectiveLang === 'hi' ? 'hi-IN' : 'en-IN'
    }

    utterance.rate = 0.95
    utterance.pitch = 1.0
    utterance.onstart = () => setSpeaking(true)
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    utteranceRef.current = utterance
    window.speechSynthesis.speak(utterance)
  }, [muted, voicesLoaded])

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel()
    setSpeaking(false)
  }, [])

  const toggleMute = useCallback(() => {
    setMuted(prev => {
      const next = !prev
      localStorage.setItem('nyaaya_tts_muted', String(next))
      if (next) window.speechSynthesis?.cancel()
      return next
    })
  }, [])

  return (
    <TTSContext.Provider value={{ muted, speaking, speak, stop, toggleMute }}>
      {children}
    </TTSContext.Provider>
  )
}

export function useTTS() {
  const ctx = useContext(TTSContext)
  if (!ctx) throw new Error('useTTS must be used within TTSProvider')
  return ctx
}
