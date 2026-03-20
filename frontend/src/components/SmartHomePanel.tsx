import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { Lightbulb, Thermometer, Lock } from 'lucide-react'
import { useStore } from '../store/useStore'

export default function SmartHomePanel() {
  const { devices, setDevices } = useStore()

  useEffect(() => {
    fetchDevices()
    const interval = setInterval(fetchDevices, 30000)
    return () => clearInterval(interval)
  }, [])

  async function fetchDevices() {
    try {
      const res = await fetch('/api/smart-home/devices')
      if (res.ok) {
        const data = await res.json()
        if (data.devices) setDevices(data.devices.slice(0, 6))
      }
    } catch (e) {}
  }

  async function toggleDevice(entityId: string, currentState: string) {
    const action = currentState === 'on' ? 'turn_off' : 'turn_on'
    try {
      await fetch('/api/smart-home/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity_id: entityId, action }),
      })
      fetchDevices()
    } catch (e) {}
  }

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case 'light': return <Lightbulb size={16} />
      case 'climate': return <Thermometer size={16} />
      case 'lock': return <Lock size={16} />
      default: return <Lightbulb size={16} />
    }
  }

  if (devices.length === 0) {
    return (
      <div className="glass rounded-xl p-3">
        <p className="text-slate-500 text-xs text-center">🏠 HA未接続</p>
      </div>
    )
  }

  return (
    <div className="glass rounded-xl p-3">
      <p className="text-slate-400 text-xs mb-2">🏠 スマートホーム</p>
      <div className="grid grid-cols-3 gap-2">
        {devices.slice(0, 6).map((device) => (
          <motion.button
            key={device.entity_id}
            whileTap={{ scale: 0.93 }}
            onClick={() => toggleDevice(device.entity_id, device.state)}
            className={`rounded-lg p-2 text-xs text-left touch-active ${
              device.state === 'on'
                ? 'bg-yellow-500/20 border border-yellow-500/40 text-yellow-300'
                : 'bg-slate-800 border border-slate-700 text-slate-500'
            }`}
          >
            <div className="mb-1">{getDomainIcon(device.domain)}</div>
            <div className="truncate">{device.name}</div>
          </motion.button>
        ))}
      </div>
    </div>
  )
}
