"""Factory for creating image encoders."""
from .base_encoder import ImageEncoder
from .clip_encoder import CLIPEncoder
from .dinov2_encoder import DINOv2Encoder


class EncoderFactory:
    """Factory for creating image encoder instances."""

    _encoders = {
        'clip': CLIPEncoder,
        'dinov2': DINOv2Encoder,
    }

    @classmethod
    def create(cls, encoder_type: str) -> ImageEncoder:
        """
        Create an encoder instance.

        Args:
            encoder_type: Type of encoder ('clip' or 'dinov2')

        Returns:
            ImageEncoder instance

        Raises:
            ValueError: If encoder_type is not recognized
        """
        if encoder_type not in cls._encoders:
            available = ', '.join(cls._encoders.keys())
            raise ValueError(
                f"Unknown encoder type: '{encoder_type}'. "
                f"Available encoders: {available}"
            )

        return cls._encoders[encoder_type]()

    @classmethod
    def get_available_encoders(cls) -> list[str]:
        """
        Get list of available encoder types.

        Returns:
            List of encoder type names
        """
        return list(cls._encoders.keys())
