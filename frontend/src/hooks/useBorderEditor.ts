import { useState, useCallback } from 'react'
import type { RefObject } from 'react'
import type { BorderInfo } from '../types/disc'

interface UseBorderEditorProps {
  initialBorder: BorderInfo | null
  imageDimensions: { width: number; height: number } | null
  canvasRef: RefObject<HTMLCanvasElement | null>
  imageRef: RefObject<HTMLImageElement | null>
}

interface UseBorderEditorReturn {
  // Border state
  currentBorder: BorderInfo | null
  originalBorder: BorderInfo | null
  hasChanges: boolean
  isSelected: boolean
  isResizeMode: boolean
  showBorder: boolean

  // Setters
  setCurrentBorder: (border: BorderInfo | null) => void
  setOriginalBorder: (border: BorderInfo | null) => void
  setHasChanges: (hasChanges: boolean) => void
  setShowBorder: (show: boolean) => void

  // Interaction state
  isDraggingBorder: boolean
  isResizing: boolean

  // Actions
  handleAddBorder: () => void
  handleDeleteBorder: () => void
  handleResetBorder: () => void
  handleResizeMode: () => void

  // Mouse handlers
  handleCanvasMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void
  handleCanvasMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void
  handleCanvasMouseUp: () => void

  // Button states
  addBorderEnabled: boolean
  deleteBorderEnabled: boolean
  resizeEnabled: boolean
  resetEnabled: boolean
  saveBorderEnabled: boolean

  // Helpers
  isBorderWithinBounds: (border: BorderInfo) => boolean
}

