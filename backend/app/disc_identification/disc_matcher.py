"""Disc matching service."""
import os
from PIL import Image
from typing import List, Dict, Optional
import logging

from .encoders.base_encoder import ImageEncoder
from .encoders.encoder_factory import EncoderFactory
from .database import DatabaseService
from .config import Config
from .border_detection.border_service import BorderService

logger = logging.getLogger(__name__)


class DiscMatcher:
    """Service for matching disc images."""

    def __init__(
        self,
        encoder: Optional[ImageEncoder] = None,
        database: Optional[DatabaseService] = None,
        border_service: Optional[BorderService] = None
    ):
        """
        Initialize disc matcher.

        Args:
            encoder: Image encoder instance (defaults to config ENCODER_TYPE)
            database: Database service instance
            border_service: Border detection service instance
        """
        self.encoder = encoder or EncoderFactory.create(Config.ENCODER_TYPE)
        self.database = database or DatabaseService()
        self.border_service = border_service or BorderService()
        logger.info(f"Initialized DiscMatcher with {self.encoder.get_model_name()} encoder")

    @property
    def db(self) -> DatabaseService:
        """Alias for database service (for backward compatibility)."""
        return self.database

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
        location: Optional[str] = None,
        upload_status: str = 'SUCCESS'
    ) -> Dict:
        """
        Add a disc to the database with its image.

        Performs automatic border detection and creates both original and
        cropped embeddings when border detection is enabled.

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
            Dictionary with disc_id, image_id, and border detection info
        """
        model_name = self.encoder.get_model_name()

        # Create disc record first (need disc_id for saving images)
        disc_id = self.database.add_disc(
            owner_name=owner_name,
            owner_contact=owner_contact,
            disc_model=disc_model,
            disc_color=disc_color,
            notes=notes,
            status=status,
            location=location,
            upload_status=upload_status
        )

        # Save original image to storage
        image_path = self._save_image(image, disc_id, image_filename)

        # Initialize embedding variables
        original_embedding = None
        cropped_embedding = None
        border_info = None
        cropped_image_path = None
        preprocessing_metadata = None

        # Step 1: Always encode original image
        if Config.ENCODE_BOTH_VERSIONS or not Config.BORDER_DETECTION_ENABLED:
            logger.info(f"Encoding original image for disc {disc_id}")
            original_embedding = self.encoder.encode(image)

        # Step 2: Border detection and cropped encoding (if enabled)
        if Config.BORDER_DETECTION_ENABLED:
            logger.info(f"Running border detection for disc {disc_id}")
            border_result = self.border_service.detect_and_process(
                image=image,
                disc_id=disc_id,
                save_cropped=Config.STORE_CROPPED_IMAGES
            )

            if border_result.detected:
                border_info = border_result.border_info
                cropped_image_path = border_result.cropped_image_path
                preprocessing_metadata = border_result.preprocessing_metadata

                # Encode cropped image if available and quality is good
                if self.border_service.should_use_cropped(border_result):
                    logger.info(
                        f"Encoding cropped image for disc {disc_id} "
                        f"(confidence: {border_result.confidence:.2f})"
                    )
                    cropped_embedding = self.encoder.encode(border_result.cropped_image)

                    # If we only want cropped embeddings, don't store original
                    if not Config.ENCODE_BOTH_VERSIONS:
                        original_embedding = None
                else:
                    logger.warning(
                        f"Border detection quality insufficient for disc {disc_id} "
                        f"(confidence: {border_result.confidence:.2f})"
                    )
            else:
                logger.info(f"No border detected for disc {disc_id}, using original only")

        # Step 3: Add image with embeddings to database
        # Construct API URL from filesystem path
        image_filename = os.path.basename(image_path)
        image_url = f"/discs/identification/{disc_id}/images/{image_filename}"

        image_id = self.database.add_disc_image(
            disc_id=disc_id,
            image_url=image_url,
            model_name=model_name,
            image_path=image_path,
            original_embedding=original_embedding,
            cropped_embedding=cropped_embedding,
            border_info=border_info,
            cropped_image_path=cropped_image_path,
            preprocessing_metadata=preprocessing_metadata
        )

        logger.info(
            f"Added disc {disc_id} with image {image_id} "
            f"(original_emb: {original_embedding is not None}, "
            f"cropped_emb: {cropped_embedding is not None})"
        )

        return {
            'disc_id': disc_id,
            'image_id': image_id,
            'model_used': model_name,
            'border_detected': border_info is not None,
            'border_confidence': border_info.get('confidence', 0) if border_info else 0
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

        Performs border detection on the query image and uses cropped embeddings
        when available for improved matching accuracy.

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
        model_name = self.encoder.get_model_name()

        # Initialize embeddings
        query_original_embedding = None
        query_cropped_embedding = None

        # Step 1: Encode original query image (always, for fallback)
        logger.info("Encoding original query image")
        query_original_embedding = self.encoder.encode(query_image)

        # Step 2: Border detection and cropped encoding (if enabled)
        if Config.BORDER_DETECTION_ENABLED:
            logger.info("Running border detection on query image")
            border_result = self.border_service.detect_and_process(
                image=query_image,
                disc_id=None,  # No disc_id for query images
                save_cropped=False  # Don't save query images
            )

            if border_result.detected and self.border_service.should_use_cropped(border_result):
                logger.info(
                    f"Encoding cropped query image (confidence: {border_result.confidence:.2f})"
                )
                query_cropped_embedding = self.encoder.encode(border_result.cropped_image)
            else:
                logger.info("Query border detection insufficient, using original only")

        # Step 3: Search database with appropriate embeddings
        results = self.database.search_similar_discs(
            model_name=model_name,
            top_k=top_k,
            status_filter=status_filter,
            query_original_embedding=query_original_embedding,
            query_cropped_embedding=query_cropped_embedding,
            prefer_cropped=Config.PREFER_CROPPED_MATCHING
        )

        # Filter by minimum similarity
        filtered_results = [
            result for result in results
            if result['similarity'] >= min_similarity
        ]

        logger.info(
            f"Found {len(filtered_results)} matches above {min_similarity} threshold "
            f"(out of {len(results)} total), "
            f"using {'cropped' if query_cropped_embedding is not None else 'original'} query embedding"
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

        Performs automatic border detection and creates both original and
        cropped embeddings when border detection is enabled.

        Args:
            disc_id: Existing disc ID
            image: PIL Image object
            image_filename: Original filename

        Returns:
            Image ID
        """
        model_name = self.encoder.get_model_name()

        # Save original image
        image_path = self._save_image(image, disc_id, image_filename)

        # Initialize embedding variables
        original_embedding = None
        cropped_embedding = None
        border_info = None
        cropped_image_path = None
        preprocessing_metadata = None

        # Step 1: Always encode original image
        if Config.ENCODE_BOTH_VERSIONS or not Config.BORDER_DETECTION_ENABLED:
            logger.info(f"Encoding original image for disc {disc_id}")
            original_embedding = self.encoder.encode(image)

        # Step 2: Border detection and cropped encoding (if enabled)
        if Config.BORDER_DETECTION_ENABLED:
            logger.info(f"Running border detection for additional image on disc {disc_id}")
            border_result = self.border_service.detect_and_process(
                image=image,
                disc_id=disc_id,
                save_cropped=Config.STORE_CROPPED_IMAGES
            )

            if border_result.detected:
                border_info = border_result.border_info
                cropped_image_path = border_result.cropped_image_path
                preprocessing_metadata = border_result.preprocessing_metadata

                if self.border_service.should_use_cropped(border_result):
                    logger.info(f"Encoding cropped image (confidence: {border_result.confidence:.2f})")
                    cropped_embedding = self.encoder.encode(border_result.cropped_image)

                    if not Config.ENCODE_BOTH_VERSIONS:
                        original_embedding = None

        # Add to database with embeddings
        # Construct API URL from filesystem path
        image_filename = os.path.basename(image_path)
        image_url = f"/discs/identification/{disc_id}/images/{image_filename}"

        image_id = self.database.add_disc_image(
            disc_id=disc_id,
            image_url=image_url,
            model_name=model_name,
            image_path=image_path,
            original_embedding=original_embedding,
            cropped_embedding=cropped_embedding,
            border_info=border_info,
            cropped_image_path=cropped_image_path,
            preprocessing_metadata=preprocessing_metadata
        )

        logger.info(
            f"Added additional image {image_id} to disc {disc_id} "
            f"(original_emb: {original_embedding is not None}, "
            f"cropped_emb: {cropped_embedding is not None})"
        )
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
