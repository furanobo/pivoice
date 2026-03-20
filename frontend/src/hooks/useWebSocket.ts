import { useEffect, useRef } from 'react'
import { useStore } from '../store/useStore'

const WS_URL = `ws://${window.location.hostname}:8000/ws`

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const frameTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const { setAssistantState, setLastTranscript, setLastResponse, setLipSyncFrames, setCurrentLipValue } = useStore()

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        // Keep-alive ping
        const ping = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000)
        ;(ws as any)._pingInterval = ping
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (e) {
          console.error('WS message parse error:', e)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 3s...')
        if ((ws as any)._pingInterval) clearInterval((ws as any)._pingInterval)
        setTimeout(connect, 3000)
      }

      ws.onerror = (e) => {
        console.error('WebSocket error:', e)
      }
    }

    function handleMessage(data: any) {
      switch (data.type) {
        case 'state':
          setAssistantState(data.state)
          if (data.data?.text) setLastTranscript(data.data.text)
          break

        case 'response':
          setLastResponse(data.text || '')
          break

        case 'lipsync':
          if (data.frames && data.frames.length > 0) {
            animateLipSync(data.frames)
          }
          break

        case 'pong':
          break

        default:
          console.log('Unknown WS message:', data)
      }
    }

    function animateLipSync(frames: number[]) {
      if (frameTimerRef.current) clearInterval(frameTimerRef.current)
      let i = 0
      frameTimerRef.current = setInterval(() => {
        if (i >= frames.length) {
          clearInterval(frameTimerRef.current!)
          setCurrentLipValue(0)
          return
        }
        setCurrentLipValue(frames[i])
        i++
      }, 1000 / 30) // 30fps
    }

    connect()

    return () => {
      wsRef.current?.close()
      if (frameTimerRef.current) clearInterval(frameTimerRef.current)
    }
  }, [])

  const sendText = (text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text_input', text }))
    }
  }

  return { sendText }
}
