"""Base class for all image encoders."""
from abc import ABC, abstractmethod
import numpy as np
from PIL import Image


class ImageEncoder(ABC):
    """Abstract base class for image encoders."""

    @abstractmethod
    def encode(self, image: Image.Image) -> np.ndarray:
        """
        Extract embedding from image.

        Args:
            image: PIL Image object

        Returns:
            numpy array of embedding values
        """
        pass

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """
        Return the dimension size of embeddings.

        Returns:
            Integer dimension size
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Return the model identifier.

        Returns:
            String model name
        """
        pass

    def preprocess_image(self, image: Image.Image, target_size: tuple = None) -> Image.Image:
        """
        Common preprocessing for images.

        Args:
            image: PIL Image object
            target_size: Optional tuple (width, height) to resize to

        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize if target size specified
        if target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)

        return image
