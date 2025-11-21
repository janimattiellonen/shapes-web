import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
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

interface Disc {
  disc_id: number
  owner_name: string
  owner_contact: string
  disc_model: string | null
  disc_color: string | null
  notes: string | null
  status: string
  location: string | null
  registered_date: string
  image_id: number | null
  image_url: string | null
  image_path: string | null
  border_info: BorderInfo | null
  cropped_image_path: string | null
  created_at: string | null
}

export default function DiscsPage() {
  const [discs, setDiscs] = useState<Disc[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    fetchDiscs()
  }, [])

  const fetchDiscs = async () => {
    try {
      setLoading(true)
      setError('')

      console.log('Fetching discs from API...')
      const response = await fetch('http://localhost:8000/discs/list')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('Fetched discs data:', data)
      setDiscs(data.discs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while fetching discs')
      console.error('Error fetching discs:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="border-detection-container">
        <h2>Registered Discs</h2>
        <div className="loading-container">
          <p>Loading discs...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="border-detection-container">
        <h2>Registered Discs</h2>
        <div className="error-container">
          <p className="error-message">{error}</p>
        </div>
      </div>
    )
  }

  if (discs.length === 0) {
    return (
      <div className="border-detection-container">
        <h2>Registered Discs</h2>
        <p className="subtitle">No discs have been registered yet.</p>
      </div>
    )
  }

  return (
    <div className="border-detection-container">
      <h2>Registered Discs</h2>
      <p className="subtitle">Total: {discs.length} disc{discs.length !== 1 ? 's' : ''}</p>

      <div className="discs-grid">
        {discs.map((disc) => (
          <DiscCard
            key={disc.disc_id}
            disc={disc}
            onDelete={(discId) => setDiscs(discs.filter(d => d.disc_id !== discId))}
          />
        ))}
      </div>
    </div>
  )
}

interface DiscCardProps {
  disc: Disc
  onDelete: (discId: number) => void
}

function DiscCard({ disc, onDelete }: DiscCardProps) {
  const navigate = useNavigate()
  const imageRef = useRef<HTMLImageElement>(null)
  const [showBorder, setShowBorder] = useState<boolean>(true)
  const [imageError, setImageError] = useState<boolean>(false)
  const [isDeleting, setIsDeleting] = useState<boolean>(false)

  const imageUrl = disc.image_url ? `http://localhost:8000${disc.image_url}` : null

  const handleEdit = () => {
    navigate(`/discs/${disc.disc_id}/edit`)
  }

  const handleDelete = async () => {
    if (!window.confirm('Do you want to delete this image?')) return

    setIsDeleting(true)
    try {
      const response = await fetch(`http://localhost:8000/discs/${disc.disc_id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to delete disc')
      }

      onDelete(disc.disc_id)
    } catch (err) {
      console.error('Error deleting disc:', err)
      alert(err instanceof Error ? err.message : 'Failed to delete disc')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="disc-card">
      <div className="disc-image-container">
        {imageUrl ? (
          <div className="preview-container">
            <img
              ref={imageRef}
              src={imageUrl}
              alt={`Disc ${disc.disc_id}`}
              className="preview-image"
              onLoad={() => {
                console.log('Image loaded successfully:', imageUrl)
              }}
              onError={(e) => {
                console.error('Failed to load image:', imageUrl, e)
                setImageError(true)
              }}
            />
            {imageError && (
              <div style={{ padding: '1rem', textAlign: 'center', color: '#c33' }}>
                Failed to load image: {imageUrl}
              </div>
            )}
            {disc.border_info && !imageError && (
              <BorderCanvas
                border={disc.border_info}
                imageRef={imageRef}
                showBorder={showBorder}
                interactive={false}
              />
            )}
          </div>
        ) : (
          <div style={{ padding: '1rem', textAlign: 'center', color: '#999' }}>
            No image available
          </div>
        )}

        {disc.border_info && (
          <div className="border-control">
            <label>
              <input
                type="checkbox"
                checked={showBorder}
                onChange={(e) => setShowBorder(e.target.checked)}
              />
              Show detected border
            </label>
          </div>
        )}
      </div>

      <div className="disc-info">
        <h3>Disc #{disc.disc_id}</h3>
        <div className="info-row">
          <span className="info-label">Owner:</span>
          <span className="info-value">{disc.owner_name}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Contact:</span>
          <span className="info-value">{disc.owner_contact}</span>
        </div>
        {disc.disc_model && (
          <div className="info-row">
            <span className="info-label">Model:</span>
            <span className="info-value">{disc.disc_model}</span>
          </div>
        )}
        {disc.disc_color && (
          <div className="info-row">
            <span className="info-label">Color:</span>
            <span className="info-value">{disc.disc_color}</span>
          </div>
        )}
        {disc.notes && (
          <div className="info-row">
            <span className="info-label">Notes:</span>
            <span className="info-value">{disc.notes}</span>
          </div>
        )}
        <div className="info-row">
          <span className="info-label">Status:</span>
          <span className="info-value status-badge">{disc.status}</span>
        </div>
        {disc.location && (
          <div className="info-row">
            <span className="info-label">Location:</span>
            <span className="info-value">{disc.location}</span>
          </div>
        )}
        <div className="info-row">
          <span className="info-label">Registered:</span>
          <span className="info-value">
            {new Date(disc.registered_date).toLocaleDateString()}
          </span>
        </div>
        <div className="action-buttons" style={{ marginTop: '1rem' }}>
          <button
            onClick={handleEdit}
            disabled={isDeleting}
            className="save-button"
          >
            Edit
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="cancel-button"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
