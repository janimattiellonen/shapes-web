"""Base OCR interface for text detection plugins."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from PIL import Image


class OCRResult:
    """Container for OCR detection results."""

    def __init__(
        self,
        texts: List[str],
        confidences: Optional[List[float]] = None,
        bounding_boxes: Optional[List[Dict[str, Any]]] = None,
        raw_result: Optional[Any] = None
    ):
        """
        Initialize OCR result.

        Args:
            texts: List of detected text strings
            confidences: Optional list of confidence scores (0.0-1.0)
            bounding_boxes: Optional list of bounding box coordinates
            raw_result: Optional raw result from OCR engine
        """
        self.texts = texts
        self.confidences = confidences or []
        self.bounding_boxes = bounding_boxes or []
        self.raw_result = raw_result

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'texts': self.texts,
            'confidences': self.confidences,
            'bounding_boxes': self.bounding_boxes,
            'detected_count': len(self.texts)
        }


class BaseOCR(ABC):
    """Abstract base class for OCR plugins."""

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the display name of this OCR engine.

        Returns:
            Display name of the OCR engine
        """
        pass

    @abstractmethod
    def detect_text(self, image: Image.Image) -> OCRResult:
        """
        Detect text in the provided image.

        Args:
            image: PIL Image object

        Returns:
            OCRResult containing detected texts and metadata
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this OCR engine is available (dependencies installed).

        Returns:
            True if OCR engine can be used, False otherwise
        """
        pass

    def cleanup(self) -> None:
        """
        Optional cleanup method called when OCR engine is no longer needed.
        Override if your OCR engine needs cleanup.
        """
        pass
