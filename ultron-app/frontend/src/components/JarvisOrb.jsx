import { useEffect, useRef } from 'react'

function JarvisOrb({ speaking, intensity }) {
  const canvasRef = useRef(null)
  const frameRef = useRef(0)
  const particlesRef = useRef([])
  const speakingRef = useRef(speaking)
  const intensityRef = useRef(intensity)
  const synapsesRef = useRef([])
  const ripplesRef = useRef([])
  const prevSpeakingRef = useRef(false)
  const heatRef = useRef(0)
  const cascadeRef = useRef(null)
  const beatGateRef = useRef(false)

  useEffect(() => {
    speakingRef.current = speaking
    intensityRef.current = intensity
  }, [speaking, intensity])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return undefined
    }

    const ctx = canvas.getContext('2d')
    ctx.fillStyle = 'rgb(4, 0, 0)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    let animationId = null
    const cx = canvas.width / 2
    const cy = canvas.height / 2
    const boundaryRadius = 112

    // Initialize particles once
    if (particlesRef.current.length === 0) {
      for (let i = 0; i < 80; i += 1) {
        const angle = Math.random() * Math.PI * 2
        const dist = Math.random() * boundaryRadius * 0.8
        particlesRef.current.push({
          x: cx + Math.cos(angle) * dist,
          y: cy + Math.sin(angle) * dist,
          vx: (Math.random() - 0.5) * 0.12,
          vy: (Math.random() - 0.5) * 0.12,
          pulsePhase: Math.random() * Math.PI * 2,
          r: Math.random() + 1.5,
        })
      }
    }

    const particles = particlesRef.current

    const draw = () => {
      frameRef.current += 1
      const frame = frameRef.current
      const pulse = speakingRef.current ? Math.sin(frame * 0.18) * intensityRef.current : 0

      // Trail overdraw instead of hard clear.
      ctx.fillStyle = 'rgba(4, 0, 0, 0.18)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Static dark radial background with low alpha so trails remain visible.
      const bgGradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 140)
      bgGradient.addColorStop(0, 'rgba(40, 4, 4, 0.12)')
      bgGradient.addColorStop(1, 'rgba(4, 0, 0, 0.12)')
      ctx.fillStyle = bgGradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      const speakingStarted = speakingRef.current && !prevSpeakingRef.current
      if (speakingStarted) {
        ripplesRef.current.push({ radius: 0, alpha: 0.9, speed: 2.8 })
        ripplesRef.current.push({ radius: 0, alpha: 0.9, speed: 1.8 })
        cascadeRef.current = { waveFront: 0, speed: 1.4, maxRadius: 115 }
      }

      if (speakingRef.current && pulse > 0.7 && !beatGateRef.current) {
        cascadeRef.current = { waveFront: 0, speed: 1.4, maxRadius: 115 }
        beatGateRef.current = true
      }
      if (pulse <= 0.7) {
        beatGateRef.current = false
      }

      prevSpeakingRef.current = speakingRef.current

      if (speakingRef.current) {
        heatRef.current += (intensityRef.current - heatRef.current) * 0.08
      } else {
        heatRef.current += (0 - heatRef.current) * 0.04
      }

      // Ripples render before connection lines.
      for (let i = ripplesRef.current.length - 1; i >= 0; i -= 1) {
        const ripple = ripplesRef.current[i]
        ripple.radius += ripple.speed
        ripple.alpha *= 0.96

        ctx.beginPath()
        ctx.arc(cx, cy, ripple.radius, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(255, 80, 40, ${ripple.alpha})`
        ctx.lineWidth = 1.5
        ctx.stroke()

        if (ripple.radius > 130 || ripple.alpha < 0.02) {
          ripplesRef.current.splice(i, 1)
        }
      }

      // Update particle physics
      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i]

        if (speakingRef.current) {
          // Breathing pulse: expand and contract from center
          p.vx += (p.x - cx) * 0.0012 * pulse
          p.vy += (p.y - cy) * 0.0012 * pulse
          p.vx += (Math.random() - 0.5) * intensityRef.current * 0.15
          p.vy += (Math.random() - 0.5) * intensityRef.current * 0.15

          const speed = Math.hypot(p.vx, p.vy)
          if (speed > 1.6) {
            const scale = 1.6 / speed
            p.vx *= scale
            p.vy *= scale
          }

          p.vx *= 0.975
          p.vy *= 0.975
        } else {
          p.vx *= 0.98
          p.vy *= 0.98

          const speed = Math.hypot(p.vx, p.vy)
          if (speed < 0.08) {
            p.vx += (Math.random() - 0.5) * 0.12
            p.vy += (Math.random() - 0.5) * 0.12
          }

          const cappedSpeed = Math.hypot(p.vx, p.vy)
          if (cappedSpeed > 0.35) {
            const scale = 0.35 / cappedSpeed
            p.vx *= scale
            p.vy *= scale
          }
        }

        p.x += p.vx
        p.y += p.vy
        if (!speakingRef.current) {
          p.x += Math.sin(frame * 0.008 + p.pulsePhase) * 0.06
          p.y += Math.cos(frame * 0.007 + p.pulsePhase * 1.3) * 0.06
        }

        const dx = p.x - cx
        const dy = p.y - cy
        const dist = Math.hypot(dx, dy)
        if (dist > boundaryRadius) {
          const angle = Math.atan2(dy, dx)
          p.x = cx + Math.cos(angle) * boundaryRadius
          p.y = cy + Math.sin(angle) * boundaryRadius
          p.vx *= -0.5
          p.vy *= -0.5
        }
      }

      // Connection lines
      let lineAlpha = 0.28
      let lineDistance = 68
      if (speakingRef.current && pulse > 0.3) {
        lineAlpha = 0.55
        lineDistance = 85
      }

      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const p1 = particles[i]
          const p2 = particles[j]
          const dx = p2.x - p1.x
          const dy = p2.y - p1.y
          const distance = Math.hypot(dx, dy)
          if (distance < lineDistance) {
            ctx.beginPath()
            ctx.moveTo(p1.x, p1.y)
            ctx.lineTo(p2.x, p2.y)
            ctx.strokeStyle = `rgba(180, 30, 30, ${lineAlpha})`
            ctx.lineWidth = 0.5
            ctx.stroke()

            if (cascadeRef.current) {
              const midX = (p1.x + p2.x) / 2
              const midY = (p1.y + p2.y) / 2
              const midDist = Math.hypot(midX - cx, midY - cy)
              const bandDelta = Math.abs(midDist - cascadeRef.current.waveFront)
              if (bandDelta < 18) {
                const cascadeAlpha = (1 - bandDelta / 18) * 0.85
                ctx.beginPath()
                ctx.moveTo(p1.x, p1.y)
                ctx.lineTo(p2.x, p2.y)
                ctx.strokeStyle = `rgba(255, 120, 60, ${cascadeAlpha})`
                ctx.lineWidth = 1.0
                ctx.stroke()
              }
            }
          }
        }
      }

      if (cascadeRef.current) {
        cascadeRef.current.waveFront += cascadeRef.current.speed
        if (cascadeRef.current.waveFront > cascadeRef.current.maxRadius) {
          cascadeRef.current = null
        }
      }

      // Random synapse flashes render after connection lines.
      if (synapsesRef.current.length < 4) {
        const spawnChance = speakingRef.current ? 0.002 : 0.008
        if (Math.random() < spawnChance) {
          for (let attempt = 0; attempt < 8; attempt += 1) {
            const i = Math.floor(Math.random() * particles.length)
            const j = Math.floor(Math.random() * particles.length)
            if (i === j) {
              continue
            }
            const p1 = particles[i]
            const p2 = particles[j]
            const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y)
            if (dist <= 90) {
              synapsesRef.current.push({ i, j, alpha: 1.0, decay: 0.035 })
              break
            }
          }
        }
      }

      for (let i = synapsesRef.current.length - 1; i >= 0; i -= 1) {
        const synapse = synapsesRef.current[i]
        const p1 = particles[synapse.i]
        const p2 = particles[synapse.j]
        if (!p1 || !p2) {
          synapsesRef.current.splice(i, 1)
          continue
        }

        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.strokeStyle = `rgba(255, 160, 60, ${synapse.alpha})`
        ctx.lineWidth = 1.2
        ctx.stroke()

        synapse.alpha -= synapse.decay
        if (synapse.alpha <= 0) {
          synapsesRef.current.splice(i, 1)
        }
      }

      // Draw particles
      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i]
        const displayR = speakingRef.current ? p.r + Math.abs(pulse) * 2.2 : p.r
        ctx.beginPath()
        ctx.arc(p.x, p.y, displayR, 0, Math.PI * 2)
        if (speakingRef.current) {
          const distFromCenter = Math.hypot(p.x - cx, p.y - cy) / 112
          const coreHeat = Math.max(0, Math.min(1, heatRef.current - distFromCenter * 0.7))
          const r = Math.floor(220 + coreHeat * 35)
          const g = Math.floor(50 + coreHeat * 120)
          const b = Math.floor(40 + coreHeat * 30)
          const a = 0.75 + coreHeat * 0.25
          ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a})`
          if (Math.abs(pulse) > 0.5 && intensityRef.current > 0.4) {
            ctx.shadowBlur = 10
            ctx.shadowColor = 'rgba(255,60,40,0.8)'
          }
        } else {
          ctx.fillStyle = 'rgba(220, 50, 40, 0.75)'
        }
        ctx.fill()
        // Reset immediately after each particle draw
        ctx.shadowBlur = 0
        ctx.shadowColor = 'transparent'
      }

      animationId = requestAnimationFrame(draw)
    }

    animationId = requestAnimationFrame(draw)

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    }
  }, [])

  return <canvas className="jarvis-orb" ref={canvasRef} width={280} height={280} />
}

export default JarvisOrb
