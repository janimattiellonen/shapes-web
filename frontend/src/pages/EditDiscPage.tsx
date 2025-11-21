import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { DiscEditor } from '../components/DiscEditor'
import type { BorderInfo, Disc } from '../types/disc'
import '../components/BorderDetection.css'

export default function EditDiscPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const discId = parseInt(id || '0', 10)

  const [disc, setDisc] = useState<Disc | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    if (discId) {
      fetchDisc()
    }
  }, [discId])

  const fetchDisc = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await fetch(`http://localhost:8000/discs/identification/${discId}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch disc: ${response.status}`)
      }

      const data = await response.json()
      setDisc(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch disc')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveBorder = async (border: BorderInfo) => {
    const response = await fetch(`http://localhost:8000/discs/${discId}/border`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ border })
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to save border')
    }

    setSuccessMessage('Border saved successfully!')
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  const handleSaveDisc = async () => {
    setIsSaving(true)
    setError('')

    try {
      // For edit mode, we just need to ensure border changes are saved
      // The disc is already confirmed
      setSuccessMessage('Changes saved successfully!')
      setTimeout(() => {
        navigate('/')
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save disc')
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    navigate('/')
  }

  if (loading) {
    return (
      <div className="border-detection-container">
        <h2>Edit Disc</h2>
        <div className="loading-container">
          <p>Loading disc...</p>
        </div>
      </div>
    )
  }

  if (error && !disc) {
    return (
      <div className="border-detection-container">
        <h2>Edit Disc</h2>
        <div className="error-container">
          <p className="error-message">{error}</p>
        </div>
      </div>
    )
  }

  if (!disc) {
    return (
      <div className="border-detection-container">
        <h2>Edit Disc</h2>
        <p>Disc not found</p>
      </div>
    )
  }

  // Get the first image from the images array
  const discImage = (disc as any).images?.[0]

  // Construct image URLs
  const baseUrl = 'http://localhost:8000'
  const imageUrl = discImage?.image_url ? `${baseUrl}${discImage.image_url}` : ''
  // Original image path - the uncropped version
  const originalImageUrl = discImage?.image_path ? `${baseUrl}/uploads/discs/${discId}/${discImage.image_path.split('/').pop()}` : undefined

  return (
    <div className="border-detection-container">
      <h2>Edit Disc #{discId}</h2>
      <p className="subtitle">Adjust the border and save changes</p>

      {imageUrl && (
        <DiscEditor
          imageUrl={imageUrl}
          initialBorder={discImage?.border_info}
          discId={discId}
          mode="edit"
          originalImageUrl={originalImageUrl}
          onSaveBorder={handleSaveBorder}
          onSaveDisc={handleSaveDisc}
          onCancel={handleCancel}
          isSaving={isSaving}
          successMessage={successMessage}
          error={error}
          setError={setError}
        />
      )}
    </div>
  )
}
