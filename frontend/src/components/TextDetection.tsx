import { useState, useRef, useEffect } from 'react';
import './TextDetection.css';

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface TextDetectionResult {
  texts: string[];
  confidences: number[];
  bounding_boxes: BoundingBox[];
  detected_count: number;
  ocr_used: string;
}

export function TextDetection() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [availableOCRs, setAvailableOCRs] = useState<string[]>([]);
  const [selectedOCR, setSelectedOCR] = useState<string>('');
  const [result, setResult] = useState<TextDetectionResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingOCRs, setIsLoadingOCRs] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch available OCRs on mount
  useEffect(() => {
    fetchAvailableOCRs();
  }, []);

  const fetchAvailableOCRs = async () => {
    setIsLoadingOCRs(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/discs/text-detection/available-ocrs');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAvailableOCRs(data.ocrs);

      // Auto-select first OCR if available
      if (data.ocrs.length > 0) {
        setSelectedOCR(data.ocrs[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch available OCR engines');
      console.error('Error fetching available OCRs:', err);
    } finally {
      setIsLoadingOCRs(false);
    }
  };

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

  const handleDetectText = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    if (!selectedOCR) {
      setError('Please select an OCR engine');
      return;
    }

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('ocr_name', selectedOCR);

      const response = await fetch('http://localhost:8000/discs/text-detection', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data: TextDetectionResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during text detection');
      console.error('Error detecting text:', err);
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
    <div className="text-detection-container">
      <h2>Disc Text Detection</h2>
      <p className="subtitle">Upload a disc image to detect text using OCR</p>

      {isLoadingOCRs ? (
        <div className="loading-ocrs">Loading available OCR engines...</div>
      ) : availableOCRs.length === 0 ? (
        <div className="error-container">
          <p className="error-message">⚠️ No OCR engines are available. Please install at least one OCR library.</p>
        </div>
      ) : (
        <>
          <div className="ocr-selection">
            <h3>Select OCR Engine</h3>
            <div className="radio-group">
              {availableOCRs.map((ocrName) => (
                <label key={ocrName} className="radio-label">
                  <input
                    type="radio"
                    name="ocr"
                    value={ocrName}
                    checked={selectedOCR === ocrName}
                    onChange={(e) => setSelectedOCR(e.target.value)}
                  />
                  <span>{ocrName}</span>
                </label>
              ))}
            </div>
          </div>

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
                  src={previewUrl}
                  alt="Preview"
                  className="preview-image"
                />
              </div>
            )}
          </div>

          <div className="action-buttons">
            {selectedFile && (
              <>
                <button
                  onClick={handleDetectText}
                  disabled={isLoading || !selectedOCR}
                  className="detect-button"
                >
                  {isLoading ? 'Processing file...' : 'Detect Text'}
                </button>
                <button onClick={handleReset} className="reset-button" disabled={isLoading}>
                  {result ? 'Try Another Image' : 'Clear'}
                </button>
              </>
            )}
          </div>

          {error && (
            <div className="error-container">
              <p className="error-message">⚠️ {error}</p>
            </div>
          )}

          {result && (
            <div className="result-container">
              <h3>Detection Results</h3>
              <div className="result-header">
                <p><strong>OCR Engine:</strong> {result.ocr_used}</p>
                <p><strong>Detected Items:</strong> {result.detected_count}</p>
              </div>

              {result.detected_count > 0 ? (
                <div className="detected-texts">
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Text</th>
                        <th>Confidence</th>
                        <th>Position</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.texts.map((text, index) => (
                        <tr key={index}>
                          <td>{index + 1}</td>
                          <td className="text-cell">{text}</td>
                          <td className="confidence-cell">
                            {result.confidences[index] !== undefined
                              ? `${formatConfidence(result.confidences[index])}%`
                              : 'N/A'}
                          </td>
                          <td className="position-cell">
                            {result.bounding_boxes[index] && (
                              <>
                                x: {result.bounding_boxes[index].x}, y: {result.bounding_boxes[index].y}
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="no-detection">
                  <p>❌ No text detected in the image.</p>
                  <p className="hint">
                    Try using a different OCR engine or ensure the text is clearly visible.
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
