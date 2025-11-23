"""EasyOCR plugin."""
import logging
import numpy as np
from PIL import Image

from .base_ocr import BaseOCR, OCRResult

logger = logging.getLogger(__name__)


class EasyOCRPlugin(BaseOCR):
    """EasyOCR implementation."""

    def __init__(self):
        """Initialize EasyOCR."""
        self._easyocr = None
        self._reader = None
        self._load_dependencies()

    def _load_dependencies(self) -> None:
        """Lazy load easyocr to avoid import errors if not installed."""
        try:
            import easyocr
            self._easyocr = easyocr
        except ImportError:
            logger.warning("easyocr not installed. EasyOCR will not be available.")

    def get_name(self) -> str:
        """Get the display name of this OCR engine."""
        return "EasyOCR"

    def is_available(self) -> bool:
        """Check if EasyOCR is available."""
        return self._easyocr is not None

    def _get_reader(self):
        """Get or create EasyOCR reader instance."""
        if self._reader is None:
            if not self.is_available():
                raise RuntimeError("EasyOCR is not available")

            try:
                # Initialize with English language
                # gpu=False to avoid CUDA dependency issues
                self._reader = self._easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR reader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR reader: {e}")
                raise RuntimeError(f"Failed to initialize EasyOCR: {str(e)}")

        return self._reader

    def detect_text(self, image: Image.Image) -> OCRResult:
        """
        Detect text using EasyOCR.

        Args:
            image: PIL Image object

        Returns:
            OCRResult containing detected texts
        """
        if not self.is_available():
            raise RuntimeError("EasyOCR is not available")

        try:
            reader = self._get_reader()

            # Convert PIL image to numpy array
            image_np = np.array(image)

            # Perform OCR
            results = reader.readtext(image_np)

            texts = []
            confidences = []
            bounding_boxes = []

            # Parse results
            # EasyOCR returns list of ([bbox], text, confidence)
            for bbox, text, conf in results:
                texts.append(text)
                confidences.append(float(conf))

                # Convert bbox to our format
                # bbox is a list of 4 corner points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]

                x_min = min(x_coords)
                y_min = min(y_coords)
                width = max(x_coords) - x_min
                height = max(y_coords) - y_min

                bounding_boxes.append({
                    'x': int(x_min),
                    'y': int(y_min),
                    'width': int(width),
                    'height': int(height)
                })

            logger.info(f"EasyOCR detected {len(texts)} text items")

            return OCRResult(
                texts=texts,
                confidences=confidences,
                bounding_boxes=bounding_boxes,
                raw_result=results
            )

        except Exception as e:
            logger.error(f"Error during EasyOCR: {e}")
            raise RuntimeError(f"EasyOCR failed: {str(e)}")

    def cleanup(self) -> None:
        """Cleanup EasyOCR reader."""
        if self._reader is not None:
            del self._reader
            self._reader = None
            logger.info("EasyOCR reader cleaned up")
