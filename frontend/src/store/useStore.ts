import { create } from 'zustand'

export type AssistantState = 'idle' | 'wake' | 'listening' | 'thinking' | 'speaking' | 'timer_done'

export interface WeatherData {
  temp: number
  feels_like: number
  humidity: number
  description: string
  icon: string
  city: string
}

export interface ScheduleEvent {
  id: string
  title: string
  time: string
  location?: string
}

export interface SmartDevice {
  entity_id: string
  name: string
  state: string
  domain: string
}

interface PiVoiceStore {
  // アシスタント状態
  assistantState: AssistantState
  lastTranscript: string
  lastResponse: string
  lipSyncFrames: number[]
  currentLipValue: number

  // データ
  weather: WeatherData | null
  schedule: ScheduleEvent[]
  devices: SmartDevice[]
  currentTime: Date
  isNightMode: boolean

  // 音楽
  nowPlaying: { title: string; artist: string; playing: boolean } | null

  // Actions
  setAssistantState: (state: AssistantState) => void
  setLastTranscript: (text: string) => void
  setLastResponse: (text: string) => void
  setLipSyncFrames: (frames: number[]) => void
  setCurrentLipValue: (value: number) => void
  setWeather: (weather: WeatherData) => void
  setSchedule: (events: ScheduleEvent[]) => void
  setDevices: (devices: SmartDevice[]) => void
  setCurrentTime: (time: Date) => void
  setNightMode: (night: boolean) => void
  setNowPlaying: (info: { title: string; artist: string; playing: boolean } | null) => void
}

export const useStore = create<PiVoiceStore>((set) => ({
  assistantState: 'idle',
  lastTranscript: '',
  lastResponse: '',
  lipSyncFrames: [],
  currentLipValue: 0,
  weather: null,
  schedule: [],
  devices: [],
  currentTime: new Date(),
  isNightMode: false,
  nowPlaying: null,

  setAssistantState: (state) => set({ assistantState: state }),
  setLastTranscript: (text) => set({ lastTranscript: text }),
  setLastResponse: (text) => set({ lastResponse: text }),
  setLipSyncFrames: (frames) => set({ lipSyncFrames: frames }),
  setCurrentLipValue: (value) => set({ currentLipValue: value }),
  setWeather: (weather) => set({ weather }),
  setSchedule: (events) => set({ schedule: events }),
  setDevices: (devices) => set({ devices }),
  setCurrentTime: (time) => set({ currentTime: time }),
  setNightMode: (night) => set({ isNightMode: night }),
  setNowPlaying: (info) => set({ nowPlaying: info }),
}))
