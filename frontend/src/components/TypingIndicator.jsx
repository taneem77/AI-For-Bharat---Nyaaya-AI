export default function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3 animate-fade-slide-up" role="status" aria-label="Typing">
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5 shadow-sm">
        <span className="typing-dot w-2 h-2 rounded-full bg-slate-400" />
        <span className="typing-dot w-2 h-2 rounded-full bg-slate-400" />
        <span className="typing-dot w-2 h-2 rounded-full bg-slate-400" />
      </div>
    </div>
  )
}
