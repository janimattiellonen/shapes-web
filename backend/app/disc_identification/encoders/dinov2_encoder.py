"""DINOv2-based image encoder."""
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel
from .base_encoder import ImageEncoder


class DINOv2Encoder(ImageEncoder):
    """Image encoder using Meta's DINOv2 model."""

    def __init__(self, model_name: str = "facebook/dinov2-base"):
        """
        Initialize DINOv2 encoder.

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name_full = model_name
        self.model = AutoModel.from_pretrained(model_name)
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model.eval()

        # Disable gradients for inference
        for param in self.model.parameters():
            param.requires_grad = False

    def encode(self, image: Image.Image) -> np.ndarray:
        """
        Extract DINOv2 embedding from image.

        Args:
            image: PIL Image object

        Returns:
            768-dimensional numpy array
        """
        # Preprocess image
        image = self.preprocess_image(image)

        # Process with DINOv2
        inputs = self.processor(images=image, return_tensors="pt")

        # Extract features without gradients
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use CLS token (first token) as embedding
            embedding = outputs.last_hidden_state[:, 0, :].squeeze()

        # Convert to numpy
        embedding_np = embedding.cpu().numpy()

        return embedding_np

    def get_embedding_dim(self) -> int:
        """Return embedding dimension."""
        return 768

    def get_model_name(self) -> str:
        """Return model identifier."""
        return "dinov2"
