import { useEffect, useRef } from 'react'

function JarvisOrb({ speaking, intensity }) {
  const canvasRef = useRef(null)
  const frameRef = useRef(0)
  const particlesRef = useRef([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return undefined
    }

    const ctx = canvas.getContext('2d')
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
      const pulse = speaking ? Math.sin(frame * 0.18) * intensity : 0

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Static dark radial background
      const bgGradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 140)
      bgGradient.addColorStop(0, 'rgba(40, 4, 4, 0.9)')
      bgGradient.addColorStop(1, 'rgba(4, 0, 0, 0.98)')
      ctx.fillStyle = bgGradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Update particle physics
      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i]

        if (speaking) {
          // Breathing pulse: expand and contract from center
          p.vx += (p.x - cx) * 0.0012 * pulse
          p.vy += (p.y - cy) * 0.0012 * pulse
          p.vx += (Math.random() - 0.5) * intensity * 0.15
          p.vy += (Math.random() - 0.5) * intensity * 0.15

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
        if (!speaking) {
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
      if (speaking && pulse > 0.3) {
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
          }
        }
      }

      // Draw particles
      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i]
        const displayR = speaking ? p.r + Math.abs(pulse) * 2.2 : p.r
        ctx.beginPath()
        ctx.arc(p.x, p.y, displayR, 0, Math.PI * 2)
        if (speaking) {
          ctx.fillStyle = `rgba(255, 70, 50, ${0.75 + Math.abs(pulse) * 0.25})`
          if (Math.abs(pulse) > 0.5 && intensity > 0.4) {
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
  }, [speaking, intensity])

  return <canvas className="jarvis-orb" ref={canvasRef} width={280} height={280} />
}

export default JarvisOrb
