import { useState, useRef, useEffect } from 'react';
import './ShapeDetector.css';

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface DetectionResult {
  shape: string;
  confidence: number;
  probabilities: {
    circle: number;
    triangle: number;
    rectangle: number;
  };
  bounding_box: BoundingBox | null;
}

export function ShapeDetector() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [showBoundingBox, setShowBoundingBox] = useState<boolean>(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

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

  // Draw bounding box on canvas when result changes
  useEffect(() => {
    if (!result || !result.bounding_box || !showBoundingBox) {
      // Clear canvas if no bounding box or checkbox unchecked
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        }
      }
      return;
    }

    const image = imageRef.current;
    const canvas = canvasRef.current;

    if (!image || !canvas) return;

    // Wait for image to load
    const drawBox = () => {
      const { width, height } = image.getBoundingClientRect();
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.clearRect(0, 0, width, height);

      const box = result.bounding_box!;
      const x = box.x * width;
      const y = box.y * height;
      const boxWidth = box.width * width;
      const boxHeight = box.height * height;

      // Draw bounding box
      ctx.strokeStyle = '#646cff';
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, boxWidth, boxHeight);

      // Draw corner markers
      const cornerSize = 10;
      ctx.fillStyle = '#646cff';
      // Top-left
      ctx.fillRect(x - 2, y - 2, cornerSize, 4);
      ctx.fillRect(x - 2, y - 2, 4, cornerSize);
      // Top-right
      ctx.fillRect(x + boxWidth - cornerSize + 2, y - 2, cornerSize, 4);
      ctx.fillRect(x + boxWidth - 2, y - 2, 4, cornerSize);
      // Bottom-left
      ctx.fillRect(x - 2, y + boxHeight - 2, cornerSize, 4);
      ctx.fillRect(x - 2, y + boxHeight - cornerSize + 2, 4, cornerSize);
      // Bottom-right
      ctx.fillRect(x + boxWidth - cornerSize + 2, y + boxHeight - 2, cornerSize, 4);
      ctx.fillRect(x + boxWidth - 2, y + boxHeight - cornerSize + 2, 4, cornerSize);
    };

    if (image.complete) {
      drawBox();
    } else {
      image.addEventListener('load', drawBox);
      return () => image.removeEventListener('load', drawBox);
    }
  }, [result, showBoundingBox]);

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
            <img
              ref={imageRef}
              src={previewUrl}
              alt="Preview"
              className="preview-image"
            />
            <canvas
              ref={canvasRef}
              className="bounding-box-canvas"
            />
          </div>
        )}
      </div>

      {result && result.bounding_box && (
        <div className="bounding-box-control">
          <label>
            <input
              type="checkbox"
              checked={showBoundingBox}
              onChange={(e) => setShowBoundingBox(e.target.checked)}
            />
            <span>Draw bounding border</span>
          </label>
        </div>
      )}

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
