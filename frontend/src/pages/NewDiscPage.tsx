import { useState, useRef, useEffect } from 'react'
import '../components/BorderDetection.css'

interface BorderCircle {
  type: 'circle'
  center: { x: number; y: number }
  radius: number
  confidence: number
}

interface BorderEllipse {
  type: 'ellipse'
  center: { x: number; y: number }
  axes: { major: number; minor: number }
  angle: number
  confidence: number
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
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [isUploading, setIsUploading] = useState<boolean>(false)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [isCancelling, setIsCancelling] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const [isDragging, setIsDragging] = useState<boolean>(false)
  const [showBorder, setShowBorder] = useState<boolean>(true)
  const [successMessage, setSuccessMessage] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)

  const handleFileSelect = (file: File) => {
    // Validate file type
    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      setError('Please select a PNG, JPG, or JPEG image')
      return
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }

    setError('')
    setUploadResult(null)
    setSuccessMessage('')

    // Create preview URL
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)

    // Auto-upload
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
    setIsDragging(true)
  }

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)

    const file = event.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleSave = async () => {
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

      // Reset form after successful save
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

      // Reset form after successful cancellation
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
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Draw border on canvas when result changes
  useEffect(() => {
    if (!uploadResult || !uploadResult.border || !showBorder) {
      // Clear canvas if no border or checkbox unchecked
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

    // Wait for image to load
    const drawBorder = () => {
      const { width, height } = image.getBoundingClientRect()
      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.clearRect(0, 0, width, height)

      const border = uploadResult.border!

      // Calculate scale factors
      const scaleX = width / image.naturalWidth
      const scaleY = height / image.naturalHeight

      // Draw border
      ctx.strokeStyle = '#646cff'
      ctx.lineWidth = 3

      if (border.type === 'circle') {
        // Draw circle
        const centerX = border.center.x * scaleX
        const centerY = border.center.y * scaleY
        const radius = border.radius * Math.min(scaleX, scaleY)

        ctx.beginPath()
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
        ctx.stroke()

        // Draw center point
        ctx.fillStyle = '#646cff'
        ctx.beginPath()
        ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI)
        ctx.fill()
      } else {
        // Draw ellipse
        const centerX = border.center.x * scaleX
        const centerY = border.center.y * scaleY
        const radiusX = border.axes.major * scaleX
        const radiusY = border.axes.minor * scaleY
        const rotation = (border.angle * Math.PI) / 180

        ctx.beginPath()
        ctx.ellipse(centerX, centerY, radiusX, radiusY, rotation, 0, 2 * Math.PI)
        ctx.stroke()

        // Draw center point
        ctx.fillStyle = '#646cff'
        ctx.beginPath()
        ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI)
        ctx.fill()
      }
    }

    if (image.complete) {
      drawBorder()
    } else {
      image.addEventListener('load', drawBorder)
      return () => image.removeEventListener('load', drawBorder)
    }
  }, [uploadResult, showBorder])

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
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
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
            />
            <canvas
              ref={canvasRef}
              className="border-canvas"
            />
          </div>
        )}
      </div>

      {isUploading && (
        <div className="loading-container">
          <p>Uploading and detecting border...</p>
        </div>
      )}

      {uploadResult && uploadResult.border && (
        <div className="border-control">
          <label>
            <input
              type="checkbox"
              checked={showBorder}
              onChange={(e) => setShowBorder(e.target.checked)}
            />
            <span>Show detected border</span>
          </label>
        </div>
      )}

      {uploadResult && !uploadResult.border_detected && (
        <div className="notice-container">
          <p className="notice-message">⚠️ No border detected. You can still save this disc image.</p>
        </div>
      )}

      <div className="action-buttons">
        {uploadResult && !successMessage && (
          <>
            <button
              onClick={handleSave}
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
