"""
Utility for generating synthetic geometric shape images for training.
Supports ellipses, triangles, and rectangles.
"""

import numpy as np
from PIL import Image, ImageDraw
import random


class ShapeGenerator:
    """Generate synthetic images of geometric shapes."""

    def __init__(self, img_size=128):
        """
        Initialize the shape generator.

        Args:
            img_size: Size of the generated square images (default: 128x128)
        """
        self.img_size = img_size
        self.shape_names = ['ellipse', 'triangle', 'rectangle']
        self.num_classes = len(self.shape_names)

    def generate_ellipse(self, img_size=None):
        """Generate a random ellipse image (includes circles as a special case)."""
        size = img_size or self.img_size
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)

        # Random radii for ellipse (between 20% and 40% of image size)
        min_radius = max(5, int(size * 0.2))
        max_radius = max(min_radius + 1, int(size * 0.4))
        radius_x = random.randint(min_radius, max_radius)
        radius_y = random.randint(min_radius, max_radius)

        # Random center position
        margin = 5
        max_radius_overall = max(radius_x, radius_y)
        min_pos = max(max_radius_overall + margin, margin)
        max_pos = max(min_pos + 1, size - max_radius_overall - margin)
        center_x = random.randint(min_pos, max_pos)
        center_y = random.randint(min_pos, max_pos)

        # Random color
        color = self._random_color()

        # Draw ellipse
        draw.ellipse(
            [center_x - radius_x, center_y - radius_y,
             center_x + radius_x, center_y + radius_y],
            fill=color,
            outline='black',
            width=2
        )

        return np.array(img)

    # Keep backward compatibility
    def generate_circle(self, img_size=None):
        """Generate a random circle image (alias for generate_ellipse)."""
        return self.generate_ellipse(img_size)

    def generate_triangle(self, img_size=None):
        """Generate a random triangle image."""
        size = img_size or self.img_size
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)

        # Random triangle vertices
        margin = max(5, int(size * 0.15))
        max_pos = max(margin + 1, size - margin)
        points = []
        for _ in range(3):
            x = random.randint(margin, max_pos)
            y = random.randint(margin, max_pos)
            points.append((x, y))

        # Random color
        color = self._random_color()

        # Draw triangle
        draw.polygon(points, fill=color, outline='black', width=2)

        return np.array(img)

    def generate_rectangle(self, img_size=None):
        """Generate a random rectangle image."""
        size = img_size or self.img_size
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)

        # Random width and height
        min_dim = max(10, int(size * 0.3))
        max_dim = max(min_dim + 1, int(size * 0.6))
        width = random.randint(min_dim, max_dim)
        height = random.randint(min_dim, max_dim)

        # Random top-left corner
        margin = 5
        max_x = max(margin + 1, size - width - margin)
        max_y = max(margin + 1, size - height - margin)
        x1 = random.randint(margin, max_x)
        y1 = random.randint(margin, max_y)

        # Random color
        color = self._random_color()

        # Draw rectangle
        draw.rectangle(
            [x1, y1, x1 + width, y1 + height],
            fill=color,
            outline='black',
            width=2
        )

        return np.array(img)

    def _random_color(self):
        """Generate a random RGB color."""
        return (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )

    def generate_dataset(self, samples_per_class=1000, img_size=None):
        """
        Generate a dataset of shape images.

        Args:
            samples_per_class: Number of samples to generate per shape class
            img_size: Size of images to generate

        Returns:
            X: numpy array of images (N, H, W, 3)
            y: numpy array of labels (N,)
        """
        size = img_size or self.img_size
        total_samples = samples_per_class * self.num_classes

        X = np.zeros((total_samples, size, size, 3), dtype=np.float32)
        y = np.zeros(total_samples, dtype=np.int32)

        generators = [
            self.generate_ellipse,
            self.generate_triangle,
            self.generate_rectangle
        ]

        idx = 0
        for class_idx, generator in enumerate(generators):
            for _ in range(samples_per_class):
                X[idx] = generator(size)
                y[idx] = class_idx
                idx += 1

        # Normalize pixel values to [0, 1]
        X = X / 255.0

        return X, y

    def get_class_name(self, class_idx):
        """Get the name of a shape class from its index."""
        return self.shape_names[class_idx]
