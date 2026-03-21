import { useEffect, useRef } from 'react'

const BAR_COUNT = 40

function lerp(a, b, t) {
  return a + (b - a) * t
}

function roundedBar(ctx, x, y, w, h, r) {
  const radius = Math.min(r, w / 2, Math.abs(h) / 2)
  const sign = h >= 0 ? 1 : -1
  const hh = Math.abs(h)

  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + w - radius, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + sign * radius)
  ctx.lineTo(x + w, y + sign * (hh - radius))
  ctx.quadraticCurveTo(x + w, y + sign * hh, x + w - radius, y + sign * hh)
  ctx.lineTo(x + radius, y + sign * hh)
  ctx.quadraticCurveTo(x, y + sign * hh, x, y + sign * (hh - radius))
  ctx.lineTo(x, y + sign * radius)
  ctx.quadraticCurveTo(x, y, x + radius, y)
  ctx.closePath()
}

function VoiceWaveform({ speaking, intensity }) {
  const canvasRef = useRef(null)
  const barsRef = useRef(Array.from({ length: BAR_COUNT }, () => 0))

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return undefined
    }

    const ctx = canvas.getContext('2d')
    let frame = 0
    let animationId = null

    const draw = () => {
      frame += 1
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const centerY = canvas.height / 2
      const barWidth = 6
      const gap = 4
      const totalWidth = BAR_COUNT * (barWidth + gap)
      const startX = (canvas.width - totalWidth) / 2

      for (let i = 0; i < BAR_COUNT; i += 1) {
        const waveA = Math.sin(frame * 0.11 + i * 0.42)
        const waveB = Math.sin(frame * 0.052 + i * 0.18 + 2)
        const waveC = Math.sin(frame * 0.079 + i * 0.31 + 1.3)
        const blend = (waveA * 0.5 + waveB * 0.32 + waveC * 0.28 + 1) / 2

        const target = speaking
          ? (5 + blend * 26) * (0.65 + intensity * 0.7)
          : Math.random() * 1.4

        barsRef.current[i] = lerp(barsRef.current[i], target, speaking ? 0.32 : 0.12)

        const x = startX + i * (barWidth + gap)
        const height = barsRef.current[i]
        const highEnergy = speaking && height > 18

        ctx.fillStyle = 'rgba(239, 68, 68, 0.95)'
        if (highEnergy) {
          ctx.shadowColor = 'rgba(239, 68, 68, 0.9)'
          ctx.shadowBlur = 10
        } else {
          ctx.shadowBlur = 0
        }

        roundedBar(ctx, x, centerY, barWidth, -height, 3)
        ctx.fill()
        roundedBar(ctx, x, centerY, barWidth, height, 3)
        ctx.fill()
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

  return (
    <div className={`waveform-wrap ${speaking ? 'active' : ''}`}>
      <canvas className="voice-waveform" ref={canvasRef} width={400} height={48} />
    </div>
  )
}

export default VoiceWaveform
