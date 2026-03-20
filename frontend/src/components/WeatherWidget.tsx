import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { useStore } from '../store/useStore'

const WEATHER_ICONS: Record<string, string> = {
  '01d': '☀️', '01n': '🌙',
  '02d': '⛅', '02n': '⛅',
  '03d': '☁️', '03n': '☁️',
  '04d': '☁️', '04n': '☁️',
  '09d': '🌧️', '09n': '🌧️',
  '10d': '🌦️', '10n': '🌧️',
  '11d': '⛈️', '11n': '⛈️',
  '13d': '❄️', '13n': '❄️',
  '50d': '🌫️', '50n': '🌫️',
}

export default function WeatherWidget() {
  const { weather, setWeather } = useStore()

  useEffect(() => {
    fetchWeather()
    const interval = setInterval(fetchWeather, 30 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  async function fetchWeather() {
    try {
      const res = await fetch('/api/weather')
      if (res.ok) {
        const data = await res.json()
        if (data.temp !== undefined) setWeather(data)
      }
    } catch (e) {
      // Weather API not configured
    }
  }

  if (!weather) {
    return (
      <div className="text-slate-500 text-sm">
        <div className="text-2xl">🌤️</div>
        <div>--°C</div>
      </div>
    )
  }

  const icon = WEATHER_ICONS[weather.icon] || '🌤️'

  return (
    <motion.div
      className="text-right"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="text-3xl">{icon}</div>
      <div className="text-white font-bold text-xl">{weather.temp}°C</div>
      <div className="text-slate-400 text-xs">{weather.description}</div>
      <div className="text-slate-500 text-xs">{weather.city}</div>
    </motion.div>
  )
}
