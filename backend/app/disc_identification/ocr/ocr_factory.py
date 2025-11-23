"""Factory for creating and managing OCR instances."""
from typing import Dict, List, Type, Optional
import logging

from .base_ocr import BaseOCR

logger = logging.getLogger(__name__)


class OCRFactory:
    """Factory for creating OCR instances."""

    # Registry of available OCR classes
    _ocr_registry: Dict[str, Type[BaseOCR]] = {}

    @classmethod
    def register_ocr(cls, ocr_class: Type[BaseOCR]) -> None:
        """
        Register an OCR class.

        Args:
            ocr_class: OCR class to register
        """
        # Create temporary instance to get the name
        try:
            instance = ocr_class()
            name = instance.get_name()
            cls._ocr_registry[name] = ocr_class
            logger.info(f"Registered OCR engine: {name}")
        except Exception as e:
            logger.error(f"Failed to register OCR class {ocr_class.__name__}: {e}")

    @classmethod
    def create_ocr(cls, ocr_name: str) -> Optional[BaseOCR]:
        """
        Create an OCR instance by name.

        Args:
            ocr_name: Name of the OCR engine

        Returns:
            OCR instance or None if not found/available
        """
        ocr_class = cls._ocr_registry.get(ocr_name)

        if ocr_class is None:
            logger.error(f"OCR engine '{ocr_name}' not found in registry")
            return None

        try:
            instance = ocr_class()
            if not instance.is_available():
                logger.error(f"OCR engine '{ocr_name}' is not available (missing dependencies)")
                return None
            return instance
        except Exception as e:
            logger.error(f"Failed to create OCR instance for '{ocr_name}': {e}")
            return None

    @classmethod
    def get_available_ocrs(cls) -> List[str]:
        """
        Get list of available OCR engine names.

        Returns:
            List of OCR engine names that are available
        """
        available = []
        for name, ocr_class in cls._ocr_registry.items():
            try:
                instance = ocr_class()
                if instance.is_available():
                    available.append(name)
            except Exception as e:
                logger.debug(f"OCR engine '{name}' is not available: {e}")

        return available

    @classmethod
    def get_all_registered_ocrs(cls) -> List[str]:
        """
        Get list of all registered OCR engine names (even if not available).

        Returns:
            List of all registered OCR engine names
        """
        return list(cls._ocr_registry.keys())
