"""Tesseract OCR plugin."""
import logging
from typing import Optional
from PIL import Image

from .base_ocr import BaseOCR, OCRResult

logger = logging.getLogger(__name__)


class TesseractOCR(BaseOCR):
    """Tesseract OCR implementation."""

    def __init__(self):
        """Initialize Tesseract OCR."""
        self._pytesseract = None
        self._load_dependencies()

    def _load_dependencies(self) -> None:
        """Lazy load pytesseract to avoid import errors if not installed."""
        try:
            import pytesseract
            self._pytesseract = pytesseract
        except ImportError:
            logger.warning("pytesseract not installed. Tesseract OCR will not be available.")

    def get_name(self) -> str:
        """Get the display name of this OCR engine."""
        return "Tesseract OCR"

    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        if self._pytesseract is None:
            return False

        try:
            # Try to get tesseract version to verify it's installed
            self._pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.debug(f"Tesseract not available: {e}")
            return False

    def detect_text(self, image: Image.Image) -> OCRResult:
        """
        Detect text using Tesseract OCR.

        Args:
            image: PIL Image object

        Returns:
            OCRResult containing detected texts
        """
        if not self.is_available():
            raise RuntimeError("Tesseract OCR is not available")

        try:
            # Get detailed data from Tesseract
            data = self._pytesseract.image_to_data(
                image,
                output_type=self._pytesseract.Output.DICT
            )

            texts = []
            confidences = []
            bounding_boxes = []

            # Filter out empty detections and low confidence results
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])

                if text and conf > 0:
                    texts.append(text)
                    confidences.append(conf / 100.0)  # Convert to 0-1 range

                    # Create bounding box
                    bounding_boxes.append({
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })

            logger.info(f"Tesseract detected {len(texts)} text items")

            return OCRResult(
                texts=texts,
                confidences=confidences,
                bounding_boxes=bounding_boxes,
                raw_result=data
            )

        except Exception as e:
            logger.error(f"Error during Tesseract OCR: {e}")
            raise RuntimeError(f"Tesseract OCR failed: {str(e)}")
