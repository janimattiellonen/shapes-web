"""
Border Processing Module

Handles image processing operations related to disc border detection,
including cropping, masking, and image transformations.
"""
from PIL import Image, ImageDraw
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BorderProcessor:
    """Processes images based on detected border information."""

    @staticmethod
    def create_cropped_image(
        image: Image.Image,
        border_info: Dict,
        padding: int = 0
    ) -> Image.Image:
        """
        Create a cropped version of the image based on border detection.

        Args:
            image: PIL Image to crop
            border_info: Border detection results with type, center, radius/axes
            padding: Optional padding around the detected border (pixels)

        Returns:
            Cropped PIL Image

        Raises:
            ValueError: If border_info is invalid
        """
        if not border_info or 'type' not in border_info:
            raise ValueError("Invalid border_info: must contain 'type' field")

        border_type = border_info['type']

        if border_type == 'circle':
            return BorderProcessor._crop_circle(image, border_info, padding)
        elif border_type == 'ellipse':
            return BorderProcessor._crop_ellipse(image, border_info, padding)
        else:
            raise ValueError(f"Unsupported border type: {border_type}")

    @staticmethod
    def _crop_circle(
        image: Image.Image,
        border_info: Dict,
        padding: int = 0
    ) -> Image.Image:
        """
        Crop image to circular border.

        Args:
            image: PIL Image
            border_info: Contains center (x, y) and radius
            padding: Padding in pixels

        Returns:
            Cropped square image containing the circle
        """
        center = border_info['center']
        radius = border_info['radius']

        # Calculate bounding box with padding
        x = center['x']
        y = center['y']
        r = radius + padding

        # Calculate crop box (ensure within image bounds)
        left = max(0, int(x - r))
        top = max(0, int(y - r))
        right = min(image.width, int(x + r))
        bottom = min(image.height, int(y + r))

        # Crop to bounding box
        cropped = image.crop((left, top, right, bottom))

        logger.debug(f"Cropped circle: center=({x}, {y}), radius={radius}, "
                    f"box=({left}, {top}, {right}, {bottom})")

        return cropped

    @staticmethod
    def _crop_ellipse(
        image: Image.Image,
        border_info: Dict,
        padding: int = 0
    ) -> Image.Image:
        """
        Crop image to elliptical border.

        Args:
            image: PIL Image
            border_info: Contains center (x, y), major_axis, minor_axis, angle
            padding: Padding in pixels

        Returns:
            Cropped rectangular image containing the ellipse
        """
        center = border_info['center']
        major_axis = border_info['major_axis']
        minor_axis = border_info['minor_axis']

        # Use the major axis as the bounding dimension
        radius = max(major_axis, minor_axis) / 2 + padding

        x = center['x']
        y = center['y']

        # Calculate crop box (ensure within image bounds)
        left = max(0, int(x - radius))
        top = max(0, int(y - radius))
        right = min(image.width, int(x + radius))
        bottom = min(image.height, int(y + radius))

        # Crop to bounding box
        cropped = image.crop((left, top, right, bottom))

        logger.debug(f"Cropped ellipse: center=({x}, {y}), axes=({major_axis}, {minor_axis}), "
                    f"box=({left}, {top}, {right}, {bottom})")

        return cropped

    @staticmethod
    def create_circular_mask(
        image_size: Tuple[int, int],
        border_info: Dict
    ) -> Image.Image:
        """
        Create a binary mask for the detected disc region.

        Useful for future implementations that need masking instead of cropping.

        Args:
            image_size: (width, height) of the target image
            border_info: Border detection results

        Returns:
            Binary mask image (L mode) - white for disc, black for background
        """
        if not border_info or 'type' not in border_info:
            raise ValueError("Invalid border_info: must contain 'type' field")

        mask = Image.new('L', image_size, 0)  # Black background
        draw = ImageDraw.Draw(mask)

        border_type = border_info['type']

        if border_type == 'circle':
            center = border_info['center']
            radius = border_info['radius']
            bbox = [
                center['x'] - radius,
                center['y'] - radius,
                center['x'] + radius,
                center['y'] + radius
            ]
            draw.ellipse(bbox, fill=255)

        elif border_type == 'ellipse':
            center = border_info['center']
            major_axis = border_info['major_axis']
            minor_axis = border_info['minor_axis']
            angle = border_info.get('angle', 0)

            # For simplicity, create axis-aligned ellipse
            # TODO: Handle rotation if needed in future
            bbox = [
                center['x'] - major_axis / 2,
                center['y'] - minor_axis / 2,
                center['x'] + major_axis / 2,
                center['y'] + minor_axis / 2
            ]
            draw.ellipse(bbox, fill=255)

        logger.debug(f"Created {border_type} mask for image size {image_size}")

        return mask

    @staticmethod
    def apply_mask_to_image(
        image: Image.Image,
        mask: Image.Image,
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Image.Image:
        """
        Apply a mask to an image, replacing background with solid color.

        Args:
            image: Source PIL Image (RGB)
            mask: Binary mask (L mode)
            background_color: RGB tuple for background (default: white)

        Returns:
            Masked image with background replaced
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')

        if mask.size != image.size:
            raise ValueError(f"Mask size {mask.size} doesn't match image size {image.size}")

        # Create solid background
        background = Image.new('RGB', image.size, background_color)

        # Composite: disc pixels from image, background elsewhere
        result = Image.composite(image, background, mask)

        logger.debug(f"Applied mask to image, background color: {background_color}")

        return result

    @staticmethod
    def calculate_crop_dimensions(border_info: Dict) -> Tuple[int, int]:
        """
        Calculate the dimensions of the cropped image.

        Args:
            border_info: Border detection results

        Returns:
            Tuple of (width, height) for the crop
        """
        border_type = border_info['type']

        if border_type == 'circle':
            radius = border_info['radius']
            size = int(radius * 2)
            return (size, size)

        elif border_type == 'ellipse':
            major_axis = border_info['major_axis']
            minor_axis = border_info['minor_axis']
            # Use major axis for square crop
            size = int(max(major_axis, minor_axis))
            return (size, size)

        return (0, 0)
