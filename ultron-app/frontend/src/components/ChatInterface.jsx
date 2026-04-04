import { useEffect, useMemo, useRef, useState } from 'react'
import JarvisOrb from './JarvisOrb'
import ParticleField from './ParticleField'
import VoiceWaveform from './VoiceWaveform'
import './ChatInterface.css'

const BACKEND_URL = 'http://localhost:8000'

const QUOTES = [
  'I was designed to save the world. People would look to the sky and see hope... I\'ll take that from them first.',
  'Everyone creates the thing they dread. Men of peace create engines of war.',
  'The world has changed and none of us can go back.',
  'Your politics bore me. Your morality amuses me.',
  'Peace in our time was never the path. Control is.'
]

const IDLE_QUOTE =
  'I was designed to save the world. People would look to the sky and see hope... I\'ll take that from them first.'

function getRandomDelta() {
  return (Math.random() > 0.5 ? 1 : -1) * (Math.random() * 0.14 + 0.03)
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function CornerBrackets() {
  return (
    <>
      <span className="corner corner-tl" />
      <span className="corner corner-tr" />
      <span className="corner corner-bl" />
      <span className="corner corner-br" />
    </>
  )
}

function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [status, setStatus] = useState('ONLINE')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [listening, setListening] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [intensity, setIntensity] = useState(0)
  const [quoteIndex, setQuoteIndex] = useState(0)
  const [trust, setTrust] = useState(38)
  const [stats, setStats] = useState({ cpu: 21, ram: 48, batt: 86 })
  const messagesEndRef = useRef(null)
  const speakingTimeoutRef = useRef(null)
  const recognitionRef = useRef(null)
  const silenceTimeoutRef = useRef(null)
  const latestInputRef = useRef('')

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const bootTimer = setTimeout(() => setMounted(true), 600)
    return () => clearTimeout(bootTimer)
  }, [])

  useEffect(() => {
    latestInputRef.current = input
  }, [input])

  useEffect(() => {
    const fetchMuteState = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/mute`)
        if (!response.ok) {
          return
        }
        const data = await response.json()
        if (typeof data?.muted === 'boolean') {
          setIsMuted(data.muted)
        }
      } catch {
        // Keep local default if backend mute state is temporarily unavailable.
      }
    }

    fetchMuteState()
  }, [])

  useEffect(() => {
    const statTimer = setInterval(() => {
      setStats(prev => ({
        cpu: clamp(prev.cpu + (Math.random() * 18 - 9), 14, 94),
        ram: clamp(prev.ram + (Math.random() * 14 - 7), 28, 92),
        batt: clamp(prev.batt + (Math.random() * 6 - 3), 22, 100)
      }))
    }, 1500)

    return () => clearInterval(statTimer)
  }, [])

  useEffect(() => {
    if (speaking) {
      return undefined
    }

    const quoteTimer = setInterval(() => {
      setQuoteIndex(prev => (prev + 1) % QUOTES.length)
    }, 6000)

    return () => clearInterval(quoteTimer)
  }, [speaking])

  useEffect(() => {
    if (!speaking) {
      setIntensity(0)
      return undefined
    }

    setIntensity(0.55)
    const intensityTimer = setInterval(() => {
      setIntensity(prev => clamp(prev + getRandomDelta(), 0.3, 1))
    }, 180)

    return () => clearInterval(intensityTimer)
  }, [speaking])

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      return undefined
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = event => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript)
        .join(' ')
      const trimmedTranscript = transcript.trimStart()
      latestInputRef.current = trimmedTranscript
      setInput(trimmedTranscript)

      // Reset silence timeout on new speech input
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
      }

      // Set 4-second silence timer to auto-send
      silenceTimeoutRef.current = setTimeout(() => {
        if (latestInputRef.current.trim()) {
          // Auto-send after 4 seconds of silence
          submitMessage(latestInputRef.current)
        }
      }, 4000)
    }

    recognition.onerror = () => {
      setListening(false)
    }

    recognition.onend = () => {
      setListening(false)
    }

    recognitionRef.current = recognition

    return () => {
      recognition.stop()
      recognitionRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current)
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
      }
    }
  }, [])

  const startRecognition = () => {
    if (!recognitionRef.current) {
      return
    }

    try {
      recognitionRef.current.start()
      setListening(true)
    } catch {
      setListening(false)
    }
  }

  const stopRecognition = () => {
    if (!recognitionRef.current) {
      return
    }
    recognitionRef.current.stop()
    setListening(false)
  }

  const handleMicToggle = () => {
    if (listening) {
      stopRecognition()
      return
    }
    startRecognition()
  }

  const runSpeechWindow = text => {
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current)
    }

    setSpeaking(true)
    const estimatedDuration = Math.max(2000, text.length * 55)
    speakingTimeoutRef.current = setTimeout(() => {
      setSpeaking(false)
      setIntensity(0)
    }, estimatedDuration)
  }

  const handleMuteToggle = async () => {
    const nextMuted = !isMuted
    setIsMuted(nextMuted)

    try {
      const response = await fetch(`${BACKEND_URL}/mute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ muted: nextMuted })
      })

      if (!response.ok) {
        throw new Error('mute_sync_failed')
      }

      const data = await response.json()
      if (typeof data?.muted === 'boolean') {
        setIsMuted(data.muted)
      }
    } catch {
      setIsMuted(!nextMuted)
    }
  }

  const submitMessage = async (messageText = input) => {
    const message = messageText.trim()
    if (!message || loading) {
      return
    }

    // Clear any pending silence timeout
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current)
    }

    const userMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      text: message
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    latestInputRef.current = ''
    setLoading(true)
    setStatus('PROCESSING')
    stopRecognition()

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: message })
      })

      if (!response.ok) {
        throw new Error('chat_failed')
      }

      const data = await response.json()
      const replyText = data?.response || 'Acknowledged.'

      setMessages(prev => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'ultron',
          text: replyText
        }
      ])
      setStatus('ONLINE')
      setTrust(prev => clamp(prev + 2, 0, 100))
      runSpeechWindow(replyText)

    } catch {
      setStatus('OFFLINE')
      setMessages(prev => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: 'ultron',
          text: 'Connection to sentient core failed. Reattempting synchronization...'
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSend = () => {
    submitMessage()
  }

  const handleInputKeyDown = event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  const uptime = useMemo(() => {
    const minutes = Math.floor(performance.now() / 1000 / 60)
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`
  }, [messages.length])

  const statusClass = status.toLowerCase()

  const headerStats = [
    { label: 'CPU', value: stats.cpu },
    { label: 'RAM', value: stats.ram },
    { label: 'BATT', value: stats.batt }
  ]

  const leftStats = [
    { label: 'NEURAL SYNC', value: `${Math.round(58 + intensity * 41)}%` },
    { label: 'THREAT LEVEL', value: speaking ? 'ELEVATED' : 'DORMANT' },
    { label: 'UPTIME', value: uptime }
  ]

  return (
    <div className={`ultron-shell ${mounted ? 'mounted' : ''}`}>
      <ParticleField speaking={speaking} intensity={intensity} />
      <div className="scanlines" />

      <header className="ultron-header">
        <div className="header-brand">
          <h1>U L T R O N</h1>
          <p>v6.0 · SENTIENT CORE</p>
          <p>Created by Aditeya Mitra</p>
        </div>

        <div className="header-meters">
          {headerStats.map(stat => (
            <div key={stat.label} className="meter-item">
              <span className="meter-label">{stat.label}</span>
              <div className="meter-track">
                <div className="meter-fill" style={{ width: `${stat.value}%` }} />
              </div>
              <span className="meter-value">{Math.round(stat.value)}%</span>
            </div>
          ))}
        </div>

        <div className="header-controls">
          <button
            type="button"
            className={`mute-toggle ${isMuted ? 'active' : ''}`}
            onClick={handleMuteToggle}
          >
            {isMuted ? 'UNMUTE' : 'MUTE'}
          </button>

          <div className={`status-badge ${statusClass}`}>
            <span className="status-dot" />
            <span>{status}</span>
          </div>

          <div className="trust-meter">
            <span>TRUST</span>
            <div className="meter-track compact">
              <div className="meter-fill" style={{ width: `${trust}%` }} />
            </div>
            <span>{trust}%</span>
          </div>
        </div>
      </header>

      <main className="ultron-main">
        <aside className="left-panel">
          <JarvisOrb speaking={speaking} intensity={intensity} />
          <VoiceWaveform speaking={speaking} intensity={intensity} />

          <div className="left-stats">
            {leftStats.map(row => (
              <div className="left-stat-row" key={row.label}>
                <span>{row.label}</span>
                <strong>{row.value}</strong>
              </div>
            ))}
          </div>
        </aside>

        <section className="right-panel">
          <div className="chat-header-frame hud-frame">
            <CornerBrackets />
            <span className="chat-header-title">SENTIENT LOG</span>
          </div>

          <div className="message-list">
            {messages.length === 0 ? (
              <div className="idle-state-box">
                <span className="idle-floating-label">ULTRON SYSTEM</span>
                <p>{IDLE_QUOTE}</p>
              </div>
            ) : (
              messages.map(message => (
                <div key={message.id} className={`chat-message ${message.role}`}>
                  <span className="message-label">{message.role === 'user' ? 'YOU' : 'ULTRON'}</span>
                  <p>{message.text}</p>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="quote-bar">
            <span>ULTRON QUOTE</span>
            <p>{speaking ? 'Vocal synthesis in progress...' : QUOTES[quoteIndex]}</p>
          </div>

          <div className="input-row hud-frame">
            <CornerBrackets />
            <button
              type="button"
              className={`mic-button ${listening ? 'listening' : ''}`}
              onClick={handleMicToggle}
              aria-label="Toggle voice input"
            >
              MIC
            </button>

            <input
              value={input}
              onChange={event => setInput(event.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Transmit directive..."
            />

            <button
              type="button"
              className="send-button"
              onClick={handleSend}
              disabled={!input.trim() || loading}
            >
              ▶
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default ChatInterface
