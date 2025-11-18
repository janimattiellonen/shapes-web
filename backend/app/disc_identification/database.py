"""Database operations for disc identification."""
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from .config import Config

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations."""

    def __init__(self, database_url: str = None):
        """
        Initialize database service.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or Config.DATABASE_URL
        self._connection = None

    def get_connection(self):
        """Get database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(self.database_url)
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()

    def add_disc(
        self,
        owner_name: str,
        owner_contact: str,
        disc_model: Optional[str] = None,
        disc_color: Optional[str] = None,
        notes: Optional[str] = None,
        status: str = 'registered',
        location: Optional[str] = None,
        upload_status: str = 'PENDING'
    ) -> int:
        """
        Add a new disc to the database.

        Args:
            owner_name: Name of disc owner
            owner_contact: Contact information
            disc_model: Model/brand of disc
            disc_color: Color of disc
            notes: Additional notes
            status: Status ('registered', 'stolen', 'found')
            location: Location information
            upload_status: Upload workflow status ('PENDING', 'SUCCESS')

        Returns:
            ID of created disc record
        """
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO discs (owner_name, owner_contact, disc_model, disc_color, notes, status, location, upload_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (owner_name, owner_contact, disc_model, disc_color, notes, status, location, upload_status)
            )
            disc_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Created disc record with ID: {disc_id}")
            return disc_id

    def add_disc_image(
        self,
        disc_id: int,
        image_url: str,
        model_name: str,
        image_path: Optional[str] = None,
        original_embedding: Optional[np.ndarray] = None,
        cropped_embedding: Optional[np.ndarray] = None,
        border_info: Optional[Dict] = None,
        cropped_image_path: Optional[str] = None,
        preprocessing_metadata: Optional[Dict] = None
    ) -> int:
        """
        Add a disc image with embeddings to the database.

        Args:
            disc_id: ID of the disc
            image_url: URL/path to original image
            model_name: Name of encoder model used
            image_path: Optional local file path for original image
            original_embedding: Embedding from original full image
            cropped_embedding: Embedding from cropped disc region
            border_info: Border detection metadata (JSONB)
            cropped_image_path: Path to cropped image file
            preprocessing_metadata: Additional preprocessing info (JSONB)

        Returns:
            ID of created disc_image record
        """
        conn = self.get_connection()
        with conn.cursor() as cur:
            # Convert numpy arrays to lists for PostgreSQL
            original_emb_list = original_embedding.tolist() if original_embedding is not None else None
            cropped_emb_list = cropped_embedding.tolist() if cropped_embedding is not None else None

            cur.execute(
                """
                INSERT INTO disc_images (
                    disc_id, image_url, image_path, model_name,
                    original_embedding, cropped_embedding,
                    border_info, cropped_image_path, preprocessing_metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    disc_id, image_url, image_path, model_name,
                    original_emb_list, cropped_emb_list,
                    border_info, cropped_image_path, preprocessing_metadata
                )
            )
            image_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Created disc_image record with ID: {image_id}")
            return image_id

    def search_similar_discs(
        self,
        model_name: str,
        top_k: int = 10,
        status_filter: Optional[str] = None,
        query_original_embedding: Optional[np.ndarray] = None,
        query_cropped_embedding: Optional[np.ndarray] = None,
        prefer_cropped: bool = True
    ) -> List[Dict]:
        """
        Search for similar discs using vector similarity.

        Supports searching with both original and cropped embeddings.
        When prefer_cropped=True, prioritizes cropped-to-cropped comparison.

        Args:
            model_name: Name of encoder model used
            top_k: Number of results to return
            status_filter: Optional filter by disc status
            query_original_embedding: Query embedding from original image
            query_cropped_embedding: Query embedding from cropped image
            prefer_cropped: Whether to prefer cropped embeddings when available

        Returns:
            List of matching disc records with similarity scores
        """
        conn = self.get_connection()

        # Determine which embedding to use for search
        if prefer_cropped and query_cropped_embedding is not None:
            # Use cropped embedding, fallback to original for images without crops
            query_embedding = query_cropped_embedding
            embedding_column = "COALESCE(di.cropped_embedding, di.original_embedding)"
            match_type_expr = "CASE WHEN di.cropped_embedding IS NOT NULL THEN 'cropped' ELSE 'original' END"
        elif query_original_embedding is not None:
            # Use original embedding
            query_embedding = query_original_embedding
            embedding_column = "di.original_embedding"
            match_type_expr = "'original'"
        else:
            raise ValueError("At least one of query_original_embedding or query_cropped_embedding must be provided")

        # Convert numpy array to list for PostgreSQL
        embedding_list = query_embedding.tolist()

        # Build query
        query = f"""
            SELECT
                d.id as disc_id,
                d.owner_name,
                d.owner_contact,
                d.disc_model,
                d.disc_color,
                d.notes,
                d.status,
                d.location,
                d.registered_date,
                d.stolen_date,
                di.id as image_id,
                di.image_url,
                di.image_path,
                di.cropped_image_path,
                di.border_info,
                1 - ({embedding_column} <=> %s::vector) as similarity,
                {match_type_expr} as match_type
            FROM disc_images di
            JOIN discs d ON di.disc_id = d.id
            WHERE di.model_name = %s
              AND {embedding_column} IS NOT NULL
        """

        params = [embedding_list, model_name]

        if status_filter:
            query += " AND d.status = %s"
            params.append(status_filter)

        query += f"""
            ORDER BY {embedding_column} <=> %s::vector
            LIMIT %s
        """
        params.extend([embedding_list, top_k])

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()

        # Convert to list of dicts
        return [dict(row) for row in results]

    def get_disc_by_id(self, disc_id: int) -> Optional[Dict]:
        """
        Get disc information by ID.

        Args:
            disc_id: Disc ID

        Returns:
            Disc information or None
        """
        conn = self.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM discs WHERE id = %s
                """,
                (disc_id,)
            )
            result = cur.fetchone()
            return dict(result) if result else None

    def update_disc_status(
        self,
        disc_id: int,
        status: str,
        stolen_date: Optional[datetime] = None,
        found_date: Optional[datetime] = None
    ) -> bool:
        """
        Update disc status.

        Args:
            disc_id: Disc ID
            status: New status
            stolen_date: Optional stolen date
            found_date: Optional found date

        Returns:
            True if updated, False otherwise
        """
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE discs
                SET status = %s, stolen_date = %s, found_date = %s
                WHERE id = %s
                """,
                (status, stolen_date, found_date, disc_id)
            )
            conn.commit()
            return cur.rowcount > 0

    def get_disc_images(self, disc_id: int) -> List[Dict]:
        """
        Get all images for a disc.

        Args:
            disc_id: Disc ID

        Returns:
            List of image records with border detection and embedding info
        """
        conn = self.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id, disc_id, image_url, image_path, cropped_image_path,
                    model_name, border_info, preprocessing_metadata, created_at
                FROM disc_images
                WHERE disc_id = %s
                ORDER BY created_at DESC
                """,
                (disc_id,)
            )
            results = cur.fetchall()
            return [dict(row) for row in results]

    def confirm_disc_upload(self, disc_id: int) -> bool:
        """
        Confirm disc upload by updating upload_status to SUCCESS.

        Args:
            disc_id: Disc ID

        Returns:
            True if updated, False otherwise
        """
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE discs
                SET upload_status = 'SUCCESS'
                WHERE id = %s AND upload_status = 'PENDING'
                """,
                (disc_id,)
            )
            conn.commit()
            updated = cur.rowcount > 0
            if updated:
                logger.info(f"Confirmed disc upload for ID: {disc_id}")
            return updated

    def delete_disc(self, disc_id: int) -> bool:
        """
        Delete a disc and all associated images.

        Args:
            disc_id: Disc ID

        Returns:
            True if deleted, False otherwise
        """
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM discs
                WHERE id = %s
                """,
                (disc_id,)
            )
            conn.commit()
            deleted = cur.rowcount > 0
            if deleted:
                logger.info(f"Deleted disc with ID: {disc_id}")
            return deleted
