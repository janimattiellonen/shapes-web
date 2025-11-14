"""
CNN model for geometric shape classification.
Works with standard TensorFlow (CPU/GPU) and Apple Silicon with Metal.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
import os


class ShapeClassifier:
    """Convolutional Neural Network for classifying geometric shapes."""

    def __init__(self, img_size=128, num_classes=3):
        """
        Initialize the shape classifier.

        Args:
            img_size: Size of input images (square)
            num_classes: Number of shape classes to classify
        """
        self.img_size = img_size
        self.num_classes = num_classes
        self.model = None
        self.history = None

        # Configure TensorFlow for available hardware
        self._configure_hardware()

    def _configure_hardware(self):
        """Configure TensorFlow to optimize for available hardware (CPU/GPU/Metal)."""
        try:
            # Check if GPU is available
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                print(f"GPU(s) detected: {len(gpus)} device(s)")
                for gpu in gpus:
                    print(f"  - {gpu}")
                    # Enable memory growth to avoid allocating all GPU memory at once
                    try:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    except RuntimeError as e:
                        print(f"Memory growth setting: {e}")
            else:
                print("No GPU detected. Running on CPU.")
        except Exception as e:
            print(f"Hardware configuration: {e}. Using defaults.")

    def build_model(self):
        """
        Build the CNN architecture for shape classification.

        Architecture:
        - 3 Convolutional blocks with MaxPooling
        - Batch normalization for stability
        - Dropout for regularization
        - Dense layers for classification
        """
        model = models.Sequential([
            # Input layer
            layers.Input(shape=(self.img_size, self.img_size, 3)),

            # First convolutional block
            layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),

            # Second convolutional block
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),

            # Third convolutional block
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.4),

            # Flatten and dense layers
            layers.Flatten(),
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),

            # Output layer
            layers.Dense(self.num_classes, activation='softmax')
        ])

        self.model = model
        return model

    def compile_model(self, learning_rate=0.001):
        """
        Compile the model with optimizer and loss function.

        Args:
            learning_rate: Learning rate for Adam optimizer
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

    def train(self, X_train, y_train, X_val, y_val,
              epochs=50, batch_size=32, callbacks=None):
        """
        Train the model on the provided data.

        Args:
            X_train: Training images
            y_train: Training labels
            X_val: Validation images
            y_val: Validation labels
            epochs: Number of training epochs
            batch_size: Batch size for training
            callbacks: List of Keras callbacks

        Returns:
            Training history
        """
        if self.model is None:
            raise ValueError("Model not compiled. Call compile_model() first.")

        if callbacks is None:
            callbacks = [
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7
                )
            ]

        print("\nStarting training...")
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        return self.history

    def evaluate(self, X_test, y_test):
        """
        Evaluate the model on test data.

        Args:
            X_test: Test images
            y_test: Test labels

        Returns:
            Test loss and accuracy
        """
        if self.model is None:
            raise ValueError("Model not trained.")

        results = self.model.evaluate(X_test, y_test, verbose=0)
        return results

    def predict(self, images):
        """
        Make predictions on new images.

        Args:
            images: numpy array of images (N, H, W, 3)

        Returns:
            Predicted class indices and probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained.")

        predictions = self.model.predict(images)
        predicted_classes = tf.argmax(predictions, axis=1).numpy()

        return predicted_classes, predictions

    def save_model(self, filepath='models/shape_classifier.keras'):
        """
        Save the trained model to disk.

        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("No model to save.")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath='models/shape_classifier.keras'):
        """
        Load a trained model from disk.

        Args:
            filepath: Path to the saved model
        """
        self.model = keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")

    def summary(self):
        """Print model architecture summary."""
        if self.model is None:
            raise ValueError("Model not built.")

        return self.model.summary()
