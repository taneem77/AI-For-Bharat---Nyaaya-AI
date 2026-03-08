import { useState } from 'react'
import { Globe } from 'lucide-react'

const LANGUAGES = [
  { code: 'hi', label: 'Hindi', flag: 'HI' },
  { code: 'en', label: 'English', flag: 'EN' },
  { code: 'mr', label: 'Marathi', flag: 'MR' },
]

export default function LanguageToggle({ value = 'hi', onChange }) {
  const [open, setOpen] = useState(false)
  const current = LANGUAGES.find(l => l.code === value) || LANGUAGES[0]

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs bg-dark-700 hover:bg-dark-600 text-slate-300 px-2.5 py-1.5 rounded-lg border border-dark-600 transition-colors"
      >
        <Globe size={14} className="text-teal-400" />
        <span>{current.flag}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 bg-dark-800 border border-dark-600 rounded-lg overflow-hidden z-50 shadow-xl min-w-[120px]">
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              onClick={() => { onChange(lang.code); setOpen(false) }}
              className={`w-full text-left px-3 py-2 text-xs transition-colors flex items-center gap-2 ${
                lang.code === value
                  ? 'bg-teal-600/20 text-teal-300'
                  : 'text-slate-300 hover:bg-dark-700'
              }`}
            >
              <span className="font-medium">{lang.flag}</span>
              <span>{lang.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
