"""
Shape prediction service for loading and using the trained Keras model.
Singleton pattern ensures model is loaded only once.
"""

import numpy as np
from PIL import Image
import io
import os
from typing import Dict, Tuple
from app.ml.shape_classifier import ShapeClassifier


class ShapePredictor:
    """Singleton service for shape prediction."""

    _instance = None
    _model = None
    _class_names = ['circle', 'triangle', 'rectangle']

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShapePredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the predictor and load the model if not already loaded."""
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """Load the trained Keras model from disk."""
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'ml', 'models', 'shape_classifier.keras'
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please ensure shape_classifier.keras is in backend/app/ml/models/"
            )

        print(f"Loading model from {model_path}...")
        classifier = ShapeClassifier(img_size=128, num_classes=3)
        classifier.load_model(model_path)
        self._model = classifier.model
        print("Model loaded successfully!")

    @staticmethod
    def preprocess_image(image_bytes: bytes) -> np.ndarray:
        """
        Preprocess uploaded image for model prediction.

        Args:
            image_bytes: Raw image bytes from upload

        Returns:
            Preprocessed image array ready for prediction (1, 128, 128, 3)
        """
        # Open image from bytes
        img = Image.open(io.BytesIO(image_bytes))

        # Handle transparency by converting to white background
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))

            # Convert image to RGBA if needed
            if img.mode == 'P':
                img = img.convert('RGBA')

            # Composite the image on white background
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            else:
                background.paste(img)

            img = background
        else:
            # Convert to RGB if not already
            img = img.convert('RGB')

        # Resize to model input size (128x128)
        img = img.resize((128, 128), Image.Resampling.LANCZOS)

        # Convert to numpy array and normalize
        img_array = np.array(img, dtype=np.float32)
        img_array = img_array / 255.0  # Normalize to [0, 1]

        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)

        return img_array

    def predict(self, image_bytes: bytes) -> Dict[str, any]:
        """
        Predict the shape in the uploaded image.

        Args:
            image_bytes: Raw image bytes from upload

        Returns:
            Dictionary with prediction results:
            {
                "shape": "circle",
                "confidence": 0.95,
                "probabilities": {
                    "circle": 0.95,
                    "triangle": 0.03,
                    "rectangle": 0.02
                }
            }
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Cannot make predictions.")

        # Preprocess the image
        processed_image = self.preprocess_image(image_bytes)

        # Make prediction
        predictions = self._model.predict(processed_image, verbose=0)

        # Get predicted class and confidence
        predicted_class_idx = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][predicted_class_idx])
        predicted_shape = self._class_names[predicted_class_idx]

        # Create probabilities dictionary
        probabilities = {
            class_name: float(predictions[0][i])
            for i, class_name in enumerate(self._class_names)
        }

        return {
            "shape": predicted_shape,
            "confidence": confidence,
            "probabilities": probabilities
        }

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of ShapePredictor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
