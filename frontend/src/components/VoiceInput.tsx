import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mic, Send, X } from 'lucide-react'
import { useStore } from '../store/useStore'

interface Props {
  onSendText: (text: string) => void
}

export default function VoiceInput({ onSendText }: Props) {
  const [inputText, setInputText] = useState('')
  const [showInput, setShowInput] = useState(false)
  const { assistantState } = useStore()

  const isActive = ['wake', 'listening', 'thinking', 'speaking'].includes(assistantState)

  const handleSend = () => {
    if (inputText.trim()) {
      onSendText(inputText.trim())
      setInputText('')
      setShowInput(false)
    }
  }

  return (
    <div className="flex items-center gap-3">
      {showInput ? (
        <motion.div
          className="flex items-center gap-2 flex-1"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="テキストで入力するのだ..."
            className="flex-1 bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-green-400"
            autoFocus
          />
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleSend}
            className="p-3 rounded-xl bg-green-500 text-white touch-active"
          >
            <Send size={18} />
          </motion.button>
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setShowInput(false)}
            className="p-3 rounded-xl bg-slate-700 text-slate-400 touch-active"
          >
            <X size={18} />
          </motion.button>
        </motion.div>
      ) : (
        <>
          <motion.div
            className="flex items-center gap-3 flex-1 px-5 py-3 rounded-xl glass"
            animate={{ borderColor: isActive ? 'rgba(74,222,128,0.5)' : 'rgba(255,255,255,0.1)' }}
          >
            <motion.div
              animate={{ scale: isActive ? [1, 1.3, 1] : 1 }}
              transition={{ duration: 0.8, repeat: isActive ? Infinity : 0 }}
            >
              <Mic size={20} className={isActive ? 'text-green-400' : 'text-slate-400'} />
            </motion.div>
            <span className="text-sm text-slate-400">
              {isActive ? '聞いてるのだ...' : '「ねえ、ずんだもん」と話しかけるのだ'}
            </span>
          </motion.div>
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setShowInput(true)}
            className="p-3 rounded-xl glass touch-active"
          >
            <Send size={18} className="text-slate-400" />
          </motion.button>
        </>
      )}
    </div>
  )
}
