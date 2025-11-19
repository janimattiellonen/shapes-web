import { useState, useRef } from 'react'
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

interface DiscMatch {
  disc_id: number
  owner_name: string
  owner_contact: string
  disc_model: string | null
  disc_color: string | null
  notes: string | null
  status: string
  location: string | null
  image_url: string
  image_path: string | null
  cropped_image_path: string | null
  border_info: BorderInfo | null
  match_type: string | null
  similarity: number
}

interface SearchResponse {
  matches: DiscMatch[]
  total_matches: number
  model_used: string
  query_info: {
    filename: string
    top_k: number
    min_similarity: number
  }
}

export default function SearchDisc() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [searching, setSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<DiscMatch[]>([])
  const [error, setError] = useState<string>('')
  const [searchComplete, setSearchComplete] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.match(/^image\/(png|jpeg|jpg)$/)) {
      setError('Please select a PNG or JPEG image')
      return
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }

    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setError('')
    setSearchResults([])
    setSearchComplete(false)
  }

  const handleSearch = async () => {
    if (!selectedFile) {
      setError('Please select an image first')
      return
    }

    try {
      setSearching(true)
      setError('')

      const formData = new FormData()
      formData.append('image', selectedFile)
      formData.append('top_k', '3') // Only return top 3 matches

      console.log('Searching for disc...')
      const response = await fetch('http://localhost:8000/discs/identification/search', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: SearchResponse = await response.json()
      console.log('Search results:', data)

      setSearchResults(data.matches)
      setSearchComplete(true)

      if (data.matches.length === 0) {
        setError('No matches found for this disc')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during search')
      console.error('Search error:', err)
    } finally {
      setSearching(false)
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
    setSearchResults([])
    setError('')
    setSearchComplete(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="border-detection-container">
      <h2>Search for Your Disc</h2>
      <p className="subtitle">Upload an image to find potential matches in our database</p>

      {/* Upload Section */}
      <div className="upload-section" style={{ marginBottom: '2rem' }}>
        <div className="file-input-wrapper">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleFileSelect}
            className="file-input"
            id="search-file-input"
          />
          <label htmlFor="search-file-input" className="file-input-label">
            {selectedFile ? selectedFile.name : 'Choose disc image...'}
          </label>
        </div>

        {selectedFile && (
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button
              onClick={handleSearch}
              disabled={searching}
              className="button button-primary"
            >
              {searching ? 'Searching...' : 'Search for Matches'}
            </button>
            <button onClick={handleClear} className="button button-secondary">
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Preview of Query Image */}
      {previewUrl && (
        <div style={{ marginBottom: '2rem' }}>
          <h3>Your Query Image:</h3>
          <div className="preview-container" style={{ maxWidth: '400px' }}>
            <img
              src={previewUrl}
              alt="Query disc"
              className="preview-image"
              style={{ width: '100%', borderRadius: '8px' }}
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-container" style={{ marginBottom: '2rem' }}>
          <p className="error-message">{error}</p>
        </div>
      )}

      {/* Search Results */}
      {searchComplete && searchResults.length > 0 && (
        <>
          <h3>
            Found {searchResults.length} Match{searchResults.length !== 1 ? 'es' : ''}
          </h3>
          <p className="subtitle">Showing top matches ranked by similarity</p>

          <div className="discs-grid">
            {searchResults.map((match, index) => (
              <MatchCard key={match.disc_id} match={match} rank={index + 1} />
            ))}
          </div>
        </>
      )}

      {searchComplete && searchResults.length === 0 && !error && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p>No matching discs found. Try with a different image.</p>
        </div>
      )}
    </div>
  )
}

interface MatchCardProps {
  match: DiscMatch
  rank: number
}

function MatchCard({ match, rank }: MatchCardProps) {
  const imageRef = useRef<HTMLImageElement>(null)
  const [showBorder, setShowBorder] = useState<boolean>(true)
  const [imageError, setImageError] = useState<boolean>(false)

  const imageUrl = match.image_url ? `http://localhost:8000${match.image_url}` : null
  const similarityPercent = (match.similarity * 100).toFixed(1)

  // Determine match quality badge
  let matchBadge = { text: 'Good Match', color: '#4CAF50' }
  if (match.similarity >= 0.9) {
    matchBadge = { text: 'Excellent Match', color: '#2196F3' }
  } else if (match.similarity >= 0.8) {
    matchBadge = { text: 'Very Good Match', color: '#4CAF50' }
  } else if (match.similarity >= 0.7) {
    matchBadge = { text: 'Good Match', color: '#FF9800' }
  } else {
    matchBadge = { text: 'Possible Match', color: '#9E9E9E' }
  }

  return (
    <div className="disc-card" style={{ position: 'relative' }}>
      {/* Rank Badge */}
      <div
        style={{
          position: 'absolute',
          top: '1rem',
          left: '1rem',
          background: '#2196F3',
          color: 'white',
          padding: '0.5rem 1rem',
          borderRadius: '20px',
          fontWeight: 'bold',
          zIndex: 10,
        }}
      >
        #{rank}
      </div>

      {/* Match Quality Badge */}
      <div
        style={{
          position: 'absolute',
          top: '1rem',
          right: '1rem',
          background: matchBadge.color,
          color: 'white',
          padding: '0.5rem 1rem',
          borderRadius: '20px',
          fontSize: '0.9rem',
          fontWeight: 'bold',
          zIndex: 10,
        }}
      >
        {matchBadge.text}
      </div>

      <div className="disc-image-container">
        {imageUrl ? (
          <div className="preview-container">
            <img
              ref={imageRef}
              src={imageUrl}
              alt={`Match ${rank}`}
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
                Failed to load image
              </div>
            )}
            {match.border_info && !imageError && (
              <BorderCanvas
                border={match.border_info}
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

        {match.border_info && (
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
        <h3>Disc #{match.disc_id}</h3>

        {/* Similarity Score */}
        <div
          className="info-row"
          style={{
            background: '#f5f5f5',
            padding: '0.75rem',
            borderRadius: '4px',
            marginBottom: '0.5rem',
          }}
        >
          <span className="info-label">Similarity:</span>
          <span
            className="info-value"
            style={{ fontWeight: 'bold', color: matchBadge.color }}
          >
            {similarityPercent}%
          </span>
          {match.match_type && (
            <span style={{ fontSize: '0.8rem', color: '#666', marginLeft: '0.5rem' }}>
              ({match.match_type})
            </span>
          )}
        </div>

        <div className="info-row">
          <span className="info-label">Owner:</span>
          <span className="info-value">{match.owner_name}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Contact:</span>
          <span className="info-value">{match.owner_contact}</span>
        </div>
        {match.disc_model && (
          <div className="info-row">
            <span className="info-label">Model:</span>
            <span className="info-value">{match.disc_model}</span>
          </div>
        )}
        {match.disc_color && (
          <div className="info-row">
            <span className="info-label">Color:</span>
            <span className="info-value">{match.disc_color}</span>
          </div>
        )}
        {match.notes && (
          <div className="info-row">
            <span className="info-label">Notes:</span>
            <span className="info-value">{match.notes}</span>
          </div>
        )}
        <div className="info-row">
          <span className="info-label">Status:</span>
          <span className="info-value status-badge">{match.status}</span>
        </div>
        {match.location && (
          <div className="info-row">
            <span className="info-label">Location:</span>
            <span className="info-value">{match.location}</span>
          </div>
        )}
      </div>
    </div>
  )
}
