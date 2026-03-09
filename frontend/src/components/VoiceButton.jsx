import { useState, useRef, useCallback } from 'react'
import { Mic, MicOff } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { useTTS } from '../context/TTSContext'

// Use multilingual recognition — browsers will detect Hindi/English automatically
const STT_LANGS = {
  hi: 'hi-IN',
  en: 'en-IN',
}

export default function VoiceButton({ onTranscript, onInterim }) {
  const [recording, setRecording] = useState(false)
  const [error, setError] = useState(null)
  const [supported] = useState(() => 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window)
  const recognitionRef = useRef(null)
  const autoSendTimerRef = useRef(null)
  const { t, lang } = useLanguage()
  const { stop: stopTTS, speaking } = useTTS()

  const toggle = useCallback(() => {
    if (recording) {
      stop()
    } else {
      start()
    }
  }, [recording])

  function start() {
    if (speaking) stopTTS()

    setError(null)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError(t('voice_error'))
      return
    }

    const recognition = new SpeechRecognition()
    // Match the current UI language, but en-IN also recognizes Hindi/Hinglish well
    recognition.lang = STT_LANGS[lang] || 'en-IN'
    recognition.interimResults = true
    recognition.continuous = true
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          final += transcript
        } else {
          interim += transcript
        }
      }

      if (interim && onInterim) onInterim(interim)

      if (final) {
        onTranscript(final)
        if (autoSendTimerRef.current) clearTimeout(autoSendTimerRef.current)
        autoSendTimerRef.current = setTimeout(() => {
          stop()
        }, 1500)
      }
    }

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setError(t('voice_error'))
      } else if (event.error === 'no-speech') {
        setError(t('voice_no_speech'))
      } else if (event.error === 'network') {
        setError(t('error_network'))
      }
      setRecording(false)
    }

    recognition.onend = () => setRecording(false)

    recognitionRef.current = recognition
    recognition.start()
    setRecording(true)
  }

  function stop() {
    if (autoSendTimerRef.current) {
      clearTimeout(autoSendTimerRef.current)
      autoSendTimerRef.current = null
    }
    recognitionRef.current?.stop()
    setRecording(false)
  }

  if (!supported) return null

  return (
    <div className="flex flex-col items-center">
      <button
        onClick={toggle}
        className={`rounded-xl transition-all min-w-[56px] min-h-[56px] flex items-center justify-center focus:outline-2 focus:outline-teal-400 ${
          recording
            ? 'bg-red-500/20 text-red-400 ring-2 ring-red-500/50 animate-pulse-gentle'
            : 'bg-dark-600 text-slate-400 hover:text-teal-400 hover:bg-dark-500'
        }`}
        title={recording ? t('voice_stop') : t('voice_speak')}
        aria-label={recording ? t('voice_stop') : t('voice_speak')}
      >
        {recording ? <MicOff size={22} /> : <Mic size={22} />}
      </button>
      {error && (
        <span className="text-[10px] text-red-400 mt-1 text-center max-w-[120px]" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}
