import { useNavigate, useLocation } from 'react-router-dom'
import { Scale, ArrowLeft } from 'lucide-react'

export default function Header({ rightSlot }) {
  const navigate = useNavigate()
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <header className="sticky top-0 z-50 bg-dark-900/80 backdrop-blur-md border-b border-dark-700">
      <div className="max-w-lg mx-auto flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          {!isHome && (
            <button onClick={() => navigate(-1)} className="p-1 rounded-lg hover:bg-dark-700 transition-colors">
              <ArrowLeft size={20} className="text-slate-400" />
            </button>
          )}
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center">
              <Scale size={18} className="text-white" />
            </div>
            <span className="font-bold text-lg text-white">Nyaaya<span className="text-teal-400">.ai</span></span>
          </div>
        </div>
        {rightSlot && <div>{rightSlot}</div>}
      </div>
    </header>
  )
}
