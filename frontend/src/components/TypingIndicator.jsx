export default function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3 animate-fade-slide-up">
      <div className="bg-dark-700 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1.5">
        <span className="typing-dot w-2 h-2 rounded-full bg-teal-400" />
        <span className="typing-dot w-2 h-2 rounded-full bg-teal-400" />
        <span className="typing-dot w-2 h-2 rounded-full bg-teal-400" />
      </div>
    </div>
  )
}
