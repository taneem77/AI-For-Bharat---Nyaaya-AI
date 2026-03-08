export default function ChatBubble({ role, text, delay = 0 }) {
  const isBot = role === 'bot'

  return (
    <div
      className={`animate-fade-slide-up flex ${isBot ? 'justify-start' : 'justify-end'} mb-3`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isBot
            ? 'bg-dark-700 text-slate-200 rounded-bl-md'
            : 'bg-teal-700 text-white rounded-br-md'
        }`}
      >
        {text}
      </div>
    </div>
  )
}
