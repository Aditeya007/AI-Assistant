import { useEffect, useRef } from 'react'

const MIN_PARTICLES = 120
const MAX_PARTICLES = 140

function randomRed() {
  const shades = [
    [204, 34, 34],
    [163, 27, 27],
    [239, 68, 68],
    [122, 20, 20]
  ]
  return shades[Math.floor(Math.random() * shades.length)]
}

function spawnParticle(width, height) {
  const [r, g, b] = randomRed()
  return {
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.45,
    vy: (Math.random() - 0.5) * 0.45,
    life: Math.random() * 0.9 + 0.1,
    radius: Math.random() * 1.4 + 0.5,
    r,
    g,
    b
  }
}

function ParticleField({ speaking, intensity }) {
  const canvasRef = useRef(null)
  const particlesRef = useRef([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !canvas.parentElement) {
      return undefined
    }

    const ctx = canvas.getContext('2d')
    let width = 0
    let height = 0
    let animationId = null

    const resize = () => {
      width = canvas.parentElement.clientWidth
      height = canvas.parentElement.clientHeight
      canvas.width = width
      canvas.height = height

      const targetCount = Math.floor(MIN_PARTICLES + Math.random() * (MAX_PARTICLES - MIN_PARTICLES + 1))
      particlesRef.current = Array.from({ length: targetCount }, () => spawnParticle(width, height))
    }

    const observer = new ResizeObserver(resize)
    observer.observe(canvas.parentElement)
    resize()

    const tick = () => {
      const particles = particlesRef.current
      const speedScale = speaking ? 1.4 + intensity * 0.7 : 0.75
      const maxDistance = speaking ? 80 : 65

      ctx.clearRect(0, 0, width, height)

      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i]
        p.x += p.vx * speedScale
        p.y += p.vy * speedScale
        p.life -= 0.0026

        if (p.life <= 0 || p.x < -20 || p.x > width + 20 || p.y < -20 || p.y > height + 20) {
          particles[i] = spawnParticle(width, height)
          continue
        }

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius + (speaking ? intensity * 0.6 : 0), 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${p.r}, ${p.g}, ${p.b}, ${0.2 + p.life * 0.5})`
        if (speaking) {
          ctx.shadowColor = 'rgba(239, 68, 68, 0.65)'
          ctx.shadowBlur = 8 + intensity * 9
        } else {
          ctx.shadowBlur = 0
        }
        ctx.fill()
      }

      ctx.shadowBlur = 0

      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const a = particles[i]
          const b = particles[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const distance = Math.hypot(dx, dy)

          if (distance < maxDistance) {
            const alpha = (1 - distance / maxDistance) * (speaking ? 0.34 : 0.22)
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.strokeStyle = `rgba(239, 68, 68, ${alpha})`
            ctx.lineWidth = speaking ? 1.05 : 0.8
            ctx.stroke()
          }
        }
      }

      animationId = requestAnimationFrame(tick)
    }

    animationId = requestAnimationFrame(tick)

    return () => {
      observer.disconnect()
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    }
  }, [speaking, intensity])

  return <canvas className="particle-field" ref={canvasRef} />
}

export default ParticleField
