import { useEffect } from 'react'
import { useStore } from '../store/useStore'

const DAYS_JA = ['日', '月', '火', '水', '木', '金', '土']
const MONTHS_JA = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

export default function ClockWidget() {
  const { currentTime, setCurrentTime, setNightMode } = useStore()

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      setCurrentTime(now)
      setNightMode(now.getHours() >= 22 || now.getHours() < 6)
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const hours = currentTime.getHours().toString().padStart(2, '0')
  const minutes = currentTime.getMinutes().toString().padStart(2, '0')
  const seconds = currentTime.getSeconds().toString().padStart(2, '0')
  const day = DAYS_JA[currentTime.getDay()]
  const month = MONTHS_JA[currentTime.getMonth()]
  const date = currentTime.getDate()

  return (
    <div className="text-center">
      <div className="flex items-baseline justify-center gap-1">
        <span className="font-mono font-bold text-white" style={{ fontSize: '3.5rem', lineHeight: 1 }}>
          {hours}:{minutes}
        </span>
        <span className="font-mono text-slate-400" style={{ fontSize: '1.5rem' }}>
          {seconds}
        </span>
      </div>
      <div className="text-slate-400 text-sm mt-1">
        {month}{date}日（{day}）
      </div>
    </div>
  )
}
