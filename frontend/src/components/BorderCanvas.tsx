import { useRef, useEffect, useState } from 'react'

interface BorderCircle {
  type: 'circle'
  center: { x: number; y: number }
  radius: number
  confidence?: number
}

interface BorderEllipse {
  type: 'ellipse'
  center: { x: number; y: number }
  axes: { major: number; minor: number }
  angle: number
  confidence?: number
}

type BorderInfo = BorderCircle | BorderEllipse

interface BorderCanvasProps {
  border: BorderInfo | null
  imageRef: React.RefObject<HTMLImageElement | null>
  canvasRef?: React.RefObject<HTMLCanvasElement | null>
  showBorder?: boolean
  isSelected?: boolean
  isResizeMode?: boolean
  interactive?: boolean
  onMouseDown?: (e: React.MouseEvent<HTMLCanvasElement>) => void
  onMouseMove?: (e: React.MouseEvent<HTMLCanvasElement>) => void
  onMouseUp?: (e: React.MouseEvent<HTMLCanvasElement>) => void
  className?: string
}

export function BorderCanvas({
  border,
  imageRef,
  canvasRef: externalCanvasRef,
  showBorder = true,
  isSelected = false,
  isResizeMode = false,
  interactive = false,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  className = ''
}: BorderCanvasProps) {
  const internalCanvasRef = useRef<HTMLCanvasElement>(null)
  const canvasRef = externalCanvasRef || internalCanvasRef
  const [canvasStyle, setCanvasStyle] = useState<{ top: number; left: number; width: number; height: number } | null>(null)

  // Update canvas position to match image
  useEffect(() => {
    const updateCanvasPosition = () => {
      const image = imageRef.current
      if (!image) return

      const imageRect = image.getBoundingClientRect()
      const containerRect = image.parentElement?.getBoundingClientRect()

      if (containerRect) {
        setCanvasStyle({
          top: imageRect.top - containerRect.top,
          left: imageRect.left - containerRect.left,
          width: imageRect.width,
          height: imageRect.height
        })
      }
    }

    const image = imageRef.current
    if (image?.complete) {
      updateCanvasPosition()
    } else if (image) {
      image.addEventListener('load', updateCanvasPosition)
      return () => image.removeEventListener('load', updateCanvasPosition)
    }

    window.addEventListener('resize', updateCanvasPosition)
    return () => window.removeEventListener('resize', updateCanvasPosition)
  }, [imageRef])

  // Draw border on canvas
  useEffect(() => {
    if (!border || !showBorder) {
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d')
        if (ctx) {
          ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height)
        }
      }
      return
    }

    const image = imageRef.current
    const canvas = canvasRef.current

    if (!image || !canvas) return

    const drawBorder = () => {
      const { width, height } = image.getBoundingClientRect()
      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.clearRect(0, 0, width, height)

      // Calculate scale factors
      const scaleX = width / image.naturalWidth
      const scaleY = height / image.naturalHeight

      // Draw border with selection highlight (if interactive)
      ctx.strokeStyle = interactive && isSelected ? '#22c55e' : '#646cff'
      ctx.lineWidth = interactive && isSelected ? 4 : 3

      if (border.type === 'circle') {
        // Use uniform scaling to maintain circle shape
        const scale = Math.min(scaleX, scaleY)
        const centerX = border.center.x * scale
        const centerY = border.center.y * scale
        const radius = border.radius * scale

        ctx.beginPath()
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
        ctx.stroke()

        // Draw center point
        ctx.fillStyle = interactive && isSelected ? '#22c55e' : '#646cff'
        ctx.beginPath()
        ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI)
        ctx.fill()

        // Draw resize handle if in resize mode (only in interactive mode)
        if (interactive && isResizeMode && isSelected) {
          ctx.fillStyle = '#f59e0b'
          ctx.beginPath()
          ctx.arc(centerX, centerY, 10, 0, 2 * Math.PI)
          ctx.fill()
          ctx.strokeStyle = '#fff'
          ctx.lineWidth = 2
          ctx.stroke()
        }
      } else {
        const centerX = border.center.x * scaleX
        const centerY = border.center.y * scaleY
        const radiusX = border.axes.major * scaleX
        const radiusY = border.axes.minor * scaleY
        const rotation = (border.angle * Math.PI) / 180

        ctx.beginPath()
        ctx.ellipse(centerX, centerY, radiusX, radiusY, rotation, 0, 2 * Math.PI)
        ctx.stroke()

        // Draw center point
        ctx.fillStyle = interactive && isSelected ? '#22c55e' : '#646cff'
        ctx.beginPath()
        ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI)
        ctx.fill()

        // Draw resize handle if in resize mode (only in interactive mode)
        if (interactive && isResizeMode && isSelected) {
          ctx.fillStyle = '#f59e0b'
          ctx.beginPath()
          ctx.arc(centerX, centerY, 10, 0, 2 * Math.PI)
          ctx.fill()
          ctx.strokeStyle = '#fff'
          ctx.lineWidth = 2
          ctx.stroke()
        }
      }
    }

    if (image.complete) {
      drawBorder()
    } else {
      image.addEventListener('load', drawBorder)
      return () => image.removeEventListener('load', drawBorder)
    }

    // Add window resize listener for responsive rendering
    const handleResize = () => {
      if (image.complete) {
        drawBorder()
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [border, showBorder, isSelected, isResizeMode, interactive, imageRef])

  return (
    <canvas
      ref={canvasRef}
      className={`border-canvas ${className}`}
      onMouseDown={interactive ? onMouseDown : undefined}
      onMouseMove={interactive ? onMouseMove : undefined}
      onMouseUp={interactive ? onMouseUp : undefined}
      style={{
        position: 'absolute',
        top: canvasStyle?.top ?? 0,
        left: canvasStyle?.left ?? 0,
        width: canvasStyle?.width ?? '100%',
        height: canvasStyle?.height ?? '100%',
        pointerEvents: interactive ? 'auto' : 'none'
      }}
    />
  )
}
