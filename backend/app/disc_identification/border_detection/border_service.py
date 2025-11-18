"""
Border Detection Service

Orchestrates border detection and image processing workflow.
Provides a high-level interface for detecting disc borders and generating
cropped images.
"""
from PIL import Image
from typing import Dict, Optional, Tuple
from datetime import datetime
import os
import logging

from .disc_border_detector import DiscBorderDetector
from .border_processor import BorderProcessor
from ..config import Config

logger = logging.getLogger(__name__)


class BorderDetectionResult:
    """
    Result of border detection and processing operation.

    Attributes:
        detected: Whether a border was detected
        border_info: Border detection metadata (type, center, radius, etc.)
        confidence: Detection confidence score (0-1)
        cropped_image: PIL Image of the cropped disc region (if successful)
        cropped_image_path: Path where cropped image was saved (if saved)
        preprocessing_metadata: Additional metadata about processing
    """

    def __init__(
        self,
        detected: bool,
        border_info: Optional[Dict] = None,
        confidence: float = 0.0,
        cropped_image: Optional[Image.Image] = None,
        cropped_image_path: Optional[str] = None,
        preprocessing_metadata: Optional[Dict] = None
    ):
        self.detected = detected
        self.border_info = border_info
        self.confidence = confidence
        self.cropped_image = cropped_image
        self.cropped_image_path = cropped_image_path
        self.preprocessing_metadata = preprocessing_metadata or {}

    def to_dict(self) -> Dict:
        """Convert result to dictionary for storage/serialization."""
        return {
            'detected': self.detected,
            'border_info': self.border_info,
            'confidence': self.confidence,
            'cropped_image_path': self.cropped_image_path,
            'preprocessing_metadata': self.preprocessing_metadata
        }


