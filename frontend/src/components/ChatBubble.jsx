import { Volume2 } from 'lucide-react'
import { useTTS } from '../context/TTSContext'

export default function ChatBubble({ role, text, delay = 0, timestamp }) {
  const isBot = role === 'bot'
  const { speak, muted } = useTTS()

  return (
    <div
      className={`animate-fade-slide-up flex ${isBot ? 'justify-start' : 'justify-end'} mb-3`}
      style={{ animationDelay: `${delay}ms` }}
      role="listitem"
      aria-label={`${isBot ? 'Nyaaya' : 'You'}: ${text}`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed relative group ${
          isBot
            ? 'bg-white text-dark-900 rounded-bl-sm shadow-sm'
            : 'bg-[#DCF8C6] text-dark-900 rounded-br-sm shadow-sm'
        }`}
      >
        {/* Message tail */}
        <div className={`absolute top-0 w-3 h-3 ${
          isBot
            ? '-left-1.5 bg-white'
            : '-right-1.5 bg-[#DCF8C6]'
        }`} style={{
          clipPath: isBot
            ? 'polygon(100% 0, 100% 100%, 0 0)'
            : 'polygon(0 0, 100% 0, 0 100%)'
        }} />

        {text}

        {/* Timestamp + TTS replay */}
        <div className={`flex items-center gap-1.5 mt-1 ${isBot ? 'justify-start' : 'justify-end'}`}>
          {timestamp && (
            <span className="text-[10px] text-slate-500">{timestamp}</span>
          )}
          {isBot && !muted && (
            <button
              onClick={() => speak(text)}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-dark-200"
              aria-label="Replay message"
              title="Replay"
            >
              <Volume2 size={12} className="text-slate-400" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
