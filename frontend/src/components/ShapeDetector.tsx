import { useState, useRef } from 'react';
import './ShapeDetector.css';

interface DetectionResult {
  shape: string;
  confidence: number;
  probabilities: {
    circle: number;
    triangle: number;
    rectangle: number;
  };
}

export function ShapeDetector() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    // Validate file type
    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      setError('Please select a PNG, JPG, or JPEG image');
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    setError('');
    setResult(null);

    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDetectShape = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);

      const response = await fetch('http://localhost:8000/detect-shape', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data: DetectionResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during detection');
      console.error('Error detecting shape:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatConfidence = (confidence: number): string => {
    return (confidence * 100).toFixed(2);
  };

  return (
    <div className="shape-detector-container">
      <h2>Shape Detection</h2>
      <p className="subtitle">Upload an image to detect circles, triangles, or rectangles</p>

      <div
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          accept="image/png,image/jpeg,image/jpg"
          style={{ display: 'none' }}
        />

        {!previewUrl ? (
          <div className="upload-prompt">
            <div className="upload-icon">📁</div>
            <p>Click to select or drag and drop an image</p>
            <p className="upload-hint">PNG, JPG, JPEG (max 10MB)</p>
          </div>
        ) : (
          <div className="preview-container">
            <img src={previewUrl} alt="Preview" className="preview-image" />
          </div>
        )}
      </div>

      <div className="action-buttons">
        {selectedFile && !result && (
          <>
            <button
              onClick={handleDetectShape}
              disabled={isLoading}
              className="detect-button"
            >
              {isLoading ? 'Detecting...' : 'Detect Shape'}
            </button>
            <button onClick={handleReset} className="reset-button">
              Clear
            </button>
          </>
        )}

        {result && (
          <button onClick={handleReset} className="reset-button">
            Try Another Image
          </button>
        )}
      </div>

      {error && (
        <div className="error-container">
          <p className="error-message">⚠️ {error}</p>
        </div>
      )}

      {result && (
        <div className="result-container">
          <h3>Detection Result</h3>
          <div className="result-card">
            <div className="shape-icon">{getShapeIcon(result.shape)}</div>
            <div className="result-details">
              <p className="detected-shape">
                Detected: <strong>{result.shape.toUpperCase()}</strong>
              </p>
              <p className="confidence">
                Confidence: <strong>{formatConfidence(result.confidence)}%</strong>
              </p>
            </div>
          </div>

          <div className="probabilities-container">
            <h4>All Probabilities</h4>
            <div className="probability-bars">
              {Object.entries(result.probabilities).map(([shape, prob]) => (
                <div key={shape} className="probability-item">
                  <div className="probability-label">
                    <span>{getShapeIcon(shape)}</span>
                    <span>{shape}</span>
                  </div>
                  <div className="probability-bar-container">
                    <div
                      className="probability-bar"
                      style={{ width: `${prob * 100}%` }}
                    />
                  </div>
                  <span className="probability-value">{formatConfidence(prob)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getShapeIcon(shape: string): string {
  const icons: { [key: string]: string } = {
    circle: '⭕',
    triangle: '🔺',
    rectangle: '▭',
  };
  return icons[shape.toLowerCase()] || '❓';
}
