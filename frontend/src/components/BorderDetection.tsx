import { useState, useRef, useEffect } from 'react';
import './BorderDetection.css';

interface BorderCircle {
  type: 'circle';
  center: { x: number; y: number };
  radius: number;
  confidence: number;
}

interface BorderEllipse {
  type: 'ellipse';
  center: { x: number; y: number };
  axes: { major: number; minor: number };
  angle: number;
  confidence: number;
}

type BorderInfo = BorderCircle | BorderEllipse;

interface DetectionResult {
  detected: boolean;
  border: BorderInfo | null;
  message: string;
}

export function BorderDetection() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [showBorder, setShowBorder] = useState<boolean>(true);
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

  const handleDetectBorder = async () => {
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

      const response = await fetch('http://localhost:8000/discs/border-detection', {
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
      console.error('Error detecting border:', err);
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

  // Draw border on canvas when result changes
  useEffect(() => {
    if (!result || !result.border || !showBorder) {
      // Clear canvas if no border or checkbox unchecked
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
    const drawBorder = () => {
      const { width, height } = image.getBoundingClientRect();
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.clearRect(0, 0, width, height);

      const border = result.border!;

      // Calculate scale factors
      const scaleX = width / image.naturalWidth;
      const scaleY = height / image.naturalHeight;

      // Draw border
      ctx.strokeStyle = '#646cff';
      ctx.lineWidth = 3;

      if (border.type === 'circle') {
        // Draw circle
        const centerX = border.center.x * scaleX;
        const centerY = border.center.y * scaleY;
        const radius = border.radius * Math.min(scaleX, scaleY);

        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.stroke();

        // Draw center point
        ctx.fillStyle = '#646cff';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI);
        ctx.fill();
      } else {
        // Draw ellipse
        const centerX = border.center.x * scaleX;
        const centerY = border.center.y * scaleY;
        const radiusX = border.axes.major * scaleX;
        const radiusY = border.axes.minor * scaleY;
        const rotation = (border.angle * Math.PI) / 180;

        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, rotation, 0, 2 * Math.PI);
        ctx.stroke();

        // Draw center point
        ctx.fillStyle = '#646cff';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI);
        ctx.fill();
      }
    };

    if (image.complete) {
      drawBorder();
    } else {
      image.addEventListener('load', drawBorder);
      return () => image.removeEventListener('load', drawBorder);
    }
  }, [result, showBorder]);

  return (
    <div className="border-detection-container">
      <h2>Disc Border Detection</h2>
      <p className="subtitle">Upload a disc image to automatically detect its border</p>

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

      {result && result.border && (
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

      <div className="action-buttons">
        {selectedFile && !result && (
          <>
            <button
              onClick={handleDetectBorder}
              disabled={isLoading}
              className="detect-button"
            >
              {isLoading ? 'Detecting...' : 'Detect Border'}
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
          {result.detected && result.border ? (
            <div className="result-card">
              <div className="border-icon">🎯</div>
              <div className="result-details">
                <p className="detected-type">
                  Type: <strong>{result.border.type.toUpperCase()}</strong>
                </p>
                <p className="confidence">
                  Confidence: <strong>{formatConfidence(result.border.confidence)}%</strong>
                </p>
                <div className="border-info">
                  <h4>Border Coordinates</h4>
                  <div className="coordinates">
                    <p>Center: ({result.border.center.x}, {result.border.center.y})</p>
                    {result.border.type === 'circle' ? (
                      <p>Radius: {result.border.radius}px</p>
                    ) : (
                      <>
                        <p>Major axis: {result.border.axes.major}px</p>
                        <p>Minor axis: {result.border.axes.minor}px</p>
                        <p>Rotation: {result.border.angle.toFixed(1)}°</p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="no-detection">
              <p>❌ {result.message}</p>
              <p className="hint">
                Tips: Make sure the disc is clearly visible and takes up most of the image.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
