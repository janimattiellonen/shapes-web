import { useRef, useEffect, useState } from 'react'
import { BorderCanvas } from './BorderCanvas'
import { useBorderEditor } from '../hooks/useBorderEditor'
import type { BorderInfo } from '../types/disc'
import './BorderDetection.css'

interface DiscEditorProps {
  imageUrl: string
  initialBorder: BorderInfo | null
  discId: number
  mode: 'new' | 'edit'
  originalImageUrl?: string // For edit mode - the uncropped original
  onSaveBorder: (border: BorderInfo) => Promise<void>
  onSaveDisc: () => Promise<void>
  onCancel: () => void
  onResetImage?: () => void // For edit mode - switch to original image
  isSaving?: boolean
  isCancelling?: boolean
  successMessage?: string
  error?: string
  setError?: (error: string) => void
}

export function DiscEditor({
  imageUrl,
  initialBorder,
  discId,
  mode,
  originalImageUrl,
  onSaveBorder,
  onSaveDisc,
  onCancel,
  onResetImage,
  isSaving = false,
  isCancelling = false,
  successMessage,
  error,
  setError,
}: DiscEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(null)
  const [isSavingBorder, setIsSavingBorder] = useState(false)
  const [isUsingOriginalImage, setIsUsingOriginalImage] = useState(false)

  const currentImageUrl = isUsingOriginalImage && originalImageUrl ? originalImageUrl : imageUrl

  const {
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
  } = useBorderEditor({
    initialBorder,
    imageDimensions,
    canvasRef,
    imageRef,
  })

  // Update border when initialBorder changes
  useEffect(() => {
    setOriginalBorder(initialBorder)
    setCurrentBorder(initialBorder)
    setHasChanges(false)
  }, [initialBorder, setOriginalBorder, setCurrentBorder, setHasChanges])

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.target as HTMLImageElement
    setImageDimensions({ width: img.naturalWidth, height: img.naturalHeight })
  }

  const handleSaveBorder = async () => {
    if (!currentBorder) return

    if (!isBorderWithinBounds(currentBorder)) {
      setError?.('Border extends outside image boundaries. Please adjust the border before saving.')
      return
    }

    setIsSavingBorder(true)
    setError?.('')

    try {
      await onSaveBorder(currentBorder)
      setOriginalBorder({ ...currentBorder })
      setHasChanges(false)
    } catch (err) {
      setError?.(err instanceof Error ? err.message : 'Failed to save border')
    } finally {
      setTimeout(() => setIsSavingBorder(false), 3000)
    }
  }

  const handleSaveDisc = async () => {
    if (!currentBorder) {
      const confirmed = window.confirm('Do you really want to save without adding a border?')
      if (!confirmed) return
    }

    if (currentBorder && !isBorderWithinBounds(currentBorder)) {
      setError?.('Border extends outside image boundaries. Please adjust the border before saving.')
      return
    }

    // Auto-save border if there are unsaved changes
    if (currentBorder && hasChanges) {
      try {
        await onSaveBorder(currentBorder)
        setOriginalBorder({ ...currentBorder })
        setHasChanges(false)
      } catch (err) {
        setError?.(err instanceof Error ? err.message : 'Failed to save border before saving disc')
        return
      }
    }

    await onSaveDisc()
  }

  const handleResetImage = () => {
    setIsUsingOriginalImage(true)
    onResetImage?.()
  }

  const resetImageEnabled = mode === 'edit' && originalImageUrl && !isUsingOriginalImage

  return (
    <div className="disc-editor">
      <div className="preview-container">
        <img
          ref={imageRef}
          src={currentImageUrl}
          alt={`Disc ${discId}`}
          className="preview-image"
          onLoad={handleImageLoad}
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

      {currentBorder && (
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

      {!currentBorder && (
        <div className="notice-container">
          <p className="notice-message">No border detected. Use "Add Border" to create one manually.</p>
        </div>
      )}

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
        {resetImageEnabled && (
          <button onClick={handleResetImage}>
            Reset Image
          </button>
        )}
        <button onClick={handleResizeMode} disabled={!resizeEnabled}>
          {isResizeMode ? 'Hide Resize' : 'Resize'}
        </button>
        <button
          onClick={handleSaveBorder}
          disabled={!saveBorderEnabled || isSavingBorder}
          className="primary-button"
        >
          {isSavingBorder ? 'Saving Border...' : 'Save Border'}
        </button>
      </div>

      {isSavingBorder && (
        <div className="notice-container">
          <p className="notice-message">Saving border details...</p>
        </div>
      )}

      <div className="action-buttons">
        <button
          onClick={handleSaveDisc}
          disabled={isSaving || isCancelling || isSavingBorder}
          className="save-button"
        >
          {isSaving ? 'Saving...' : 'Save Disc'}
        </button>
        <button
          onClick={onCancel}
          disabled={isSaving || isCancelling || isSavingBorder}
          className="cancel-button"
        >
          {isCancelling ? 'Cancelling...' : 'Cancel'}
        </button>
      </div>

      {successMessage && (
        <div className="success-container">
          <p className="success-message">{successMessage}</p>
        </div>
      )}

      {error && (
        <div className="error-container">
          <p className="error-message">{error}</p>
        </div>
      )}
    </div>
  )
}
