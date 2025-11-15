"""Disc matching service."""
import os
from PIL import Image
from typing import List, Dict, Optional
import logging

from .encoders.base_encoder import ImageEncoder
from .encoders.encoder_factory import EncoderFactory
from .database import DatabaseService
from .config import Config

logger = logging.getLogger(__name__)


class DiscMatcher:
    """Service for matching disc images."""

    def __init__(
        self,
        encoder: Optional[ImageEncoder] = None,
        database: Optional[DatabaseService] = None
    ):
        """
        Initialize disc matcher.

        Args:
            encoder: Image encoder instance (defaults to config ENCODER_TYPE)
            database: Database service instance
        """
        self.encoder = encoder or EncoderFactory.create(Config.ENCODER_TYPE)
        self.database = database or DatabaseService()
        logger.info(f"Initialized DiscMatcher with {self.encoder.get_model_name()} encoder")

    def add_disc(
        self,
        image: Image.Image,
        owner_name: str,
        owner_contact: str,
        image_filename: str,
        disc_model: Optional[str] = None,
        disc_color: Optional[str] = None,
        notes: Optional[str] = None,
        status: str = 'registered',
        location: Optional[str] = None
    ) -> Dict:
        """
        Add a disc to the database with its image.

        Args:
            image: PIL Image object
            owner_name: Owner's name
            owner_contact: Owner's contact info
            image_filename: Original filename
            disc_model: Disc model/brand
            disc_color: Disc color
            notes: Additional notes
            status: Disc status
            location: Location info

        Returns:
            Dictionary with disc_id and image_id
        """
        # Extract embedding from image
        embedding = self.encoder.encode(image)
        model_name = self.encoder.get_model_name()

        # Create disc record
        disc_id = self.database.add_disc(
            owner_name=owner_name,
            owner_contact=owner_contact,
            disc_model=disc_model,
            disc_color=disc_color,
            notes=notes,
            status=status,
            location=location
        )

        # Save image to storage
        image_path = self._save_image(image, disc_id, image_filename)

        # Add image with embedding to database
        image_id = self.database.add_disc_image(
            disc_id=disc_id,
            image_url=image_path,
            embedding=embedding,
            model_name=model_name,
            image_path=image_path
        )

        logger.info(f"Added disc {disc_id} with image {image_id}")

        return {
            'disc_id': disc_id,
            'image_id': image_id,
            'model_used': model_name
        }

    def find_matches(
        self,
        query_image: Image.Image,
        top_k: int = None,
        status_filter: Optional[str] = None,
        min_similarity: Optional[float] = None
    ) -> List[Dict]:
        """
        Find matching discs for a query image.

        Args:
            query_image: PIL Image to search for
            top_k: Number of results to return
            status_filter: Filter by disc status (e.g., 'stolen')
            min_similarity: Minimum similarity threshold

        Returns:
            List of matching disc records with similarity scores
        """
        top_k = top_k or Config.DEFAULT_TOP_K
        min_similarity = min_similarity or Config.MIN_SIMILARITY_THRESHOLD

        # Extract embedding from query image
        query_embedding = self.encoder.encode(query_image)
        model_name = self.encoder.get_model_name()

        # Search database
        results = self.database.search_similar_discs(
            query_embedding=query_embedding,
            model_name=model_name,
            top_k=top_k,
            status_filter=status_filter
        )

        # Filter by minimum similarity
        filtered_results = [
            result for result in results
            if result['similarity'] >= min_similarity
        ]

        logger.info(
            f"Found {len(filtered_results)} matches above {min_similarity} threshold "
            f"(out of {len(results)} total)"
        )

        return filtered_results

    def add_additional_image(
        self,
        disc_id: int,
        image: Image.Image,
        image_filename: str
    ) -> int:
        """
        Add an additional image to an existing disc.

        Args:
            disc_id: Existing disc ID
            image: PIL Image object
            image_filename: Original filename

        Returns:
            Image ID
        """
        # Extract embedding
        embedding = self.encoder.encode(image)
        model_name = self.encoder.get_model_name()

        # Save image
        image_path = self._save_image(image, disc_id, image_filename)

        # Add to database
        image_id = self.database.add_disc_image(
            disc_id=disc_id,
            image_url=image_path,
            embedding=embedding,
            model_name=model_name,
            image_path=image_path
        )

        logger.info(f"Added additional image {image_id} to disc {disc_id}")
        return image_id

    def update_disc_status(
        self,
        disc_id: int,
        status: str
    ) -> bool:
        """
        Update disc status (e.g., mark as stolen).

        Args:
            disc_id: Disc ID
            status: New status

        Returns:
            True if successful
        """
        from datetime import datetime

        stolen_date = datetime.now() if status == 'stolen' else None
        found_date = datetime.now() if status == 'found' else None

        success = self.database.update_disc_status(
            disc_id=disc_id,
            status=status,
            stolen_date=stolen_date,
            found_date=found_date
        )

        if success:
            logger.info(f"Updated disc {disc_id} status to '{status}'")
        else:
            logger.warning(f"Failed to update disc {disc_id} status")

        return success

    def _save_image(self, image: Image.Image, disc_id: int, filename: str) -> str:
        """
        Save image to disk.

        Args:
            image: PIL Image
            disc_id: Disc ID
            filename: Original filename

        Returns:
            Path to saved image
        """
        # Create upload directory if it doesn't exist
        upload_dir = Config.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)

        # Create disc-specific directory
        disc_dir = os.path.join(upload_dir, str(disc_id))
        os.makedirs(disc_dir, exist_ok=True)

        # Save image
        image_path = os.path.join(disc_dir, filename)
        image.save(image_path, quality=95)

        logger.info(f"Saved image to {image_path}")
        return image_path

    def get_disc_info(self, disc_id: int) -> Optional[Dict]:
        """
        Get detailed disc information.

        Args:
            disc_id: Disc ID

        Returns:
            Disc information with images
        """
        disc = self.database.get_disc_by_id(disc_id)
        if not disc:
            return None

        images = self.database.get_disc_images(disc_id)
        disc['images'] = images

        return disc
