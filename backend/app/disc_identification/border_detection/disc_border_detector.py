"""
Disc border detection using OpenCV.
Detects circular/elliptical disc borders in images.
"""
import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class DiscBorderDetector:
    """Detects disc golf disc borders in images using circle/ellipse detection."""

    def __init__(
        self,
        min_radius_ratio: float = 0.2,
        max_radius_ratio: float = 0.9,
        edge_threshold1: int = 50,
        edge_threshold2: int = 150,
        circle_threshold: int = 30
    ):
        """
        Initialize disc border detector.

        Args:
            min_radius_ratio: Minimum radius as ratio of image size (0.0-1.0)
            max_radius_ratio: Maximum radius as ratio of image size (0.0-1.0)
            edge_threshold1: First threshold for Canny edge detection
            edge_threshold2: Second threshold for Canny edge detection
            circle_threshold: Accumulator threshold for circle detection
        """
        self.min_radius_ratio = min_radius_ratio
        self.max_radius_ratio = max_radius_ratio
        self.edge_threshold1 = edge_threshold1
        self.edge_threshold2 = edge_threshold2
        self.circle_threshold = circle_threshold

    def detect_border(self, image: Image.Image) -> Optional[Dict]:
        """
        Detect the disc border in an image.

        Args:
            image: PIL Image object

        Returns:
            Dictionary with border information or None if no border found:
            {
                'type': 'circle' or 'ellipse',
                'center': {'x': int, 'y': int},
                'radius': int (for circle),
                'axes': {'major': int, 'minor': int} (for ellipse),
                'angle': float (for ellipse, rotation in degrees),
                'confidence': float (0.0-1.0)
            }
        """
        # Convert PIL to OpenCV
        cv_image = np.array(image.convert('RGB'))
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

        # Try circle detection first
        circle_result = self._detect_circle(cv_image)

        if circle_result:
            return circle_result

        # If circle detection fails, try ellipse detection
        ellipse_result = self._detect_ellipse(cv_image)

        return ellipse_result

    def _detect_circle(self, image: np.ndarray) -> Optional[Dict]:
        """
        Detect circular disc border using Hough Circle Transform.

        Args:
            image: OpenCV BGR image

        Returns:
            Circle detection result or None
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Calculate radius constraints based on image size
        height, width = gray.shape
        min_dim = min(height, width)
        min_radius = int(min_dim * self.min_radius_ratio)
        max_radius = int(min_dim * self.max_radius_ratio)

        # Detect circles using Hough Circle Transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min_radius,
            param1=self.edge_threshold2,
            param2=self.circle_threshold,
            minRadius=min_radius,
            maxRadius=max_radius
        )

        if circles is None or len(circles[0]) == 0:
            logger.info("No circles detected")
            return None

        # Get the largest circle closest to the image center
        circles = np.round(circles[0, :]).astype("int")
        best_circle = self._select_best_circle(circles, width, height)

        if best_circle is None:
            return None

        x, y, r = best_circle

        # Calculate confidence based on how close to image center
        center_x, center_y = width / 2, height / 2
        distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_distance = np.sqrt(center_x**2 + center_y**2)
        confidence = 1.0 - (distance_from_center / max_distance)

        logger.info(f"Circle detected: center=({x}, {y}), radius={r}, confidence={confidence:.2f}")

        return {
            'type': 'circle',
            'center': {'x': int(x), 'y': int(y)},
            'radius': int(r),
            'confidence': float(confidence)
        }

    def _detect_ellipse(self, image: np.ndarray) -> Optional[Dict]:
        """
        Detect elliptical disc border using contour fitting.

        Args:
            image: OpenCV BGR image

        Returns:
            Ellipse detection result or None
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection
        edges = cv2.Canny(blurred, self.edge_threshold1, self.edge_threshold2)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            logger.info("No contours found for ellipse detection")
            return None

        height, width = gray.shape
        min_dim = min(height, width)
        min_area = (min_dim * self.min_radius_ratio) ** 2 * np.pi

        # Find the largest ellipse-shaped contour
        best_ellipse = None
        best_score = 0

        for contour in contours:
            # Need at least 5 points to fit an ellipse
            if len(contour) < 5:
                continue

            area = cv2.contourArea(contour)

            # Filter by area
            if area < min_area:
                continue

            try:
                # Fit ellipse
                ellipse = cv2.fitEllipse(contour)
                (x, y), (major, minor), angle = ellipse

                # Check if it's reasonably circular (not too elongated)
                aspect_ratio = min(major, minor) / max(major, minor)
                if aspect_ratio < 0.7:  # Too elongated
                    continue

                # Score based on size and position
                center_x, center_y = width / 2, height / 2
                distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                max_distance = np.sqrt(center_x**2 + center_y**2)
                position_score = 1.0 - (distance_from_center / max_distance)

                # Combine size and position for total score
                size_score = area / (width * height)
                total_score = (position_score * 0.6) + (size_score * 0.4)

                if total_score > best_score:
                    best_score = total_score
                    best_ellipse = ellipse

            except cv2.error:
                continue

        if best_ellipse is None:
            logger.info("No suitable ellipse found")
            return None

        (x, y), (major, minor), angle = best_ellipse

        logger.info(f"Ellipse detected: center=({x:.0f}, {y:.0f}), axes=({major:.0f}, {minor:.0f}), angle={angle:.1f}°, confidence={best_score:.2f}")

        return {
            'type': 'ellipse',
            'center': {'x': int(x), 'y': int(y)},
            'axes': {'major': int(major / 2), 'minor': int(minor / 2)},
            'angle': float(angle),
            'confidence': float(best_score)
        }

    def _select_best_circle(
        self,
        circles: np.ndarray,
        img_width: int,
        img_height: int
    ) -> Optional[Tuple[int, int, int]]:
        """
        Select the best circle from detected circles.
        Prefers larger circles closer to the image center.

        Args:
            circles: Array of detected circles [(x, y, r), ...]
            img_width: Image width
            img_height: Image height

        Returns:
            Best circle (x, y, r) or None
        """
        if len(circles) == 0:
            return None

        center_x, center_y = img_width / 2, img_height / 2
        best_circle = None
        best_score = -1

        for circle in circles:
            x, y, r = circle

            # Calculate distance from image center
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_distance = np.sqrt(center_x**2 + center_y**2)

            # Score based on radius (larger is better) and distance from center (closer is better)
            radius_score = r / max(img_width, img_height)
            distance_score = 1.0 - (distance / max_distance)

            # Combined score (60% position, 40% size)
            total_score = (distance_score * 0.6) + (radius_score * 0.4)

            if total_score > best_score:
                best_score = total_score
                best_circle = circle

        return tuple(best_circle) if best_circle is not None else None

    def crop_to_border(
        self,
        image: Image.Image,
        border_info: Dict,
        padding: int = 0
    ) -> Image.Image:
        """
        Crop image to the detected border with optional padding.

        Args:
            image: Original PIL Image
            border_info: Border detection result
            padding: Additional padding around border (pixels)

        Returns:
            Cropped PIL Image
        """
        cv_image = np.array(image.convert('RGB'))
        height, width = cv_image.shape[:2]

        center_x = border_info['center']['x']
        center_y = border_info['center']['y']

        if border_info['type'] == 'circle':
            radius = border_info['radius']
            x1 = max(0, center_x - radius - padding)
            y1 = max(0, center_y - radius - padding)
            x2 = min(width, center_x + radius + padding)
            y2 = min(height, center_y + radius + padding)
        else:  # ellipse
            major = border_info['axes']['major']
            minor = border_info['axes']['minor']
            max_axis = max(major, minor)
            x1 = max(0, center_x - max_axis - padding)
            y1 = max(0, center_y - max_axis - padding)
            x2 = min(width, center_x + max_axis + padding)
            y2 = min(height, center_y + max_axis + padding)

        cropped = image.crop((int(x1), int(y1), int(x2), int(y2)))
        return cropped
