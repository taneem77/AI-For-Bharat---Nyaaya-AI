import { Routes, Route } from 'react-router-dom'
import { useLanguage } from './context/LanguageContext'
import Welcome from './pages/Welcome'
import Interview from './pages/Interview'
import Results from './pages/Results'
import Strategy from './pages/Strategy'
import Stories from './pages/Stories'

export default function App() {
  const { t } = useLanguage()

  return (
    <div className="min-h-screen bg-dark-950 text-slate-200 text-base leading-relaxed">
      {/* Skip to content — a11y */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:bg-teal-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg focus:outline-2 focus:outline-teal-400"
      >
        {t('a11y_skip')}
      </a>

      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route path="/interview" element={<Interview />} />
        <Route path="/results" element={<Results />} />
        <Route path="/strategy" element={<Strategy />} />
        <Route path="/stories" element={<Stories />} />
      </Routes>
    </div>
  )
}
