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
  const [voiceError, setVoiceError] = useState('')
  const recognitionRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioContextRef = useRef(null)
  const sourceNodeRef = useRef(null)
  const processorNodeRef = useRef(null)
  const pcmChunksRef = useRef([])
  const transcriptRef = useRef('')
  const manualStopRef = useRef(false)
  const restartingRef = useRef(false)
  const wantedRecordingRef = useRef(false)
  const isVoiceModeRef = useRef(false)
  const voiceSupportRef = useRef('none')
  const freshSessionRef = useRef(false)

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
    // Prefer backend mode for reliability (native browser recognition often fails with network errors).
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      setVoiceSupport('fallback') // MediaRecorder available for backend transcription
    } else if (SpeechRecognition) {
      setVoiceSupport(window.SpeechRecognition ? 'native' : 'webkit')
    } else {
      setVoiceSupport('none')
    }
  }, [])

  useEffect(() => {
    isVoiceModeRef.current = isVoiceMode
  }, [isVoiceMode])

  useEffect(() => {
    voiceSupportRef.current = voiceSupport
  }, [voiceSupport])

  // Initialize speech recognition
  const initializeSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return null

    const recognition = new SpeechRecognition()
    recognition.continuous = true  // Keep recording until manually stopped
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      restartingRef.current = false
      setIsRecording(true)
      // Clear transcript only for a fresh user-initiated session, not auto-restarts.
      if (freshSessionRef.current) {
        setTranscript('')
        setInput('')
        transcriptRef.current = ''
        freshSessionRef.current = false
      }
      setVoiceError('')
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
      transcriptRef.current = fullTranscript.trim()
      setTranscript(fullTranscript)
      setInput(fullTranscript.trim())
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setVoiceError(`Voice error: ${event.error}`)
      // Only hard-stop for permission/capture issues. Transient errors are recoverable.
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed' || event.error === 'audio-capture') {
        manualStopRef.current = true
        wantedRecordingRef.current = false
        setIsRecording(false)
      }
    }

    recognition.onend = () => {
      setIsRecording(false)
      // Some browsers end recognition unexpectedly; auto-restart unless user explicitly stopped.
      if (
        wantedRecordingRef.current &&
        !manualStopRef.current &&
        isVoiceModeRef.current &&
        (voiceSupportRef.current === 'native' || voiceSupportRef.current === 'webkit') &&
        !restartingRef.current
      ) {
        restartingRef.current = true
        setTimeout(() => {
          try {
            recognition.start()
          } catch {
            restartingRef.current = false
          }
        }, 120)
      }
    }

    return recognition
  }

  const encodeWav = (float32Samples, sampleRate) => {
    const bytesPerSample = 2
    const numChannels = 1
    const blockAlign = numChannels * bytesPerSample
    const byteRate = sampleRate * blockAlign
    const dataSize = float32Samples.length * bytesPerSample
    const buffer = new ArrayBuffer(44 + dataSize)
    const view = new DataView(buffer)

    const writeString = (offset, str) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i))
      }
    }

    writeString(0, 'RIFF')
    view.setUint32(4, 36 + dataSize, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, byteRate, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, 16, true)
    writeString(36, 'data')
    view.setUint32(40, dataSize, true)

    let offset = 44
    for (let i = 0; i < float32Samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, float32Samples[i]))
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    }

    return new Blob([buffer], { type: 'audio/wav' })
  }

  // Initialize WebAudio PCM recorder for fallback
  const initializePcmRecorder = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
      const source = audioContext.createMediaStreamSource(stream)
      const processor = audioContext.createScriptProcessor(4096, 1, 1)

      pcmChunksRef.current = []
      processor.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0)
        pcmChunksRef.current.push(new Float32Array(inputData))
      }

      source.connect(processor)
      processor.connect(audioContext.destination)

      mediaStreamRef.current = stream
      audioContextRef.current = audioContext
      sourceNodeRef.current = source
      processorNodeRef.current = processor
      return true
    } catch (error) {
      console.error('PCM recorder initialization error:', error)
      setVoiceError('Microphone permission denied or unavailable.')
      return false
    }
  }

  const stopPcmRecorderAndTranscribe = async () => {
    try {
      if (processorNodeRef.current) {
        processorNodeRef.current.disconnect()
      }
      if (sourceNodeRef.current) {
        sourceNodeRef.current.disconnect()
      }

      const sampleRate = audioContextRef.current?.sampleRate || 16000
      const totalLength = pcmChunksRef.current.reduce((sum, chunk) => sum + chunk.length, 0)
      const merged = new Float32Array(totalLength)
      let offset = 0
      for (const chunk of pcmChunksRef.current) {
        merged.set(chunk, offset)
        offset += chunk.length
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop())
      }
      if (audioContextRef.current) {
        await audioContextRef.current.close()
      }

      mediaStreamRef.current = null
      audioContextRef.current = null
      sourceNodeRef.current = null
      processorNodeRef.current = null
      pcmChunksRef.current = []

      if (!merged.length) {
        setVoiceError('No audio captured. Try again and speak clearly.')
        return
      }

      const audioBlob = encodeWav(merged, sampleRate)
      const formData = new FormData()
      formData.append('file', audioBlob, 'recording.wav')

      const response = await axios.post(`${API_URL}/transcribe`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      const transcribedText = (response.data?.text || '').trim()
      if (transcribedText) {
        setInput(transcribedText)
        setVoiceError('')
        setTimeout(() => sendMessage(transcribedText), 80)
      } else {
        setVoiceError(response.data?.error || 'No speech detected. Try speaking louder and closer to mic.')
      }
    } catch (error) {
      console.error('Transcription error:', error)
      setVoiceError('Transcription failed. Ensure backend is running and Vosk model is loaded.')
    } finally {
      setIsRecording(false)
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
        // Preflight mic permission to avoid silent non-capture states.
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
          stream.getTracks().forEach(track => track.stop())
        } catch (e) {
          setVoiceError('Microphone permission denied or unavailable.')
          return
        }

        wantedRecordingRef.current = true
        manualStopRef.current = false
        freshSessionRef.current = true
        setVoiceError('')
        try {
          recognitionRef.current.start()
        } catch (e) {
          // Ignore "already started" type errors from rapid taps.
          console.debug('Recognition start ignored:', e)
        }
      }
    } else if (voiceSupport === 'fallback') {
      // Use WebAudio PCM recorder + backend
      const ok = await initializePcmRecorder()
      if (ok) {
        setVoiceError('')
        setIsRecording(true)
      }
    }
  }

  // Stop recording
  const stopRecording = () => {
    if (voiceSupport === 'native' || voiceSupport === 'webkit') {
      if (recognitionRef.current) {
        wantedRecordingRef.current = false
        manualStopRef.current = true
        recognitionRef.current.stop()
        // Send the message after a brief delay to ensure transcript is captured
        setTimeout(() => {
          const textToSend = transcriptRef.current || input.trim()
          if (textToSend) {
            setInput(textToSend)
            setTimeout(() => sendMessage(textToSend), 50)
          }
        }, 200)
      }
    } else if (voiceSupport === 'fallback') {
      if (isRecording) {
        wantedRecordingRef.current = false
        stopPcmRecorderAndTranscribe()
      }
    }
  }

  // Clear transcript when voice recognition picks up something wrong
  const clearTranscript = () => {
    setTranscript('')
    setInput('')
    setVoiceError('')
    transcriptRef.current = ''
    // If currently recording, stop and restart
    if (isRecording) {
      if (voiceSupport === 'native' || voiceSupport === 'webkit') {
        if (recognitionRef.current) {
          manualStopRef.current = false
          recognitionRef.current.stop()
          // Brief delay before restarting
          setTimeout(() => {
            if (recognitionRef.current) {
              recognitionRef.current.start()
            }
          }, 300)
        }
      } else if (voiceSupport === 'fallback') {
        if (isRecording) {
          stopPcmRecorderAndTranscribe()
        }
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
  const sendMessage = async (forcedText = null) => {
    const textToSend = (forcedText ?? input).trim()
    if (!textToSend || loading) return

    const userMessage = {
      type: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setIsThinking(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, { text: textToSend })
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
                <button
                  className="clear-transcript-button"
                  onClick={clearTranscript}
                  title="Clear incorrect transcription"
                >
                  ✕
                </button>
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
            {voiceError && (
              <div className="browser-support-badge" style={{ color: '#fca5a5', borderColor: 'rgba(239, 68, 68, 0.5)' }}>
                {voiceError}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatInterface
