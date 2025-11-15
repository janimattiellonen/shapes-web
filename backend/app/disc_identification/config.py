"""Configuration for disc identification system."""
import os
from typing import Optional


class Config:
    """Configuration class for disc identification."""

    # Encoder configuration - Change this to switch models!
    ENCODER_TYPE: str = os.getenv('ENCODER_TYPE', 'clip')  # 'clip' or 'dinov2'

    # Database configuration
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5440/disc_identification'
    )

    # Image storage configuration
    UPLOAD_DIR: str = os.getenv('UPLOAD_DIR', '/app/uploads/discs')
    MAX_IMAGE_SIZE_MB: int = int(os.getenv('MAX_IMAGE_SIZE_MB', '10'))
    ALLOWED_EXTENSIONS: set = {'.jpg', '.jpeg', '.png'}

    # Search configuration
    DEFAULT_TOP_K: int = int(os.getenv('DEFAULT_TOP_K', '10'))
    MIN_SIMILARITY_THRESHOLD: float = float(os.getenv('MIN_SIMILARITY_THRESHOLD', '0.7'))

    @classmethod
    def get_max_image_size_bytes(cls) -> int:
        """Get maximum image size in bytes."""
        return cls.MAX_IMAGE_SIZE_MB * 1024 * 1024

    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        valid_encoders = ['clip', 'dinov2']
        if cls.ENCODER_TYPE not in valid_encoders:
            raise ValueError(
                f"Invalid ENCODER_TYPE: {cls.ENCODER_TYPE}. "
                f"Must be one of: {', '.join(valid_encoders)}"
            )