class BorderService:
    """
    Service for detecting disc borders and processing images.

    Combines border detection with image processing to provide a complete
    workflow for extracting disc regions from images.
    """

    def __init__(
        self,
        detector: Optional[DiscBorderDetector] = None,
        confidence_threshold: float = None
    ):
        """
        Initialize border service.

        Args:
            detector: Border detector instance (creates new if not provided)
            confidence_threshold: Minimum confidence for accepting detection
                                 (uses config default if not provided)
        """
        self.detector = detector or DiscBorderDetector()
        self.processor = BorderProcessor()
        self.confidence_threshold = confidence_threshold or Config.BORDER_CONFIDENCE_THRESHOLD

    def detect_and_process(
        self,
        image: Image.Image,
        disc_id: Optional[int] = None,
        save_cropped: bool = True,
        padding: int = 0
    ) -> BorderDetectionResult:
        """
        Detect border and create cropped image.

        This is the main entry point for border detection workflow.

        Args:
            image: PIL Image to process
            disc_id: Optional disc ID for saving cropped image
            save_cropped: Whether to save the cropped image to disk
            padding: Optional padding around detected border (pixels)

        Returns:
            BorderDetectionResult with detection info and cropped image
        """
        logger.info(f"Starting border detection for disc_id={disc_id}")

        # Step 1: Detect border
        border_info = self.detector.detect_border(image)

        if border_info is None:
            logger.warning("No border detected")
            return BorderDetectionResult(
                detected=False,
                border_info=None,
                confidence=0.0,
                preprocessing_metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'border_detection',
                    'padding': padding
                }
            )

        confidence = border_info.get('confidence', 0.0)
        logger.info(f"Border detected: {border_info['type']} with confidence {confidence:.2f}")

        # Check confidence threshold
        if confidence < self.confidence_threshold:
            logger.warning(
                f"Border confidence {confidence:.2f} below threshold "
                f"{self.confidence_threshold}"
            )
            return BorderDetectionResult(
                detected=True,
                border_info=border_info,
                confidence=confidence,
                preprocessing_metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'border_detection',
                    'padding': padding,
                    'below_threshold': True
                }
            )

        # Step 2: Create cropped image
        try:
            cropped_image = self.processor.create_cropped_image(
                image,
                border_info,
                padding=padding
            )
            logger.info(f"Created cropped image: {cropped_image.size}")

        except Exception as e:
            logger.error(f"Failed to create cropped image: {e}")
            return BorderDetectionResult(
                detected=True,
                border_info=border_info,
                confidence=confidence,
                preprocessing_metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'border_detection',
                    'padding': padding,
                    'crop_error': str(e)
                }
            )

        # Step 3: Save cropped image (if requested and disc_id provided)
        cropped_image_path = None
        if save_cropped and disc_id is not None:
            try:
                cropped_image_path = self._save_cropped_image(
                    cropped_image,
                    disc_id
                )
                logger.info(f"Saved cropped image to {cropped_image_path}")

            except Exception as e:
                logger.error(f"Failed to save cropped image: {e}")

        # Step 4: Build result
        result = BorderDetectionResult(
            detected=True,
            border_info=border_info,
            confidence=confidence,
            cropped_image=cropped_image,
            cropped_image_path=cropped_image_path,
            preprocessing_metadata={
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'border_detection',
                'border_type': border_info['type'],
                'padding': padding,
                'cropped_size': cropped_image.size,
                'saved': cropped_image_path is not None
            }
        )

        return result

    def _save_cropped_image(
        self,
        image: Image.Image,
        disc_id: int
    ) -> str:
        """
        Save cropped image to disk.

        Args:
            image: PIL Image to save
            disc_id: Disc ID for directory organization

        Returns:
            Path to saved image

        Raises:
            IOError: If save fails
        """
        # Create disc directory if it doesn't exist
        disc_dir = os.path.join(Config.UPLOAD_DIR, str(disc_id))
        os.makedirs(disc_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cropped_{timestamp}.jpg"
        image_path = os.path.join(disc_dir, filename)

        # Save image
        image.save(image_path, quality=95)

        logger.debug(f"Saved cropped image to {image_path}")

        return image_path

    def create_mask(
        self,
        image: Image.Image,
        border_info: Dict
    ) -> Optional[Image.Image]:
        """
        Create a binary mask for the detected border.

        Useful for future implementations that need masking instead of cropping.

        Args:
            image: Source image (for size reference)
            border_info: Border detection results

        Returns:
            Binary mask image (L mode), or None if border_info invalid
        """
        if not border_info:
            return None

        try:
            mask = self.processor.create_circular_mask(
                image.size,
                border_info
            )
            return mask

        except Exception as e:
            logger.error(f"Failed to create mask: {e}")
            return None

    def should_use_cropped(
        self,
        border_result: BorderDetectionResult
    ) -> bool:
        """
        Determine if cropped image should be used based on detection quality.

        Args:
            border_result: Border detection result

        Returns:
            True if cropped image is suitable for use, False otherwise
        """
        if not border_result.detected:
            return False

        if border_result.confidence < self.confidence_threshold:
            return False

        if border_result.cropped_image is None:
            return False

        return True

    def apply_border(
        self,
        image: Image.Image,
        border_info: Dict,
        disc_id: Optional[int] = None,
        save_cropped: bool = True,
        padding: int = 0
    ) -> BorderDetectionResult:
        """
        Apply a manual border (from user editing) and create cropped image.

        Similar to detect_and_process but uses provided border_info instead
        of running detection.

        Args:
            image: PIL Image to process
            border_info: Border information (type, center, radius/axes, angle)
            disc_id: Optional disc ID for saving cropped image
            save_cropped: Whether to save the cropped image to disk
            padding: Optional padding around border (pixels)

        Returns:
            BorderDetectionResult with cropped image and processing info
        """
        logger.info(f"Applying manual border for disc_id={disc_id}")

        # Manually set confidence to 1.0 since this is user-provided
        confidence = border_info.get('confidence', 1.0)

        # Create cropped image
        try:
            cropped_image = self.processor.create_cropped_image(
                image,
                border_info,
                padding=padding
            )
            logger.info(f"Created cropped image from manual border: {cropped_image.size}")

        except Exception as e:
            logger.error(f"Failed to create cropped image from manual border: {e}")
            return BorderDetectionResult(
                detected=True,
                border_info=border_info,
                confidence=confidence,
                preprocessing_metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'manual_border',
                    'padding': padding,
                    'crop_error': str(e)
                }
            )

        # Save cropped image (if requested and disc_id provided)
        cropped_image_path = None
        if save_cropped and disc_id is not None:
            try:
                cropped_image_path = self._save_cropped_image(
                    cropped_image,
                    disc_id
                )
                logger.info(f"Saved cropped image to {cropped_image_path}")

            except Exception as e:
                logger.error(f"Failed to save cropped image: {e}")

        # Build result
        result = BorderDetectionResult(
            detected=True,
            border_info=border_info,
            confidence=confidence,
            cropped_image=cropped_image,
            cropped_image_path=cropped_image_path,
            preprocessing_metadata={
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'manual_border',
                'border_type': border_info['type'],
                'padding': padding,
                'cropped_size': cropped_image.size,
                'saved': cropped_image_path is not None
            }
        )

        return result
