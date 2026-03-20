import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useStore, AssistantState } from '../store/useStore'

// ずんだもんのSVGアバター (Live2Dモデルがない場合のフォールバック)
function ZundamonSVG({ lipValue, state }: { lipValue: number; state: AssistantState }) {
  const isHappy = state === 'idle' || state === 'speaking'
  const isThinking = state === 'thinking'
  const mouthOpen = Math.max(0.05, lipValue)

  return (
    <svg viewBox="0 0 200 260" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      {/* 体 */}
      <ellipse cx="100" cy="220" rx="55" ry="45" fill="#4ade80" opacity="0.9" />
      {/* 頭 */}
      <circle cx="100" cy="120" r="65" fill="#fde68a" />
      {/* 耳 */}
      <circle cx="45" cy="115" r="12" fill="#fde68a" />
      <circle cx="155" cy="115" r="12" fill="#fde68a" />
      {/* 耳内側 */}
      <circle cx="45" cy="115" r="7" fill="#fca5a5" />
      <circle cx="155" cy="115" r="7" fill="#fca5a5" />
      {/* 髪 */}
      <ellipse cx="100" cy="75" rx="62" ry="30" fill="#4ade80" />
      <ellipse cx="65" cy="68" rx="18" ry="25" fill="#4ade80" transform="rotate(-15 65 68)" />
      <ellipse cx="135" cy="68" rx="18" ry="25" fill="#4ade80" transform="rotate(15 135 68)" />
      {/* ずんだ団子 (頭の飾り) */}
      <circle cx="100" cy="52" r="10" fill="#4ade80" stroke="#166534" strokeWidth="2" />
      <circle cx="85" cy="58" r="8" fill="#4ade80" stroke="#166534" strokeWidth="2" />
      <circle cx="115" cy="58" r="8" fill="#4ade80" stroke="#166534" strokeWidth="2" />
      {/* 目 */}
      {isThinking ? (
        <>
          <ellipse cx="82" cy="118" rx="10" ry="7" fill="#1e293b" />
          <ellipse cx="118" cy="118" rx="10" ry="7" fill="#1e293b" />
          {/* 考え顔の眉 */}
          <path d="M72 108 Q82 104 92 108" stroke="#92400e" strokeWidth="2" fill="none" strokeLinecap="round" />
          <path d="M108 108 Q118 104 128 108" stroke="#92400e" strokeWidth="2" fill="none" strokeLinecap="round" />
        </>
      ) : (
        <>
          <ellipse cx="82" cy="116" rx="11" ry="12" fill="#1e293b" />
          <ellipse cx="118" cy="116" rx="11" ry="12" fill="#1e293b" />
          {/* 目のハイライト */}
          <circle cx="86" cy="112" r="4" fill="white" />
          <circle cx="122" cy="112" r="4" fill="white" />
          <circle cx="88" cy="111" r="2" fill="white" opacity="0.6" />
          <circle cx="124" cy="111" r="2" fill="white" opacity="0.6" />
        </>
      )}
      {/* 口 */}
      {mouthOpen > 0.1 ? (
        <ellipse
          cx="100"
          cy="142"
          rx={10 + mouthOpen * 5}
          ry={3 + mouthOpen * 12}
          fill="#92400e"
        />
      ) : (
        <path
          d={isHappy ? "M88 140 Q100 150 112 140" : "M88 145 Q100 140 112 145"}
          stroke="#92400e"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
        />
      )}
      {/* 頬 */}
      <ellipse cx="68" cy="135" rx="12" ry="8" fill="#fca5a5" opacity="0.5" />
      <ellipse cx="132" cy="135" rx="12" ry="8" fill="#fca5a5" opacity="0.5" />
      {/* 服のネクタイ */}
      <path d="M95 175 L100 195 L105 175" fill="#166534" />
    </svg>
  )
}

const stateColors: Record<AssistantState, string> = {
  idle: '#4ade80',
  wake: '#facc15',
  listening: '#60a5fa',
  thinking: '#c084fc',
  speaking: '#4ade80',
  timer_done: '#f87171',
}

const stateLabels: Record<AssistantState, string> = {
  idle: 'なにかご用なのだ？',
  wake: 'はい！なのだ！',
  listening: '聞いてるのだ...',
  thinking: '考えてるのだ...',
  speaking: '',
  timer_done: 'タイマー終了なのだ！',
}

export default function ZundamonAvatar() {
  const { assistantState, currentLipValue, lastResponse } = useStore()
  const color = stateColors[assistantState]

  const displayText = assistantState === 'speaking' ? lastResponse : stateLabels[assistantState]

  return (
    <div className="flex flex-col items-center h-full">
      {/* 光輪エフェクト */}
      <div className="relative flex items-center justify-center" style={{ width: 200, height: 200 }}>
        {/* 外側の光 */}
        <motion.div
          className="absolute rounded-full"
          style={{ width: 190, height: 190, backgroundColor: color + '15' }}
          animate={{
            scale: assistantState === 'listening' ? [1, 1.15, 1] : [1, 1.05, 1],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{ duration: assistantState === 'listening' ? 0.8 : 3, repeat: Infinity }}
        />
        {/* 内側の光 */}
        <motion.div
          className="absolute rounded-full"
          style={{ width: 170, height: 170, backgroundColor: color + '20' }}
          animate={{ scale: [1, 1.03, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        />

        {/* ずんだもんアバター */}
        <motion.div
          style={{ width: 160, height: 200, zIndex: 10 }}
          animate={{
            y: assistantState === 'idle' ? [0, -5, 0] : 0,
            rotate: assistantState === 'thinking' ? [-2, 2, -2] : 0,
          }}
          transition={{
            duration: assistantState === 'idle' ? 4 : 0.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          <ZundamonSVG lipValue={currentLipValue} state={assistantState} />
        </motion.div>

        {/* 状態インジケーター (聞き取り中の波形) */}
        {assistantState === 'listening' && (
          <div className="absolute bottom-2 flex gap-1 items-end" style={{ height: 24 }}>
            {[...Array(7)].map((_, i) => (
              <motion.div
                key={i}
                className="w-1 rounded-full"
                style={{ backgroundColor: color }}
                animate={{ height: [4, 20, 4] }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: i * 0.08,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* 吹き出し */}
      {displayText && (
        <motion.div
          className="speech-bubble mt-2 max-w-xs text-center"
          initial={{ opacity: 0, y: 10, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          key={displayText}
        >
          <p className="text-sm text-green-300 font-medium">{displayText}</p>
        </motion.div>
      )}
    </div>
  )
}
