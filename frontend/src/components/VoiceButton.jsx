import { useState, useRef } from 'react'
import { Mic, MicOff } from 'lucide-react'

export default function VoiceButton({ onTranscript }) {
  const [recording, setRecording] = useState(false)
  const [supported] = useState(() => 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window)
  const recognitionRef = useRef(null)

  function toggle() {
    if (recording) {
      stop()
    } else {
      start()
    }
  }

  function start() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.lang = 'hi-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      onTranscript(transcript)
      setRecording(false)
    }
    recognition.onerror = () => setRecording(false)
    recognition.onend = () => setRecording(false)

    recognitionRef.current = recognition
    recognition.start()
    setRecording(true)
  }

  function stop() {
    recognitionRef.current?.stop()
    setRecording(false)
  }

  if (!supported) return null

  return (
    <button
      onClick={toggle}
      className={`p-2.5 rounded-xl transition-all ${
        recording
          ? 'bg-red-500/20 text-red-400 ring-2 ring-red-500/50 animate-pulse-gentle'
          : 'bg-dark-600 text-slate-400 hover:text-teal-400 hover:bg-dark-500'
      }`}
      title={recording ? 'Stop recording' : 'Speak in Hindi/English'}
    >
      {recording ? <MicOff size={20} /> : <Mic size={20} />}
    </button>
  )
}
