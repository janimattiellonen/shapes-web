"""PaddleOCR plugin."""
import logging
import numpy as np
from PIL import Image

from .base_ocr import BaseOCR, OCRResult

logger = logging.getLogger(__name__)


class PaddleOCRPlugin(BaseOCR):
    """PaddleOCR implementation."""

    def __init__(self):
        """Initialize PaddleOCR."""
        self._paddleocr = None
        self._ocr = None
        self._load_dependencies()

    def _load_dependencies(self) -> None:
        """Lazy load paddleocr to avoid import errors if not installed."""
        try:
            from paddleocr import PaddleOCR
            self._paddleocr = PaddleOCR
        except ImportError:
            logger.warning("paddleocr not installed. PaddleOCR will not be available.")

    def get_name(self) -> str:
        """Get the display name of this OCR engine."""
        return "PaddleOCR"

    def is_available(self) -> bool:
        """Check if PaddleOCR is available."""
        return self._paddleocr is not None

    def _get_ocr(self):
        """Get or create PaddleOCR instance."""
        if self._ocr is None:
            if not self.is_available():
                raise RuntimeError("PaddleOCR is not available")

            try:
                # Initialize PaddleOCR with English language
                # use_angle_cls=True for rotated text detection
                # use_gpu=False to avoid CUDA dependency issues
                self._ocr = self._paddleocr(
                    use_angle_cls=True,
                    lang='en',
                    use_gpu=False,
                    show_log=False
                )
                logger.info("PaddleOCR initialized")
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                raise RuntimeError(f"Failed to initialize PaddleOCR: {str(e)}")

        return self._ocr

    def detect_text(self, image: Image.Image) -> OCRResult:
        """
        Detect text using PaddleOCR.

        Args:
            image: PIL Image object

        Returns:
            OCRResult containing detected texts
        """
        if not self.is_available():
            raise RuntimeError("PaddleOCR is not available")

        try:
            ocr = self._get_ocr()

            # Convert PIL image to numpy array
            image_np = np.array(image)

            # Perform OCR
            # Returns list of results for each detected text region
            # Each result is [bbox, (text, confidence)]
            results = ocr.ocr(image_np, cls=True)

            texts = []
            confidences = []
            bounding_boxes = []

            # Parse results
            # results is a list (one per image), each containing a list of detections
            if results and results[0]:
                for line in results[0]:
                    bbox, (text, conf) = line

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

            logger.info(f"PaddleOCR detected {len(texts)} text items")

            return OCRResult(
                texts=texts,
                confidences=confidences,
                bounding_boxes=bounding_boxes,
                raw_result=results
            )

        except Exception as e:
            logger.error(f"Error during PaddleOCR: {e}")
            raise RuntimeError(f"PaddleOCR failed: {str(e)}")

    def cleanup(self) -> None:
        """Cleanup PaddleOCR instance."""
        if self._ocr is not None:
            del self._ocr
            self._ocr = None
            logger.info("PaddleOCR cleaned up")
