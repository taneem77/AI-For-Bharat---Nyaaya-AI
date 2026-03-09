import { createContext, useContext, useState, useCallback } from 'react'
import en from '../locales/en.json'
import hi from '../locales/hi.json'

const strings = { en, hi }

const LanguageContext = createContext()

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('nyaaya_lang') || 'hi')

  const toggleLang = useCallback(() => {
    setLang(prev => {
      const next = prev === 'hi' ? 'en' : 'hi'
      localStorage.setItem('nyaaya_lang', next)
      return next
    })
  }, [])

  const changeLang = useCallback((newLang) => {
    setLang(newLang)
    localStorage.setItem('nyaaya_lang', newLang)
  }, [])

  const t = useCallback((key, params) => {
    let str = strings[lang]?.[key] || strings.en[key] || key
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        str = str.replace(`{${k}}`, v)
      })
    }
    return str
  }, [lang])

  // Format Indian numbers (₹5,00,000)
  const formatINR = useCallback((num) => {
    if (num == null) return '0'
    return new Intl.NumberFormat('en-IN').format(num)
  }, [])

  return (
    <LanguageContext.Provider value={{ lang, setLang: changeLang, toggleLang, t, formatINR }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
