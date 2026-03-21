import { useEffect, useRef } from 'react'

function drawHex(ctx, cx, cy, radius, rotation, alpha) {
  ctx.save()
  ctx.translate(cx, cy)
  ctx.rotate(rotation)
  ctx.beginPath()
  for (let i = 0; i < 6; i += 1) {
    const angle = (Math.PI / 3) * i
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius
    if (i === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  }
  ctx.closePath()
  ctx.strokeStyle = `rgba(239, 68, 68, ${alpha})`
  ctx.lineWidth = 1.2
  ctx.shadowColor = 'rgba(239, 68, 68, 0.5)'
  ctx.shadowBlur = 12
  ctx.stroke()
  ctx.restore()
}

function drawOrbitDots(ctx, cx, cy, radius, frame, speed, size, speaking) {
  const dotCount = 16
  for (let i = 0; i < dotCount; i += 1) {
    const phase = frame * speed + (i / dotCount) * Math.PI * 2
    const depth = Math.cos(phase)
    const x = cx + Math.cos(phase) * radius
    const y = cy + Math.sin(phase) * radius * 0.38

    const alpha = depth > 0 ? 0.82 : 0.2
    const dotRadius = size * (depth > 0 ? 1.08 : 0.75)

    ctx.beginPath()
    ctx.arc(x, y, dotRadius, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(239, 68, 68, ${alpha})`
    if (speaking && depth > 0) {
      ctx.shadowColor = 'rgba(239, 68, 68, 0.85)'
      ctx.shadowBlur = 15
    } else {
      ctx.shadowBlur = 0
    }
    ctx.fill()
  }
}

function JarvisOrb({ speaking, intensity }) {
  const canvasRef = useRef(null)
  const frameRef = useRef(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return undefined
    }

    const ctx = canvas.getContext('2d')
    let animationId = null

    const draw = () => {
      frameRef.current += 1
      const frame = frameRef.current
      const baseSpeed = speaking ? 0.025 : 0.012
      const speedBoost = speaking ? intensity * 0.018 : 0
      const spinSpeed = baseSpeed + speedBoost

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const cx = canvas.width / 2
      const cy = canvas.height / 2
      const pulse = 0.5 + Math.sin(frame * 0.045) * 0.5
      const coreRadius = speaking ? 30 + pulse * 22 + intensity * 9 : 26 + pulse * 16

      const coreGradient = ctx.createRadialGradient(cx, cy, 10, cx, cy, 92)
      coreGradient.addColorStop(0, `rgba(239, 68, 68, ${0.2 + pulse * 0.35})`)
      coreGradient.addColorStop(0.6, 'rgba(204, 34, 34, 0.24)')
      coreGradient.addColorStop(1, 'rgba(204, 34, 34, 0)')

      ctx.beginPath()
      ctx.arc(cx, cy, coreRadius + 25, 0, Math.PI * 2)
      ctx.fillStyle = coreGradient
      ctx.fill()

      drawHex(ctx, cx, cy, 112, frame * spinSpeed, 0.9)
      drawHex(ctx, cx, cy, 88, -frame * spinSpeed * 0.78, 0.68)
      drawHex(ctx, cx, cy, 62, frame * spinSpeed * 1.12, 0.54)

      const dotSize = speaking ? 2.8 + intensity * 1.8 : 2.1
      drawOrbitDots(ctx, cx, cy, 95, frame, spinSpeed * 1.4, dotSize, speaking)
      drawOrbitDots(ctx, cx, cy, 70, frame, -spinSpeed * 1.9, dotSize * 0.94, speaking)
      drawOrbitDots(ctx, cx, cy, 48, frame, spinSpeed * 2.6, dotSize * 0.88, speaking)

      const scanY = ((frame * 0.8) % (canvas.height + 40)) - 20
      const scanGradient = ctx.createLinearGradient(0, scanY - 10, 0, scanY + 12)
      scanGradient.addColorStop(0, 'rgba(239, 68, 68, 0)')
      scanGradient.addColorStop(0.45, 'rgba(239, 68, 68, 0.22)')
      scanGradient.addColorStop(1, 'rgba(239, 68, 68, 0)')
      ctx.fillStyle = scanGradient
      ctx.fillRect(10, scanY - 10, canvas.width - 20, 22)

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
