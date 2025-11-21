"""
Image utility functions for handling EXIF orientation and other image operations.
"""
from PIL import Image, ExifTags
import logging

logger = logging.getLogger(__name__)


def fix_image_orientation(image: Image.Image) -> Image.Image:
    """
    Apply EXIF orientation to ensure image is displayed correctly.

    Many cameras and phones store images in one orientation but include
    EXIF metadata indicating how to rotate them for display. This function
    applies that rotation so the image displays correctly.

    Args:
        image: PIL Image that may have EXIF orientation data

    Returns:
        PIL Image with orientation applied (rotated if necessary)
    """
    try:
        # Get EXIF data
        exif = image.getexif()
        if not exif:
            return image

        # Find the orientation tag
        orientation_key = None
        for key, value in ExifTags.TAGS.items():
            if value == 'Orientation':
                orientation_key = key
                break

        if orientation_key is None:
            return image

        orientation = exif.get(orientation_key)
        if orientation is None:
            return image

        logger.info(f"Image has EXIF orientation: {orientation}")

        # Apply the orientation transformation
        # Orientation values:
        # 1: Normal (no rotation)
        # 2: Mirrored horizontally
        # 3: Rotated 180°
        # 4: Mirrored vertically
        # 5: Mirrored horizontally then rotated 90° CCW
        # 6: Rotated 90° CW (270° CCW)
        # 7: Mirrored horizontally then rotated 90° CW
        # 8: Rotated 90° CCW (270° CW)

        if orientation == 2:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            image = image.rotate(180, expand=True)
        elif orientation == 4:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            image = image.rotate(90, expand=True)
        elif orientation == 6:
            image = image.rotate(270, expand=True)
        elif orientation == 7:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            image = image.rotate(270, expand=True)
        elif orientation == 8:
            image = image.rotate(90, expand=True)

        logger.info(f"Applied EXIF orientation {orientation}, new size: {image.size}")

        # Remove EXIF orientation tag after applying it
        # This prevents double-rotation if the image is opened again
        if hasattr(image, '_getexif'):
            exif_dict = dict(exif)
            if orientation_key in exif_dict:
                del exif_dict[orientation_key]

        return image

    except Exception as e:
        logger.warning(f"Error handling EXIF orientation: {e}")
        return image


def load_image_with_orientation(image_source) -> Image.Image:
    """
    Load an image and apply EXIF orientation correction.

    Args:
        image_source: File path (str) or file-like object (BytesIO)

    Returns:
        PIL Image with orientation applied
    """
    image = Image.open(image_source)
    return fix_image_orientation(image)
