"""CLIP-based image encoder."""
import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from .base_encoder import ImageEncoder


class CLIPEncoder(ImageEncoder):
    """Image encoder using OpenAI's CLIP model."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize CLIP encoder.

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name_full = model_name
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

        # Disable gradients for inference
        for param in self.model.parameters():
            param.requires_grad = False

    def encode(self, image: Image.Image) -> np.ndarray:
        """
        Extract CLIP embedding from image.

        Args:
            image: PIL Image object

        Returns:
            512-dimensional numpy array (padded to 768 for compatibility)
        """
        # Preprocess image
        image = self.preprocess_image(image)

        # Process with CLIP
        inputs = self.processor(images=image, return_tensors="pt")

        # Extract features without gradients
        with torch.no_grad():
            embedding = self.model.get_image_features(**inputs)

        # Convert to numpy and flatten
        embedding_np = embedding.cpu().numpy().flatten()

        # Pad to 768 dimensions for database compatibility (DINOv2 uses 768)
        padded_embedding = np.pad(embedding_np, (0, 768 - len(embedding_np)), mode='constant')

        return padded_embedding

    def get_embedding_dim(self) -> int:
        """Return embedding dimension (padded to 768)."""
        return 768

    def get_model_name(self) -> str:
        """Return model identifier."""
        return "clip"