export function useBorderEditor({
  initialBorder,
  imageDimensions,
  canvasRef,
  imageRef,
}: UseBorderEditorProps): UseBorderEditorReturn {
  // Border state
  const [originalBorder, setOriginalBorder] = useState<BorderInfo | null>(initialBorder)
  const [currentBorder, setCurrentBorder] = useState<BorderInfo | null>(initialBorder)
  const [isSelected, setIsSelected] = useState<boolean>(false)
  const [isResizeMode, setIsResizeMode] = useState<boolean>(false)
  const [hasChanges, setHasChanges] = useState<boolean>(false)
  const [showBorder, setShowBorder] = useState<boolean>(true)

  // Interaction state
  const [isDraggingBorder, setIsDraggingBorder] = useState<boolean>(false)
  const [isResizing, setIsResizing] = useState<boolean>(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number; borderX: number; borderY: number } | null>(null)
  const [resizeStart, setResizeStart] = useState<{ y: number; initialSize: number } | null>(null)

  // Helper: Convert canvas coordinates to image coordinates
  const canvasToImageCoords = useCallback((canvasX: number, canvasY: number): { x: number; y: number } => {
    const canvas = canvasRef.current
    const image = imageRef.current
    if (!canvas || !image) return { x: 0, y: 0 }

    const rect = canvas.getBoundingClientRect()
    const scale = Math.max(image.naturalWidth / rect.width, image.naturalHeight / rect.height)

    return {
      x: canvasX * scale,
      y: canvasY * scale
    }
  }, [canvasRef, imageRef])

  // Helper: Check if point is on border ring
  const isPointOnBorderRing = useCallback((canvasX: number, canvasY: number, border: BorderInfo, inResizeMode: boolean = false): boolean => {
    const image = imageRef.current
    if (!image) return false

    const rect = image.getBoundingClientRect()
    const scale = Math.min(rect.width / image.naturalWidth, rect.height / image.naturalHeight)

    const centerX = border.center.x * scale
    const centerY = border.center.y * scale
    const tolerance = 15

    if (border.type === 'circle') {
      const radius = border.radius * scale
      const distance = Math.sqrt(
        Math.pow(canvasX - centerX, 2) + Math.pow(canvasY - centerY, 2)
      )

      if (inResizeMode) {
        return Math.abs(distance - radius) <= tolerance
      } else {
        return distance <= radius + tolerance
      }
    } else {
      const radiusX = border.axes.major * scale
      const radiusY = border.axes.minor * scale
      const angle = border.angle * Math.PI / 180

      const dx = canvasX - centerX
      const dy = canvasY - centerY
      const rotX = dx * Math.cos(-angle) - dy * Math.sin(-angle)
      const rotY = dx * Math.sin(-angle) + dy * Math.cos(-angle)

      const ellipseValue = (rotX * rotX) / (radiusX * radiusX) +
                          (rotY * rotY) / (radiusY * radiusY)
      const normalizedDistance = Math.sqrt(ellipseValue)

      if (inResizeMode) {
        return Math.abs(normalizedDistance - 1) * Math.max(radiusX, radiusY) <= tolerance
      } else {
        return normalizedDistance <= 1 + (tolerance / Math.max(radiusX, radiusY))
      }
    }
  }, [imageRef])

  // Helper: Check if point is on resize handle
  const isPointOnResizeHandle = useCallback((canvasX: number, canvasY: number, border: BorderInfo): boolean => {
    if (!isResizeMode) return false

    const image = imageRef.current
    if (!image) return false

    const rect = image.getBoundingClientRect()
    const scale = Math.min(rect.width / image.naturalWidth, rect.height / image.naturalHeight)

    const centerX = border.center.x * scale
    const centerY = border.center.y * scale

    const distance = Math.sqrt(
      Math.pow(canvasX - centerX, 2) + Math.pow(canvasY - centerY, 2)
    )

    return distance <= 15
  }, [isResizeMode, imageRef])

  // Helper: Constrain border to image bounds
  const constrainBorderToImage = useCallback((border: BorderInfo): BorderInfo => {
    if (!imageDimensions) return border

    const minSize = 50
    const maxSize = Math.min(imageDimensions.width, imageDimensions.height) / 2

    if (border.type === 'circle') {
      let { center, radius } = border
      radius = Math.max(minSize, Math.min(maxSize, radius))
      center = {
        x: Math.max(radius, Math.min(imageDimensions.width - radius, center.x)),
        y: Math.max(radius, Math.min(imageDimensions.height - radius, center.y))
      }
      return { ...border, center, radius }
    } else {
      let { center, axes } = border
      const maxAxis = Math.max(axes.major, axes.minor)

      if (maxAxis > maxSize) {
        const scale = maxSize / maxAxis
        axes = { major: axes.major * scale, minor: axes.minor * scale }
      }

      if (axes.major < minSize) {
        const scale = minSize / axes.major
        axes = { major: axes.major * scale, minor: axes.minor * scale }
      }

      const maxRadius = Math.max(axes.major, axes.minor)
      center = {
        x: Math.max(maxRadius, Math.min(imageDimensions.width - maxRadius, center.x)),
        y: Math.max(maxRadius, Math.min(imageDimensions.height - maxRadius, center.y))
      }

      return { ...border, center, axes }
    }
  }, [imageDimensions])

  // Helper: Check if border is within image bounds
  const isBorderWithinBounds = useCallback((border: BorderInfo): boolean => {
    if (!imageDimensions) return false

    const { x, y } = border.center
    if (border.type === 'circle') {
      const r = border.radius
      return x - r >= 0 && y - r >= 0 && x + r <= imageDimensions.width && y + r <= imageDimensions.height
    } else {
      const rx = border.axes.major
      const ry = border.axes.minor
      const maxR = Math.max(rx, ry)
      return x - maxR >= 0 && y - maxR >= 0 && x + maxR <= imageDimensions.width && y + maxR <= imageDimensions.height
    }
  }, [imageDimensions])

  // Actions
  const handleAddBorder = useCallback(() => {
    if (!imageDimensions) return

    const radius = (Math.min(imageDimensions.width, imageDimensions.height) - 100) / 2
    const newBorder: BorderInfo = {
      type: 'circle',
      center: {
        x: imageDimensions.width / 2,
        y: imageDimensions.height / 2
      },
      radius
    }

    setCurrentBorder(newBorder)
    setHasChanges(true)
    setIsSelected(true)
  }, [imageDimensions])

  const handleDeleteBorder = useCallback(() => {
    setCurrentBorder(null)
    setIsSelected(false)
    setIsResizeMode(false)
    setHasChanges(true)
  }, [])

  const handleResetBorder = useCallback(() => {
    if (originalBorder) {
      setCurrentBorder({ ...originalBorder })
      setHasChanges(false)
      setIsSelected(false)
      setIsResizeMode(false)
    }
  }, [originalBorder])

  const handleResizeMode = useCallback(() => {
    setIsResizeMode(!isResizeMode)
  }, [isResizeMode])

  // Mouse handlers
  const handleCanvasMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!currentBorder || !canvasRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top

    if (isPointOnResizeHandle(canvasX, canvasY, currentBorder)) {
      const imageCoords = canvasToImageCoords(canvasX, canvasY)
      setIsResizing(true)
      const initialSize = currentBorder.type === 'circle'
        ? currentBorder.radius
        : Math.max(currentBorder.axes.major, currentBorder.axes.minor)
      setResizeStart({ y: imageCoords.y, initialSize })
      return
    }

    if (isPointOnBorderRing(canvasX, canvasY, currentBorder, isResizeMode)) {
      const imageCoords = canvasToImageCoords(canvasX, canvasY)
      setIsSelected(true)
      setIsDraggingBorder(true)
      setDragStart({
        x: imageCoords.x,
        y: imageCoords.y,
        borderX: currentBorder.center.x,
        borderY: currentBorder.center.y
      })
      return
    }

    setIsSelected(false)
    setIsResizeMode(false)
  }, [currentBorder, canvasRef, isResizeMode, isPointOnResizeHandle, isPointOnBorderRing, canvasToImageCoords])

  const handleCanvasMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!currentBorder || !canvasRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top
    const imageCoords = canvasToImageCoords(canvasX, canvasY)

    if (isDraggingBorder && dragStart) {
      const dx = imageCoords.x - dragStart.x
      const dy = imageCoords.y - dragStart.y

      const newBorder = {
        ...currentBorder,
        center: {
          x: dragStart.borderX + dx,
          y: dragStart.borderY + dy
        }
      }

      const constrained = constrainBorderToImage(newBorder)
      setCurrentBorder(constrained)
      setHasChanges(true)
      return
    }

    if (isResizing && resizeStart) {
      const dy = imageCoords.y - resizeStart.y
      const newSize = Math.max(50, resizeStart.initialSize - dy)

      let newBorder: BorderInfo
      if (currentBorder.type === 'circle') {
        newBorder = { ...currentBorder, radius: newSize }
      } else {
        const scale = newSize / Math.max(currentBorder.axes.major, currentBorder.axes.minor)
        newBorder = {
          ...currentBorder,
          axes: {
            major: currentBorder.axes.major * scale,
            minor: currentBorder.axes.minor * scale
          }
        }
      }

      const constrained = constrainBorderToImage(newBorder)
      setCurrentBorder(constrained)
      setHasChanges(true)
      return
    }

    // Update cursor
    if (isPointOnResizeHandle(canvasX, canvasY, currentBorder)) {
      canvasRef.current.style.cursor = 'pointer'
    } else if (isPointOnBorderRing(canvasX, canvasY, currentBorder, isResizeMode)) {
      canvasRef.current.style.cursor = 'move'
    } else {
      canvasRef.current.style.cursor = 'default'
    }
  }, [currentBorder, canvasRef, isDraggingBorder, dragStart, isResizing, resizeStart, isResizeMode, canvasToImageCoords, constrainBorderToImage, isPointOnResizeHandle, isPointOnBorderRing])

  const handleCanvasMouseUp = useCallback(() => {
    setIsDraggingBorder(false)
    setIsResizing(false)
    setDragStart(null)
    setResizeStart(null)
  }, [])

  // Button states
  const addBorderEnabled = !currentBorder && !!imageDimensions
  const deleteBorderEnabled = currentBorder !== null
  const resizeEnabled = isSelected
  const resetEnabled = hasChanges && originalBorder !== null
  const saveBorderEnabled = hasChanges && currentBorder !== null

  return {
    currentBorder,
    originalBorder,
    hasChanges,
    isSelected,
    isResizeMode,
    showBorder,
    setCurrentBorder,
    setOriginalBorder,
    setHasChanges,
    setShowBorder,
    isDraggingBorder,
    isResizing,
    handleAddBorder,
    handleDeleteBorder,
    handleResetBorder,
    handleResizeMode,
    handleCanvasMouseDown,
    handleCanvasMouseMove,
    handleCanvasMouseUp,
    addBorderEnabled,
    deleteBorderEnabled,
    resizeEnabled,
    resetEnabled,
    saveBorderEnabled,
    isBorderWithinBounds,
  }
}
