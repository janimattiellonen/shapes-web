"""Service for disc registration operations."""
import io
import logging
from typing import Dict, Optional, Union
from pathlib import Path
from PIL import Image

from .disc_matcher import DiscMatcher
from .config import Config
from .utils.image_utils import load_image_with_orientation

logger = logging.getLogger(__name__)


class DiscRegistrationResult:
    """Result of a disc registration operation."""

    def __init__(
        self,
        success: bool,
        disc_id: Optional[int] = None,
        image_id: Optional[int] = None,
        model_used: Optional[str] = None,
        border_detected: bool = False,
        border_confidence: float = 0.0,
        error_message: Optional[str] = None,
        filename: Optional[str] = None
    ):
        self.success = success
        self.disc_id = disc_id
        self.image_id = image_id
        self.model_used = model_used
        self.border_detected = border_detected
        self.border_confidence = border_confidence
        self.error_message = error_message
        self.filename = filename

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'disc_id': self.disc_id,
            'image_id': self.image_id,
            'model_used': self.model_used,
            'border_detected': self.border_detected,
            'border_confidence': self.border_confidence,
            'error_message': self.error_message,
            'filename': self.filename
        }


class DiscRegistrationService:
    """Service for registering discs from various sources."""

    def __init__(self, disc_matcher: Optional[DiscMatcher] = None):
        """
        Initialize disc registration service.

        Args:
            disc_matcher: DiscMatcher instance (creates new if not provided)
        """
        self.disc_matcher = disc_matcher or DiscMatcher()

    def validate_image_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate image file.

        Args:
            file_path: Path to image file

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        # Check file extension
        if file_path.suffix.lower() not in Config.ALLOWED_EXTENSIONS:
            return False, f"Invalid file extension: {file_path.suffix}. Allowed: {Config.ALLOWED_EXTENSIONS}"

        # Check file size
        file_size = file_path.stat().st_size
        max_size = Config.get_max_image_size_bytes()
        if file_size > max_size:
            return False, f"File too large: {file_size} bytes (max: {max_size} bytes)"

        return True, None

    def register_from_file(
        self,
        image_path: Union[str, Path],
        owner_name: str = "Pending",
        owner_contact: str = "pending@example.com",
        disc_model: Optional[str] = None,
        disc_color: Optional[str] = None,
        notes: Optional[str] = None,
        location: Optional[str] = None,
        status: str = 'registered',
        upload_status: str = 'SUCCESS'
    ) -> DiscRegistrationResult:
        """
        Register a disc from an image file.

        Args:
            image_path: Path to image file
            owner_name: Owner's name
            owner_contact: Owner's contact info
            disc_model: Disc model/brand
            disc_color: Disc color
            notes: Additional notes
            location: Location info
            status: Disc status
            upload_status: Upload status (PENDING, SUCCESS)

        Returns:
            DiscRegistrationResult with registration details
        """
        image_path = Path(image_path)

        # Validate file
        is_valid, error_message = self.validate_image_file(image_path)
        if not is_valid:
            logger.warning(f"Invalid image file: {error_message}")
            return DiscRegistrationResult(
                success=False,
                error_message=error_message,
                filename=image_path.name
            )

        try:
            # Load image with EXIF orientation correction
            pil_image = load_image_with_orientation(str(image_path))

            # Register disc
            result = self._register_disc_image(
                image=pil_image,
                filename=image_path.name,
                owner_name=owner_name,
                owner_contact=owner_contact,
                disc_model=disc_model,
                disc_color=disc_color,
                notes=notes,
                location=location,
                status=status,
                upload_status=upload_status
            )

            return result

        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            logger.error(f"{error_msg} - {image_path}")
            return DiscRegistrationResult(
                success=False,
                error_message=error_msg,
                filename=image_path.name
            )

    def register_from_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        owner_name: str = "Pending",
        owner_contact: str = "pending@example.com",
        disc_model: Optional[str] = None,
        disc_color: Optional[str] = None,
        notes: Optional[str] = None,
        location: Optional[str] = None,
        status: str = 'registered',
        upload_status: str = 'SUCCESS'
    ) -> DiscRegistrationResult:
        """
        Register a disc from image bytes (for HTTP uploads).

        Args:
            image_bytes: Image file contents as bytes
            filename: Original filename
            owner_name: Owner's name
            owner_contact: Owner's contact info
            disc_model: Disc model/brand
            disc_color: Disc color
            notes: Additional notes
            location: Location info
            status: Disc status
            upload_status: Upload status (PENDING, SUCCESS)

        Returns:
            DiscRegistrationResult with registration details
        """
        # Validate file size
        if len(image_bytes) > Config.get_max_image_size_bytes():
            error_msg = f"File too large: {len(image_bytes)} bytes (max: {Config.get_max_image_size_bytes()} bytes)"
            return DiscRegistrationResult(
                success=False,
                error_message=error_msg,
                filename=filename
            )

        try:
            # Load image with EXIF orientation correction
            pil_image = load_image_with_orientation(io.BytesIO(image_bytes))

            # Register disc
            result = self._register_disc_image(
                image=pil_image,
                filename=filename,
                owner_name=owner_name,
                owner_contact=owner_contact,
                disc_model=disc_model,
                disc_color=disc_color,
                notes=notes,
                location=location,
                status=status,
                upload_status=upload_status
            )

            return result

        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            logger.error(f"{error_msg} - {filename}")
            return DiscRegistrationResult(
                success=False,
                error_message=error_msg,
                filename=filename
            )

    def _register_disc_image(
        self,
        image: Image.Image,
        filename: str,
        owner_name: str,
        owner_contact: str,
        disc_model: Optional[str],
        disc_color: Optional[str],
        notes: Optional[str],
        location: Optional[str],
        status: str,
        upload_status: str
    ) -> DiscRegistrationResult:
        """
        Internal method to register a PIL Image.

        Args:
            image: PIL Image object
            filename: Original filename
            owner_name: Owner's name
            owner_contact: Owner's contact info
            disc_model: Disc model/brand
            disc_color: Disc color
            notes: Additional notes
            location: Location info
            status: Disc status
            upload_status: Upload status

        Returns:
            DiscRegistrationResult with registration details
        """
        try:
            # Add to database via DiscMatcher
            result = self.disc_matcher.add_disc(
                image=image,
                owner_name=owner_name,
                owner_contact=owner_contact,
                image_filename=filename,
                disc_model=disc_model,
                disc_color=disc_color,
                notes=notes,
                status=status,
                location=location,
                upload_status=upload_status
            )

            return DiscRegistrationResult(
                success=True,
                disc_id=result['disc_id'],
                image_id=result['image_id'],
                model_used=result['model_used'],
                border_detected=result.get('border_detected', False),
                border_confidence=result.get('border_confidence', 0.0),
                filename=filename
            )

        except Exception as e:
            error_msg = f"Error registering disc: {str(e)}"
            logger.error(f"{error_msg} - {filename}")
            return DiscRegistrationResult(
                success=False,
                error_message=error_msg,
                filename=filename
            )
