"""OCR service for text detection operations."""
import logging
from typing import List, Dict, Any
from PIL import Image

from .ocr_factory import OCRFactory
from .base_ocr import OCRResult

logger = logging.getLogger(__name__)


class OCRService:
    """Service for managing OCR operations."""

    @staticmethod
    def get_available_ocrs() -> List[str]:
        """
        Get list of available OCR engines.

        Returns:
            List of OCR engine names
        """
        return OCRFactory.get_available_ocrs()

    @staticmethod
    def detect_text(image: Image.Image, ocr_name: str) -> OCRResult:
        """
        Detect text in image using specified OCR engine.

        Args:
            image: PIL Image object
            ocr_name: Name of OCR engine to use

        Returns:
            OCRResult containing detected texts

        Raises:
            ValueError: If OCR engine not found or not available
            RuntimeError: If OCR detection fails
        """
        logger.info(f"Detecting text using {ocr_name}")

        ocr = OCRFactory.create_ocr(ocr_name)
        if ocr is None:
            raise ValueError(f"OCR engine '{ocr_name}' not found or not available")

        try:
            result = ocr.detect_text(image)
            logger.info(f"Text detection completed: {len(result.texts)} items found")
            return result
        except Exception as e:
            logger.error(f"Text detection failed with {ocr_name}: {e}")
            raise
        finally:
            # Cleanup OCR instance
            try:
                ocr.cleanup()
            except Exception as e:
                logger.warning(f"Error during OCR cleanup: {e}")
