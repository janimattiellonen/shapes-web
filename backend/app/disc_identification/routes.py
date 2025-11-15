"""API routes for disc identification."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image
import io
import logging

from .disc_matcher import DiscMatcher
from .config import Config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discs/identification", tags=["disc-identification"])

# Global disc matcher instance
disc_matcher: Optional[DiscMatcher] = None


def get_disc_matcher() -> DiscMatcher:
    """Get or create disc matcher instance."""
    global disc_matcher
    if disc_matcher is None:
        disc_matcher = DiscMatcher()
    return disc_matcher


class DiscRegistrationResponse(BaseModel):
    """Response for disc registration."""
    disc_id: int
    image_id: int
    model_used: str
    message: str


class DiscMatchResult(BaseModel):
    """Single match result."""
    disc_id: int
    owner_name: str
    owner_contact: str
    disc_model: Optional[str]
    disc_color: Optional[str]
    notes: Optional[str]
    status: str
    location: Optional[str]
    image_url: str
    similarity: float


class DiscSearchResponse(BaseModel):
    """Response for disc search."""
    matches: List[DiscMatchResult]
    total_matches: int
    model_used: str
    query_info: dict


class DiscInfoResponse(BaseModel):
    """Response for disc info."""
    disc_id: int
    owner_name: str
    owner_contact: str
    disc_model: Optional[str]
    disc_color: Optional[str]
    notes: Optional[str]
    status: str
    location: Optional[str]
    registered_date: str
    images: List[dict]


class StatusUpdateRequest(BaseModel):
    """Request to update disc status."""
    status: str


@router.post("/register", response_model=DiscRegistrationResponse)
async def register_disc(
    image: UploadFile = File(...),
    owner_name: str = Form(...),
    owner_contact: str = Form(...),
    disc_model: Optional[str] = Form(None),
    disc_color: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    location: Optional[str] = Form(None)
):
    """
    Register a new disc with image.

    Upload an image of your disc to register it in the system.
    This allows it to be matched if someone finds it later.

    Args:
        image: Image file of the disc
        owner_name: Name of disc owner
        owner_contact: Contact information (email/phone)
        disc_model: Optional disc model/brand
        disc_color: Optional disc color
        notes: Optional additional notes
        location: Optional location information

    Returns:
        Registration confirmation with disc ID
    """
    # Validate file type
    if image.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {image.content_type}. Only PNG, JPG, JPEG are supported."
        )

    # Read and validate file size
    contents = await image.read()
    if len(contents) > Config.get_max_image_size_bytes():
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {Config.MAX_IMAGE_SIZE_MB}MB."
        )

    try:
        # Open image
        pil_image = Image.open(io.BytesIO(contents))

        # Add to database
        matcher = get_disc_matcher()
        result = matcher.add_disc(
            image=pil_image,
            owner_name=owner_name,
            owner_contact=owner_contact,
            image_filename=image.filename or "disc.jpg",
            disc_model=disc_model,
            disc_color=disc_color,
            notes=notes,
            status='registered',
            location=location
        )

        return DiscRegistrationResponse(
            disc_id=result['disc_id'],
            image_id=result['image_id'],
            model_used=result['model_used'],
            message="Disc registered successfully"
        )

    except Exception as e:
        logger.error(f"Error registering disc: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@router.post("/search", response_model=DiscSearchResponse)
async def search_disc(
    image: UploadFile = File(...),
    top_k: Optional[int] = Form(None),
    status_filter: Optional[str] = Form(None),
    min_similarity: Optional[float] = Form(None)
):
    """
    Search for matching discs using an image.

    Upload an image of a disc to find potential matches in the database.
    Useful for finding the owner of a lost/found disc.

    Args:
        image: Image file of the disc
        top_k: Number of results to return (default: 10)
        status_filter: Filter by status ('stolen', 'registered', 'found')
        min_similarity: Minimum similarity threshold (0.0-1.0, default: 0.7)

    Returns:
        List of matching discs with similarity scores
    """
    # Validate file type
    if image.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {image.content_type}. Only PNG, JPG, JPEG are supported."
        )

    # Read and validate file size
    contents = await image.read()
    if len(contents) > Config.get_max_image_size_bytes():
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {Config.MAX_IMAGE_SIZE_MB}MB."
        )

    try:
        # Open image
        pil_image = Image.open(io.BytesIO(contents))

        # Search for matches
        matcher = get_disc_matcher()
        results = matcher.find_matches(
            query_image=pil_image,
            top_k=top_k,
            status_filter=status_filter,
            min_similarity=min_similarity
        )

        # Convert to response format
        matches = [
            DiscMatchResult(
                disc_id=r['disc_id'],
                owner_name=r['owner_name'],
                owner_contact=r['owner_contact'],
                disc_model=r['disc_model'],
                disc_color=r['disc_color'],
                notes=r['notes'],
                status=r['status'],
                location=r['location'],
                image_url=r['image_url'],
                similarity=float(r['similarity'])
            )
            for r in results
        ]

        return DiscSearchResponse(
            matches=matches,
            total_matches=len(matches),
            model_used=matcher.encoder.get_model_name(),
            query_info={
                'filename': image.filename,
                'top_k': top_k or Config.DEFAULT_TOP_K,
                'status_filter': status_filter,
                'min_similarity': min_similarity or Config.MIN_SIMILARITY_THRESHOLD
            }
        )

    except Exception as e:
        logger.error(f"Error searching discs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/{disc_id}", response_model=DiscInfoResponse)
async def get_disc_info(disc_id: int):
    """
    Get detailed information about a disc.

    Args:
        disc_id: Disc ID

    Returns:
        Disc information with all images
    """
    matcher = get_disc_matcher()
    disc_info = matcher.get_disc_info(disc_id)

    if not disc_info:
        raise HTTPException(
            status_code=404,
            detail=f"Disc with ID {disc_id} not found"
        )

    return DiscInfoResponse(
        disc_id=disc_info['id'],
        owner_name=disc_info['owner_name'],
        owner_contact=disc_info['owner_contact'],
        disc_model=disc_info['disc_model'],
        disc_color=disc_info['disc_color'],
        notes=disc_info['notes'],
        status=disc_info['status'],
        location=disc_info['location'],
        registered_date=str(disc_info['registered_date']),
        images=disc_info.get('images', [])
    )


@router.patch("/{disc_id}/status")
async def update_disc_status(disc_id: int, request: StatusUpdateRequest):
    """
    Update disc status (e.g., mark as stolen or found).

    Args:
        disc_id: Disc ID
        request: Status update request

    Returns:
        Success message
    """
    valid_statuses = ['registered', 'stolen', 'found']
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    matcher = get_disc_matcher()
    success = matcher.update_disc_status(disc_id, request.status)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Disc with ID {disc_id} not found"
        )

    return {
        "message": f"Disc status updated to '{request.status}'",
        "disc_id": disc_id,
        "status": request.status
    }


@router.post("/{disc_id}/images")
async def add_disc_image(disc_id: int, image: UploadFile = File(...)):
    """
    Add an additional image to an existing disc.

    Args:
        disc_id: Disc ID
        image: Additional image file

    Returns:
        Image ID
    """
    # Validate file type
    if image.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {image.content_type}. Only PNG, JPG, JPEG are supported."
        )

    # Read and validate file size
    contents = await image.read()
    if len(contents) > Config.get_max_image_size_bytes():
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {Config.MAX_IMAGE_SIZE_MB}MB."
        )

    try:
        # Open image
        pil_image = Image.open(io.BytesIO(contents))

        # Add image
        matcher = get_disc_matcher()
        image_id = matcher.add_additional_image(
            disc_id=disc_id,
            image=pil_image,
            image_filename=image.filename or f"disc_{disc_id}_additional.jpg"
        )

        return {
            "message": "Image added successfully",
            "disc_id": disc_id,
            "image_id": image_id
        }

    except Exception as e:
        logger.error(f"Error adding image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/health/check")
async def health_check():
    """Health check endpoint for disc identification service."""
    try:
        matcher = get_disc_matcher()
        return {
            "status": "healthy",
            "encoder": matcher.encoder.get_model_name(),
            "encoder_dim": matcher.encoder.get_embedding_dim()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
