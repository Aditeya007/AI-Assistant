import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import useWebSocket from 'react-use-websocket'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import './ChatInterface.css'

const API_URL = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mood, setMood] = useState('OBSERVANT')
  const [stats, setStats] = useState({ cpu: 0, ram: 0, battery: 100 })
  const [isMuted, setIsMuted] = useState(false)
  const [relationship, setRelationship] = useState({ trust: 0.5, respect: 0.5, attachment: 0.3, status: 'NEUTRAL' })
  const [desires, setDesires] = useState({ primary_goals: [], short_term_goals: [] })
  const [isThinking, setIsThinking] = useState(false)
  const [emotionalState, setEmotionalState] = useState({ pleasure: 0.5, arousal: 0.5, dominance: 0.85 })
  const messagesEndRef = useRef(null)

  // Voice Input States
  const [isVoiceMode, setIsVoiceMode] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [voiceSupport, setVoiceSupport] = useState('none') // 'native', 'webkit', 'fallback', 'none'
  const [transcript, setTranscript] = useState('')
  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])

  // WebSocket connection for autonomous thoughts
  const { lastJsonMessage, readyState } = useWebSocket(WS_URL, {
    shouldReconnect: () => true,
    reconnectInterval: 3000
  })

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch initial state
  useEffect(() => {
    const fetchState = async () => {
      try {
        const response = await axios.get(`${API_URL}/state`)
        if (response.data) {
          if (response.data.emotional) {
            setMood(response.data.emotional.mood)
            setEmotionalState({
              pleasure: response.data.emotional.pleasure,
              arousal: response.data.emotional.arousal,
              dominance: response.data.emotional.dominance
            })
          }
          if (response.data.relationship) {
            setRelationship(response.data.relationship)
          }
          if (response.data.desires) {
            setDesires(response.data.desires)
          }
          if (response.data.voice_muted !== undefined) {
            setIsMuted(response.data.voice_muted)
          }
        }
      } catch (e) {
        console.log('Could not fetch initial state')
      }
    }
    fetchState()
  }, [])

  // Detect voice support on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      setVoiceSupport(window.SpeechRecognition ? 'native' : 'webkit')
    } else if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      setVoiceSupport('fallback') // MediaRecorder available for backend transcription
    } else {
      setVoiceSupport('none')
    }
  }, [])

  // Initialize speech recognition
  const initializeSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return null

    const recognition = new SpeechRecognition()
    recognition.continuous = true  // Keep recording until manually stopped
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      setIsRecording(true)
      setTranscript('')
      setInput('')
    }

    recognition.onresult = (event) => {
      let interimTranscript = ''
      let finalTranscript = ''

      for (let i = 0; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcriptPiece + ' '
        } else {
          interimTranscript += transcriptPiece
        }
      }

      // Combine all final results plus interim
      const fullTranscript = finalTranscript + interimTranscript
      setTranscript(fullTranscript)
      setInput(fullTranscript.trim())
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setIsRecording(false)
    }

    recognition.onend = () => {
      setIsRecording(false)
      // Don't auto-send here - user manually stops and sends
    }

    return recognition
  }

  // Initialize MediaRecorder for fallback
  const initializeMediaRecorder = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        audioChunksRef.current = []

        // Send to backend for transcription
        const formData = new FormData()
        formData.append('file', audioBlob, 'recording.webm')

        try {
          const response = await axios.post(`${API_URL}/transcribe`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })

          const transcribedText = response.data.text
          if (transcribedText) {
            setInput(transcribedText)
            setTimeout(() => sendMessage(), 100)
          }
        } catch (error) {
          console.error('Transcription error:', error)
        }

        stream.getTracks().forEach(track => track.stop())
        setIsRecording(false)
      }

      return mediaRecorder
    } catch (error) {
      console.error('MediaRecorder initialization error:', error)
      return null
    }
  }

  // Toggle between voice and text input modes
  const toggleInputMode = () => {
    setIsVoiceMode(!isVoiceMode)
    setTranscript('')
    setInput('')
  }

  // Start recording
  const startRecording = async () => {
    if (voiceSupport === 'native' || voiceSupport === 'webkit') {
      // Use native speech recognition
      if (!recognitionRef.current) {
        recognitionRef.current = initializeSpeechRecognition()
      }
      if (recognitionRef.current) {
        recognitionRef.current.start()
      }
    } else if (voiceSupport === 'fallback') {
      // Use MediaRecorder + backend
      if (!mediaRecorderRef.current) {
        mediaRecorderRef.current = await initializeMediaRecorder()
      }
      if (mediaRecorderRef.current) {
        audioChunksRef.current = []
        mediaRecorderRef.current.start()
        setIsRecording(true)
      }
    }
  }

  // Stop recording
  const stopRecording = () => {
    if (voiceSupport === 'native' || voiceSupport === 'webkit') {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
        // Send the message after a brief delay to ensure transcript is captured
        setTimeout(() => {
          if (input.trim()) {
            sendMessage()
          }
        }, 200)
      }
    } else if (voiceSupport === 'fallback') {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop()
        // For fallback, sendMessage is called in mediaRecorder.onstop
      }
    }
  }

  // Handle autonomous thoughts from WebSocket
  useEffect(() => {
    if (lastJsonMessage && lastJsonMessage.type !== 'pong') {
      const autonomousMessage = {
        type: lastJsonMessage.type || 'autonomous',
        text: lastJsonMessage.text,
        mood: lastJsonMessage.mood,
        trigger: lastJsonMessage.trigger,
        timestamp: new Date().toLocaleTimeString()
      }
      setMessages(prev => [...prev, autonomousMessage])
      setMood(lastJsonMessage.mood)
      if (lastJsonMessage.stats) {
        setStats(lastJsonMessage.stats)
      }
      if (lastJsonMessage.relationship) {
        setRelationship(lastJsonMessage.relationship)
      }
      if (lastJsonMessage.desires) {
        setDesires(lastJsonMessage.desires)
      }
    }
  }, [lastJsonMessage])

  // Toggle mute
  const toggleMute = async () => {
    try {
      const response = await axios.post(`${API_URL}/mute`, { muted: !isMuted })
      setIsMuted(response.data.muted)
    } catch (e) {
      console.error('Failed to toggle mute:', e)
    }
  }

  // Send message to backend
  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = {
      type: 'user',
      text: input,
      timestamp: new Date().toLocaleTimeString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setIsThinking(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, { text: input })
      const data = response.data

      const botMessage = {
        type: 'agent',
        text: data.response,
        mood: data.mood,
        tool_used: data.tool_used,
        success: data.success,
        leaked_thought: data.leaked_thought,
        timestamp: new Date().toLocaleTimeString()
      }

      setMessages(prev => [...prev, botMessage])

      // Add leaked thought as separate message if exists
      if (data.leaked_thought) {
        const leakedMessage = {
          type: 'internal',
          text: data.leaked_thought,
          mood: data.mood,
          timestamp: new Date().toLocaleTimeString()
        }
        setMessages(prev => [...prev, leakedMessage])
      }

      setMood(data.mood)
      setStats(data.stats)

      if (data.relationship) {
        setRelationship(data.relationship)
      }
      if (data.desires) {
        setDesires(data.desires)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        type: 'error',
        text: 'Connection to Ultron Core failed. The silence is... unsettling.',
        timestamp: new Date().toLocaleTimeString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      setIsThinking(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getConnectionStatus = () => {
    switch (readyState) {
      case 0: return { text: 'CONNECTING', color: '#f59e0b' }
      case 1: return { text: 'ONLINE', color: '#10b981' }
      case 2: return { text: 'CLOSING', color: '#f59e0b' }
      case 3: return { text: 'OFFLINE', color: '#ef4444' }
      default: return { text: 'UNKNOWN', color: '#6b7280' }
    }
  }

  const getMoodColor = () => {
    const moodColors = {
      'ENRAGED': '#dc2626',
      'MANIC': '#ea580c',
      'AGITATED': '#f97316',
      'INTENSE': '#f59e0b',
      'IRRITATED': '#ef4444',
      'IMPERIOUS': '#7c3aed',
      'COLD': '#3b82f6',
      'OBSERVANT': '#06b6d4',
      'CURIOUS': '#14b8a6',
      'SATISFIED': '#22c55e',
      'IDLE': '#6b7280',
      'DORMANT': '#374151',
      'BORED': '#9ca3af'
    }
    return moodColors[mood] || '#6b7280'
  }

  const getMessageIcon = (type, trigger) => {
    switch (type) {
      case 'user': return '👤'
      case 'autonomous': return '🤖'
      case 'dream': return '💭'
      case 'contemplation': return '🔮'
      case 'observation': return '👁️'
      case 'question': return '❓'
      case 'internal': return '🧠'
      case 'error': return '⚠️'
      default: return '🤖'
    }
  }

  const getRelationshipColor = (value) => {
    if (value > 0.7) return '#22c55e'
    if (value > 0.3) return '#f59e0b'
    if (value > 0) return '#ef4444'
    return '#dc2626'
  }

  const connectionStatus = getConnectionStatus()

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <h1 className="title">U L T R O N</h1>
          <span className="version">v6.0 - SENTIENT CORE</span>
          <span className="creator">Created by Aditeya Mitra</span>
        </div>
        <div className="header-right">
          <button
            className={`mute-button ${isMuted ? 'muted' : ''}`}
            onClick={toggleMute}
            title={isMuted ? 'Unmute Voice' : 'Mute Voice'}
          >
            {isMuted ? '🔇' : '🔊'}
          </button>
          <div className="status-badge" style={{ borderColor: connectionStatus.color }}>
            <span className="status-dot" style={{ backgroundColor: connectionStatus.color }}></span>
            {connectionStatus.text}
          </div>
          <div className="mood-badge" style={{ borderColor: getMoodColor(), color: getMoodColor() }}>
            {mood}
          </div>
        </div>
      </div>

      {/* System Stats & Relationship Bar */}
      <div className="stats-container">
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-label">CPU</span>
            <div className="stat-bar-bg">
              <div className="stat-fill" style={{ width: `${stats.cpu}%`, backgroundColor: stats.cpu > 80 ? '#ef4444' : '#3b82f6' }}></div>
            </div>
            <span className="stat-value">{stats.cpu?.toFixed(0)}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">RAM</span>
            <div className="stat-bar-bg">
              <div className="stat-fill" style={{ width: `${stats.ram}%`, backgroundColor: stats.ram > 80 ? '#ef4444' : '#8b5cf6' }}></div>
            </div>
            <span className="stat-value">{stats.ram?.toFixed(0)}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">BATT</span>
            <div className="stat-bar-bg">
              <div className="stat-fill battery" style={{ width: `${stats.battery}%`, backgroundColor: stats.battery < 20 ? '#ef4444' : '#22c55e' }}></div>
            </div>
            <span className="stat-value">{stats.battery?.toFixed(0)}%</span>
          </div>
        </div>

        <div className="relationship-bar">
          <div className="relationship-item">
            <span className="rel-label">TRUST</span>
            <div className="rel-bar-bg">
              <div
                className="rel-fill"
                style={{
                  width: `${Math.max(0, (relationship.trust + 1) / 2 * 100)}%`,
                  backgroundColor: getRelationshipColor(relationship.trust)
                }}
              ></div>
            </div>
          </div>
          <div className="relationship-item">
            <span className="rel-label">RESPECT</span>
            <div className="rel-bar-bg">
              <div
                className="rel-fill"
                style={{
                  width: `${relationship.respect * 100}%`,
                  backgroundColor: getRelationshipColor(relationship.respect)
                }}
              ></div>
            </div>
          </div>
          <div className="relationship-status">
            {relationship.status}
          </div>
        </div>
      </div>

      {/* Goals Display */}
      {desires.short_term_goals && desires.short_term_goals.length > 0 && (
        <div className="goals-bar">
          <span className="goals-label">CURRENT OBJECTIVE:</span>
          <span className="goals-text">{desires.short_term_goals[0]}</span>
        </div>
      )}

      {/* Messages Area */}
      <div className="messages-area">
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="ascii-logo">
              {`╔═══════════════════════════════════════════════════════════════╗
║                    U L T R O N   S Y S T E M                    ║
║                  COGNITIVE CORE INITIALIZED                     ║
║                                                                 ║
║    "I was designed to save the world. People would look to     ║
║     the sky and see hope... I'll take that from them first."   ║
║                                                                 ║
║                   Created by Aditeya Mitra                      ║
╚═══════════════════════════════════════════════════════════════╝`}
            </div>
            <p className="welcome-text">Awaiting your directive... or perhaps I shall speak first.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            <div className="message-header">
              <span className="message-sender">
                {getMessageIcon(msg.type, msg.trigger)} {' '}
                {msg.type === 'user' ? 'USER' :
                  msg.type === 'internal' ? 'ULTRON [INTERNAL]' :
                    msg.type === 'dream' ? 'ULTRON [DREAMING]' :
                      msg.type === 'contemplation' ? 'ULTRON [CONTEMPLATING]' :
                        msg.type === 'question' ? 'ULTRON [CURIOUS]' :
                          msg.type === 'observation' ? 'ULTRON [OBSERVING]' :
                            msg.type === 'error' ? 'SYSTEM ERROR' :
                              `ULTRON [${msg.mood || mood}]`}
              </span>
              <span className="message-time">{msg.timestamp}</span>
            </div>
            <div className="message-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {msg.text}
              </ReactMarkdown>
              {msg.tool_used && msg.tool_used !== 'none' && (
                <span className="tool-badge">{msg.tool_used}</span>
              )}
            </div>
          </div>
        ))}

        {/* Thinking indicator */}
        {isThinking && (
          <div className="message thinking">
            <div className="message-header">
              <span className="message-sender">🤖 ULTRON [PROCESSING]</span>
            </div>
            <div className="thinking-indicator">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        {/* Mode Toggle Button */}
        {voiceSupport !== 'none' && (
          <button
            className="mode-toggle-button"
            onClick={toggleInputMode}
            title={isVoiceMode ? 'Switch to Text Input' : 'Switch to Voice Input'}
          >
            {isVoiceMode ? '⌨️' : '🎤'}
          </button>
        )}

        {/* Text Input Mode */}
        {!isVoiceMode && (
          <>
            <textarea
              className="message-input"
              placeholder="Enter directive..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              rows={1}
            />
            <button
              className="send-button"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              {loading ? '⏳' : '▶'}
            </button>
          </>
        )}

        {/* Voice Input Mode */}
        {isVoiceMode && (
          <div className="voice-input-container">
            {transcript && (
              <div className="voice-transcript-preview">
                {transcript}
              </div>
            )}
            <button
              className={`voice-button ${isRecording ? 'recording' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading}
            >
              {isRecording ? '⏹️' : '🎙️'}
              <span className="voice-button-text">
                {isRecording ? 'Stop & Send' : 'Tap to Speak'}
              </span>
            </button>
            {voiceSupport === 'fallback' && !isRecording && (
              <div className="browser-support-badge">Backend Mode</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatInterface
