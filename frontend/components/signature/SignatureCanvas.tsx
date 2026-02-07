'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Eraser } from 'lucide-react'

interface SignatureCanvasProps {
  onSignatureChange: (signatureDataUrl: string | null) => void
  label?: string
  clearLabel?: string
  hintLabel?: string
}

const SignatureCanvas = ({
  onSignatureChange,
  label = 'Sign below',
  clearLabel = 'Clear',
  hintLabel = 'Use mouse or finger to sign'
}: SignatureCanvasProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const isDrawingRef = useRef(false)
  const [hasSignature, setHasSignature] = useState(false)
  const lastPointRef = useRef<{ x: number; y: number } | null>(null)

  // Initialize canvas
  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Get the actual display size
    const rect = canvas.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1

    // Set canvas internal size based on device pixel ratio
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr

    // Scale for retina displays
    ctx.scale(dpr, dpr)

    // Set drawing style
    ctx.strokeStyle = '#1a1a1a'
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    // Fill with white background
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, rect.width, rect.height)
  }, [])

  useEffect(() => {
    initCanvas()

    // Re-initialize on resize
    const handleResize = () => initCanvas()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [initCanvas])

  // Get coordinates from mouse or touch event
  const getCoordinates = useCallback((e: MouseEvent | TouchEvent | React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }

    const rect = canvas.getBoundingClientRect()

    // Handle touch events
    if ('touches' in e && e.touches.length > 0) {
      return {
        x: e.touches[0].clientX - rect.left,
        y: e.touches[0].clientY - rect.top,
      }
    }

    // Handle mouse events
    if ('clientX' in e) {
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      }
    }

    return { x: 0, y: 0 }
  }, [])

  // Start drawing
  const startDrawing = useCallback((e: MouseEvent | TouchEvent | React.MouseEvent | React.TouchEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!ctx || !canvas) return

    isDrawingRef.current = true
    const { x, y } = getCoordinates(e)
    lastPointRef.current = { x, y }

    // Start a new path
    ctx.beginPath()
    ctx.moveTo(x, y)

    // Draw a dot for single click/tap
    ctx.lineTo(x + 0.1, y + 0.1)
    ctx.stroke()
  }, [getCoordinates])

  // Draw line
  const draw = useCallback((e: MouseEvent | TouchEvent | React.MouseEvent | React.TouchEvent) => {
    if (!isDrawingRef.current) return

    e.preventDefault()
    e.stopPropagation()

    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!ctx || !canvas) return

    const { x, y } = getCoordinates(e)

    // Draw from last point to current point
    if (lastPointRef.current) {
      ctx.beginPath()
      ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y)
      ctx.lineTo(x, y)
      ctx.stroke()
    }

    lastPointRef.current = { x, y }
    setHasSignature(true)
  }, [getCoordinates])

  // Stop drawing - capture signature immediately
  const stopDrawing = useCallback(() => {
    if (isDrawingRef.current) {
      isDrawingRef.current = false
      lastPointRef.current = null

      // Always capture signature after drawing stops
      const canvas = canvasRef.current
      if (canvas) {
        setHasSignature(true)
        const dataUrl = canvas.toDataURL('image/png')
        onSignatureChange(dataUrl)
      }
    }
  }, [onSignatureChange])

  // Add event listeners for mouse events outside React
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const handleMouseDown = (e: MouseEvent) => startDrawing(e)
    const handleMouseMove = (e: MouseEvent) => draw(e)
    const handleMouseUp = () => stopDrawing()
    const handleMouseLeave = () => stopDrawing()

    const handleTouchStart = (e: TouchEvent) => startDrawing(e)
    const handleTouchMove = (e: TouchEvent) => draw(e)
    const handleTouchEnd = () => stopDrawing()

    // Mouse events
    canvas.addEventListener('mousedown', handleMouseDown)
    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseup', handleMouseUp)
    canvas.addEventListener('mouseleave', handleMouseLeave)

    // Touch events
    canvas.addEventListener('touchstart', handleTouchStart, { passive: false })
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false })
    canvas.addEventListener('touchend', handleTouchEnd)

    // Global mouse up to handle drawing outside canvas
    window.addEventListener('mouseup', handleMouseUp)

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown)
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('mouseup', handleMouseUp)
      canvas.removeEventListener('mouseleave', handleMouseLeave)
      canvas.removeEventListener('touchstart', handleTouchStart)
      canvas.removeEventListener('touchmove', handleTouchMove)
      canvas.removeEventListener('touchend', handleTouchEnd)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [startDrawing, draw, stopDrawing])

  const clearSignature = () => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!ctx || !canvas) return

    const rect = canvas.getBoundingClientRect()
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, rect.width, rect.height)
    setHasSignature(false)
    onSignatureChange(null)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">{label}</p>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={clearSignature}
          className="gap-1 text-gray-500"
        >
          <Eraser className="w-4 h-4" />
          {clearLabel}
        </Button>
      </div>
      <div className="border-2 border-primary-500 rounded-lg overflow-hidden bg-white shadow-lg">
        <canvas
          ref={canvasRef}
          className="w-full h-40 cursor-crosshair touch-none"
          style={{ touchAction: 'none', minHeight: '150px' }}
        />
      </div>
      <p className="text-xs text-gray-500 text-center">
        {hintLabel}
      </p>
    </div>
  )
}

export default SignatureCanvas
