import { Routes, Route } from 'react-router-dom'
import Welcome from './pages/Welcome'
import Interview from './pages/Interview'
import Results from './pages/Results'
import Strategy from './pages/Strategy'
import Stories from './pages/Stories'

export default function App() {
  return (
    <div className="min-h-screen bg-dark-950 text-slate-200">
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
