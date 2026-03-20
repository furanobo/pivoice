import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Settings } from 'lucide-react'
import ClockWidget from './components/ClockWidget'
import WeatherWidget from './components/WeatherWidget'
import ZundamonAvatar from './components/ZundamonAvatar'
import VoiceInput from './components/VoiceInput'
import SmartHomePanel from './components/SmartHomePanel'
import { useWebSocket } from './hooks/useWebSocket'
import { useStore } from './store/useStore'

export default function App() {
  const { sendText } = useWebSocket()
  const { isNightMode, assistantState, schedule } = useStore()

  // モックスケジュール (Google Calendar未接続時)
  const mockSchedule = [
    { id: '1', title: 'チームMTG', time: '15:00' },
    { id: '2', title: '夕食', time: '19:30' },
  ]

  return (
    <div
      className="w-screen h-screen overflow-hidden select-none"
      style={{
        background: isNightMode
          ? 'linear-gradient(135deg, #0a0a0f 0%, #0f172a 100%)'
          : 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        filter: isNightMode ? 'brightness(0.6)' : 'brightness(1)',
        transition: 'filter 2s ease',
      }}
    >
      {/* 背景の星/粒子エフェクト */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full bg-green-400"
            style={{
              width: Math.random() * 3 + 1,
              height: Math.random() * 3 + 1,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              opacity: 0.2,
            }}
            animate={{ opacity: [0.1, 0.4, 0.1] }}
            transition={{
              duration: Math.random() * 4 + 2,
              repeat: Infinity,
              delay: Math.random() * 4,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 flex flex-col h-full p-4 gap-3">
        {/* ヘッダー: 時計 + 天気 */}
        <div className="flex items-start justify-between">
          <ClockWidget />
          <div className="flex items-start gap-3">
            <WeatherWidget />
            <motion.button
              whileTap={{ scale: 0.9 }}
              className="p-2 glass rounded-xl touch-active"
            >
              <Settings size={18} className="text-slate-400" />
            </motion.button>
          </div>
        </div>

        {/* メインコンテンツ */}
        <div className="flex flex-1 gap-3 min-h-0">
          {/* 左: ずんだもんアバター */}
          <div className="flex-shrink-0" style={{ width: '45%' }}>
            <ZundamonAvatar />
          </div>

          {/* 右: 情報ウィジェット */}
          <div className="flex-1 flex flex-col gap-3 min-w-0">
            {/* 今日の予定 */}
            <div className="glass rounded-xl p-3">
              <p className="text-slate-400 text-xs mb-2">📅 今日の予定</p>
              {mockSchedule.map((event) => (
                <div key={event.id} className="flex items-center gap-2 py-1">
                  <span className="text-green-400 text-xs font-mono w-12 flex-shrink-0">
                    {event.time}
                  </span>
                  <span className="text-white text-sm truncate">{event.title}</span>
                </div>
              ))}
            </div>

            {/* スマートホーム */}
            <SmartHomePanel />
          </div>
        </div>

        {/* 音声入力バー */}
        <VoiceInput onSendText={sendText} />
      </div>

      {/* タイマー完了オーバーレイ */}
      <AnimatePresence>
        {assistantState === 'timer_done' && (
          <motion.div
            className="absolute inset-0 flex items-center justify-center z-50"
            style={{ background: 'rgba(0,0,0,0.7)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="glass rounded-2xl p-8 text-center"
              initial={{ scale: 0.8 }}
              animate={{ scale: [0.8, 1.05, 1] }}
            >
              <div className="text-6xl mb-4">⏰</div>
              <p className="text-white text-2xl font-bold">タイマー終了なのだ！</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
