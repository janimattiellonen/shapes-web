import { useState, useRef, useEffect } from 'react'
import { BorderCanvas } from '../components/BorderCanvas'
import '../components/BorderDetection.css'

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

interface UploadResult {
  disc_id: number
  border_detected: boolean
  border: BorderInfo | null
  image_url: string
  message: string
}

export default function NewDiscPage() {
  // Upload state
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [isUploading, setIsUploading] = useState<boolean>(false)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [isCancelling, setIsCancelling] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const [isDraggingFile, setIsDraggingFile] = useState<boolean>(false)
  const [successMessage, setSuccessMessage] = useState<string>('')

  // Border state
  const [originalBorder, setOriginalBorder] = useState<BorderInfo | null>(null)
  const [currentBorder, setCurrentBorder] = useState<BorderInfo | null>(null)
  const [isSelected, setIsSelected] = useState<boolean>(false)
  const [isResizeMode, setIsResizeMode] = useState<boolean>(false)
  const [hasChanges, setHasChanges] = useState<boolean>(false)
  const [showBorder, setShowBorder] = useState<boolean>(true)

  // Interaction state
  const [isDraggingBorder, setIsDraggingBorder] = useState<boolean>(false)
  const [isResizing, setIsResizing] = useState<boolean>(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number; borderX: number; borderY: number } | null>(null)
  const [resizeStart, setResizeStart] = useState<{ y: number; initialSize: number } | null>(null)

  // Image dimensions
  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(null)

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)

  // Update original and current border when upload result changes
  useEffect(() => {
    if (uploadResult?.border) {
      setOriginalBorder(uploadResult.border)
      setCurrentBorder({ ...uploadResult.border })
      setHasChanges(false)
      setIsSelected(false)
      setIsResizeMode(false)
    } else {
      setOriginalBorder(null)
      setCurrentBorder(null)
      setHasChanges(false)
      setIsSelected(false)
      setIsResizeMode(false)
    }
  }, [uploadResult])

  // Update image dimensions when image loads
  useEffect(() => {
    const img = imageRef.current
    if (img && img.complete) {
      setImageDimensions({ width: img.naturalWidth, height: img.naturalHeight })
    }
  }, [previewUrl])

  const handleFileSelect = (file: File) => {
    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      setError('Please select a PNG, JPG, or JPEG image')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }

    setError('')
    setUploadResult(null)
    setSuccessMessage('')
    setCurrentBorder(null)
    setOriginalBorder(null)

    const url = URL.createObjectURL(file)
    setPreviewUrl(url)

    uploadImage(file)
  }

  const uploadImage = async (file: File) => {
    setIsUploading(true)
    setError('')
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('image', file)

      const response = await fetch('http://localhost:8000/discs/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data: UploadResult = await response.json()
      setUploadResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during upload')
      console.error('Error uploading image:', err)
    } finally {
      setIsUploading(false)
    }
  }

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDraggingFile(true)
  }

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDraggingFile(false)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDraggingFile(false)

    const file = event.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  // Helper: Convert canvas coordinates to image coordinates
  const canvasToImageCoords = (canvasX: number, canvasY: number): { x: number; y: number } => {
    const canvas = canvasRef.current
    const image = imageRef.current
    if (!canvas || !image) return { x: 0, y: 0 }

    const rect = canvas.getBoundingClientRect()
    const scaleX = image.naturalWidth / rect.width
    const scaleY = image.naturalHeight / rect.height

    return {
      x: canvasX * scaleX,
      y: canvasY * scaleY
    }
  }

  // Helper: Check if point is on border ring (in canvas/display coordinates)
  // When inResizeMode is false, allows clicking anywhere inside or on the border
  // When inResizeMode is true, only allows clicking on the ring perimeter
  const isPointOnBorderRing = (canvasX: number, canvasY: number, border: BorderInfo, inResizeMode: boolean = false): boolean => {
    const image = imageRef.current
    if (!image) return false

    const rect = image.getBoundingClientRect()
    const scaleX = rect.width / image.naturalWidth
    const scaleY = rect.height / image.naturalHeight

    // Convert border to display coordinates
    const centerX = border.center.x * scaleX
    const centerY = border.center.y * scaleY

    // Tolerance in display pixels (easier to click)
    const tolerance = 15

    if (border.type === 'circle') {
      // For circles, use uniform scaling (same as rendering)
      const displayScale = Math.min(scaleX, scaleY)
      const radius = border.radius * displayScale

      const distance = Math.sqrt(
        Math.pow(canvasX - centerX, 2) + Math.pow(canvasY - centerY, 2)
      )

      // When in resize mode, only allow clicking on the ring perimeter
      // Otherwise, allow clicking anywhere inside or on the border
      if (inResizeMode) {
        return Math.abs(distance - radius) <= tolerance
      } else {
        return distance <= radius + tolerance
      }
    } else {
      // For ellipse
      const radiusX = border.axes.major * scaleX
      const radiusY = border.axes.minor * scaleY
      const angle = border.angle * Math.PI / 180

      // Translate to origin
      const dx = canvasX - centerX
      const dy = canvasY - centerY

      // Rotate point back
      const rotX = dx * Math.cos(-angle) - dy * Math.sin(-angle)
      const rotY = dx * Math.sin(-angle) + dy * Math.cos(-angle)

      // Distance to ellipse (normalized)
      const ellipseValue = (rotX * rotX) / (radiusX * radiusX) +
                          (rotY * rotY) / (radiusY * radiusY)

      const normalizedDistance = Math.sqrt(ellipseValue)

      // When in resize mode, only allow clicking on the ring perimeter
      // Otherwise, allow clicking anywhere inside or on the border
      if (inResizeMode) {
        return Math.abs(normalizedDistance - 1) * Math.max(radiusX, radiusY) <= tolerance
      } else {
        return normalizedDistance <= 1 + (tolerance / Math.max(radiusX, radiusY))
      }
    }
  }

  // Helper: Check if point is on resize handle (in canvas/display coordinates)
  const isPointOnResizeHandle = (canvasX: number, canvasY: number, border: BorderInfo): boolean => {
    if (!isResizeMode) return false

    const image = imageRef.current
    if (!image) return false

    const rect = image.getBoundingClientRect()
    const scaleX = rect.width / image.naturalWidth
    const scaleY = rect.height / image.naturalHeight

    const centerX = border.center.x * scaleX
    const centerY = border.center.y * scaleY

    const distance = Math.sqrt(
      Math.pow(canvasX - centerX, 2) + Math.pow(canvasY - centerY, 2)
    )

    return distance <= 15
  }

  // Helper: Constrain border to image bounds
  const constrainBorderToImage = (border: BorderInfo): BorderInfo => {
    if (!imageDimensions) return border

    const minSize = 50 // Minimum radius (100px diameter)
    const maxSize = Math.min(imageDimensions.width, imageDimensions.height) / 2

    if (border.type === 'circle') {
      let { center, radius } = border

      // Constrain radius
      radius = Math.max(minSize, Math.min(maxSize, radius))

      // Constrain center to keep border within image
      center.x = Math.max(radius, Math.min(imageDimensions.width - radius, center.x))
      center.y = Math.max(radius, Math.min(imageDimensions.height - radius, center.y))

      return { ...border, center, radius }
    } else {
      // For ellipse, constrain proportionally
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

      // Constrain center
      const maxRadius = Math.max(axes.major, axes.minor)
      center.x = Math.max(maxRadius, Math.min(imageDimensions.width - maxRadius, center.x))
      center.y = Math.max(maxRadius, Math.min(imageDimensions.height - maxRadius, center.y))

      return { ...border, center, axes }
    }
  }

  // Mouse event handlers
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!currentBorder || !canvasRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top

    // Check if clicking on resize handle (use canvas coordinates)
    if (isPointOnResizeHandle(canvasX, canvasY, currentBorder)) {
      const imageCoords = canvasToImageCoords(canvasX, canvasY)
      setIsResizing(true)
      const initialSize = currentBorder.type === 'circle'
        ? currentBorder.radius
        : Math.max(currentBorder.axes.major, currentBorder.axes.minor)
      setResizeStart({ y: imageCoords.y, initialSize })
      return
    }

    // Check if clicking on border ring (use canvas coordinates)
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

    // Clicking outside - deselect
    setIsSelected(false)
    setIsResizeMode(false)
  }

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!currentBorder || !canvasRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top
    const imageCoords = canvasToImageCoords(canvasX, canvasY)

    // Handle border dragging
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

    // Handle resizing
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

    // Update cursor based on hover position
    handleCanvasMouseMoveHover(e)
  }

  const handleCanvasMouseUp = () => {
    setIsDraggingBorder(false)
    setIsResizing(false)
    setDragStart(null)
    setResizeStart(null)
  }

  // Button handlers
  const handleAddBorder = () => {
    if (!imageDimensions) return

    const radius = (Math.min(imageDimensions.width, imageDimensions.height) - 100) / 2
    const newBorder: BorderCircle = {
      type: 'circle',
      center: {
        x: imageDimensions.width / 2,
        y: imageDimensions.height / 2
      },
      radius
    }

    setCurrentBorder(newBorder)
    setOriginalBorder(null)
    setHasChanges(true)
    setIsSelected(true)
  }

  const handleDeleteBorder = () => {
    setCurrentBorder(null)
    setIsSelected(false)
    setIsResizeMode(false)
    setHasChanges(true)
  }

  const handleResetBorder = () => {
    if (originalBorder) {
      setCurrentBorder({ ...originalBorder })
      setHasChanges(false)
      setIsSelected(false)
      setIsResizeMode(false)
    }
  }

  const handleResizeMode = () => {
    setIsResizeMode(!isResizeMode)
  }

  const handleSaveBorder = async () => {
    if (!uploadResult || !currentBorder) return

    setIsSaving(true)
    setError('')

    try {
      const response = await fetch(`http://localhost:8000/discs/${uploadResult.disc_id}/border`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ border: currentBorder })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      // Update original border and reset changes
      setOriginalBorder({ ...currentBorder })
      setHasChanges(false)
      setSuccessMessage('Border saved successfully!')

      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while saving border')
      console.error('Error saving border:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleSaveDisc = async () => {
    if (!uploadResult) return

    setIsSaving(true)
    setError('')

    try {
      const response = await fetch(`http://localhost:8000/discs/${uploadResult.disc_id}/confirm`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setSuccessMessage(data.message)

      setTimeout(() => {
        handleReset()
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while saving')
      console.error('Error saving disc:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = async () => {
    if (!uploadResult) return

    setIsCancelling(true)
    setError('')

    try {
      const response = await fetch(`http://localhost:8000/discs/${uploadResult.disc_id}/cancel`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      handleReset()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while cancelling')
      console.error('Error cancelling disc:', err)
    } finally {
      setIsCancelling(false)
    }
  }

  const handleReset = () => {
    setPreviewUrl(null)
    setUploadResult(null)
    setError('')
    setSuccessMessage('')
    setCurrentBorder(null)
    setOriginalBorder(null)
    setHasChanges(false)
    setIsSelected(false)
    setIsResizeMode(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Get cursor style based on interaction state and hover
  // Check if mouse is hovering over border (for cursor feedback)
  const handleCanvasMouseMoveHover = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!currentBorder || !canvasRef.current || isDraggingBorder || isResizing) return

    const rect = canvasRef.current.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top

    // Check if hovering over resize handle (use canvas coordinates)
    if (isPointOnResizeHandle(canvasX, canvasY, currentBorder)) {
      canvasRef.current.style.cursor = 'pointer'
      return
    }

    // Check if hovering over border ring (use canvas coordinates)
    if (isPointOnBorderRing(canvasX, canvasY, currentBorder, isResizeMode)) {
      canvasRef.current.style.cursor = 'move'
      return
    }

    // Default cursor
    canvasRef.current.style.cursor = 'default'
  }

  // Button enabled states
  const addBorderEnabled = uploadResult && !currentBorder
  const deleteBorderEnabled = currentBorder !== null
  const resizeEnabled = isSelected
  const resetEnabled = hasChanges && originalBorder !== null
  const saveBorderEnabled = hasChanges && currentBorder !== null

  return (
    <div className="border-detection-container">
      <h2>Add New Disc</h2>
      <p className="subtitle">Upload a disc image to add it to your collection</p>

      {successMessage && (
        <div className="success-container">
          <p className="success-message">✓ {successMessage}</p>
        </div>
      )}

      <div
        className={`upload-area ${isDraggingFile ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploadResult && fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          accept="image/png,image/jpeg,image/jpg"
          style={{ display: 'none' }}
          disabled={isUploading || isSaving || isCancelling}
        />

        {!previewUrl ? (
          <div className="upload-prompt">
            <div className="upload-icon">🥏</div>
            <p>Click to select or drag and drop a disc image</p>
            <p className="upload-hint">PNG, JPG, JPEG (max 10MB)</p>
          </div>
        ) : (
          <div className="preview-container">
            <img
              ref={imageRef}
              src={previewUrl}
              alt="Preview"
              className="preview-image"
              onLoad={(e) => {
                const img = e.target as HTMLImageElement
                setImageDimensions({ width: img.naturalWidth, height: img.naturalHeight })
              }}
            />
            <BorderCanvas
              border={currentBorder}
              imageRef={imageRef}
              canvasRef={canvasRef}
              showBorder={showBorder}
              isSelected={isSelected}
              isResizeMode={isResizeMode}
              interactive={true}
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              className={`${isDraggingBorder ? 'dragging' : ''} ${isResizing ? 'resizing' : ''}`}
            />
          </div>
        )}
      </div>

      {isUploading && (
        <div className="loading-container">
          <p>Uploading and detecting border...</p>
        </div>
      )}

      {uploadResult && currentBorder && (
        <div className="border-control">
          <label>
            <input
              type="checkbox"
              checked={showBorder}
              onChange={(e) => setShowBorder(e.target.checked)}
            />
            <span>Show border</span>
          </label>
        </div>
      )}

      {uploadResult && !uploadResult.border_detected && !currentBorder && (
        <div className="notice-container">
          <p className="notice-message">⚠️ No border detected. Use "Add Border" to create one manually.</p>
        </div>
      )}

      {uploadResult && (
        <div className="border-controls">
          <button onClick={handleAddBorder} disabled={!addBorderEnabled}>
            Add Border
          </button>
          <button onClick={handleDeleteBorder} disabled={!deleteBorderEnabled}>
            Delete Border
          </button>
          <button onClick={handleResetBorder} disabled={!resetEnabled}>
            Reset Border
          </button>
          <button onClick={handleResizeMode} disabled={!resizeEnabled}>
            {isResizeMode ? 'Hide Resize' : 'Resize'}
          </button>
          <button
            onClick={handleSaveBorder}
            disabled={!saveBorderEnabled || isSaving}
            className="primary-button"
          >
            {isSaving ? 'Saving Border...' : 'Save Border'}
          </button>
        </div>
      )}

      <div className="action-buttons">
        {uploadResult && !successMessage && (
          <>
            <button
              onClick={handleSaveDisc}
              disabled={isSaving || isCancelling}
              className="save-button"
            >
              {isSaving ? 'Saving...' : 'Save Disc'}
            </button>
            <button
              onClick={handleCancel}
              disabled={isSaving || isCancelling}
              className="cancel-button"
            >
              {isCancelling ? 'Cancelling...' : 'Cancel'}
            </button>
          </>
        )}
      </div>

      {error && (
        <div className="error-container">
          <p className="error-message">⚠️ {error}</p>
        </div>
      )}
    </div>
  )
}
