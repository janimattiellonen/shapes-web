"""API routes for disc identification."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from PIL import Image
import io
import logging
import os
from pathlib import Path

from .disc_matcher import DiscMatcher
from .config import Config
from .border_detection.disc_border_detector import DiscBorderDetector
from .utils.image_utils import load_image_with_orientation
from .disc_registration_service import DiscRegistrationService
from .ocr.ocr_service import OCRService
import shutil

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
    image_path: Optional[str]
    cropped_image_path: Optional[str]
    border_info: Optional[Dict]
    match_type: Optional[str]
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

    # Use registration service
    matcher = get_disc_matcher()
    service = DiscRegistrationService(disc_matcher=matcher)

    result = service.register_from_bytes(
        image_bytes=contents,
        filename=image.filename or "disc.jpg",
        owner_name=owner_name,
        owner_contact=owner_contact,
        disc_model=disc_model,
        disc_color=disc_color,
        notes=notes,
        location=location,
        status='registered',
        upload_status='SUCCESS'
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error_message or "Error processing image"
        )

    return DiscRegistrationResponse(
        disc_id=result.disc_id,
        image_id=result.image_id,
        model_used=result.model_used,
        message="Disc registered successfully"
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
        pil_image = load_image_with_orientation(io.BytesIO(contents))

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
                image_path=r.get('image_path'),
                cropped_image_path=r.get('cropped_image_path'),
                border_info=r.get('border_info'),
                match_type=r.get('match_type'),
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
        pil_image = load_image_with_orientation(io.BytesIO(contents))

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


@router.get("/{disc_id}/images/{image_filename}")
async def get_disc_image(disc_id: int, image_filename: str):
    """
    Serve a disc image file.

    Returns the actual image file for a given disc. Validates that the image
    belongs to the specified disc before serving.

    Args:
        disc_id: ID of the disc
        image_filename: Name of the image file to retrieve

    Returns:
        FileResponse with the image file

    Raises:
        404: If disc or image not found
        403: If image doesn't belong to the specified disc
    """
    try:
        matcher = get_disc_matcher()

        # Get all images for this disc to validate the image belongs to it
        disc_images = matcher.db.get_disc_images(disc_id)

        if not disc_images:
            raise HTTPException(
                status_code=404,
                detail=f"No images found for disc ID {disc_id}"
            )

        # Construct the full image path
        image_path = os.path.join(Config.UPLOAD_DIR, str(disc_id), image_filename)

        # Validate that this image belongs to the disc
        # Check if any of the disc's images match this path
        valid_image = False
        for img in disc_images:
            # Check both image_path (if stored) and construct path from image_url
            if img.get('image_path') == image_path or \
               img.get('image_path', '').endswith(f"/{disc_id}/{image_filename}") or \
               img.get('cropped_image_path', '').endswith(f"/{disc_id}/{image_filename}"):
                valid_image = True
                break

        if not valid_image:
            raise HTTPException(
                status_code=403,
                detail=f"Image '{image_filename}' does not belong to disc ID {disc_id}"
            )

        # Check if file exists on disk
        if not os.path.exists(image_path):
            logger.error(f"Image file not found on disk: {image_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found: {image_filename}"
            )

        # Determine media type from file extension
        file_ext = Path(image_filename).suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        media_type = media_type_map.get(file_ext, 'application/octet-stream')

        logger.info(f"Serving image: {image_path}")
        return FileResponse(
            path=image_path,
            media_type=media_type,
            filename=image_filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )


# Border Detection Endpoint (separate router for cleaner organization)
border_router = APIRouter(prefix="/discs/border-detection", tags=["border-detection"])


class BorderDetectionResponse(BaseModel):
    """Response for border detection."""
    detected: bool
    border: Optional[Dict] = None
    message: str


@border_router.post("", response_model=BorderDetectionResponse)
async def detect_border(image: UploadFile = File(...)):
    """
    Detect disc border in an image.

    Identifies the circular or elliptical border of a disc golf disc.
    Returns coordinates that can be used to crop or highlight the disc.

    Args:
        image: Uploaded image file (PNG, JPG, JPEG)

    Returns:
        BorderDetectionResponse with border coordinates:
        - For circles: center (x, y), radius
        - For ellipses: center (x, y), major/minor axes, rotation angle
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
        pil_image = load_image_with_orientation(io.BytesIO(contents))

        # Detect border
        detector = DiscBorderDetector()
        border_info = detector.detect_border(pil_image)

        if border_info is None:
            return BorderDetectionResponse(
                detected=False,
                border=None,
                message="No disc border detected. Try with a clearer image."
            )

        logger.info(f"Border detected: {border_info['type']} with confidence {border_info.get('confidence', 0):.2f}")

        return BorderDetectionResponse(
            detected=True,
            border=border_info,
            message=f"Detected {border_info['type']} border successfully"
        )

    except Exception as e:
        logger.error(f"Error detecting border: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


# New Disc Upload Workflow Endpoints
upload_router = APIRouter(prefix="/discs", tags=["disc-upload"])


class DiscUploadResponse(BaseModel):
    """Response for disc upload."""
    disc_id: int
    border_detected: bool
    border: Optional[Dict] = None
    image_url: str
    message: str


class DiscConfirmResponse(BaseModel):
    """Response for disc confirmation."""
    disc_id: int
    status: str
    message: str


class DiscCancelResponse(BaseModel):
    """Response for disc cancellation."""
    disc_id: int
    deleted: bool
    message: str


class BorderUpdateRequest(BaseModel):
    """Request to update disc border."""
    border: Dict


class BorderUpdateResponse(BaseModel):
    """Response for border update."""
    disc_id: int
    border_info: Dict
    message: str


class DiscListItem(BaseModel):
    """Single disc in the list response."""
    disc_id: int
    owner_name: str
    owner_contact: str
    disc_model: Optional[str]
    disc_color: Optional[str]
    notes: Optional[str]
    status: str
    location: Optional[str]
    registered_date: str
    image_id: Optional[int]
    image_url: Optional[str]
    image_path: Optional[str]
    border_info: Optional[Dict]
    cropped_image_path: Optional[str]
    created_at: Optional[str]


class DiscListResponse(BaseModel):
    """Response for disc list."""
    discs: List[DiscListItem]
    total: int


@upload_router.get("/list", response_model=DiscListResponse)
async def list_discs():
    """
    Get all discs with upload_status='SUCCESS'.

    Returns:
        DiscListResponse with list of all successful disc uploads
    """
    try:
        matcher = get_disc_matcher()
        discs = matcher.database.get_all_successful_discs()

        # Convert to response format
        disc_items = []
        for disc in discs:
            disc_items.append(DiscListItem(
                disc_id=disc['disc_id'],
                owner_name=disc['owner_name'],
                owner_contact=disc['owner_contact'],
                disc_model=disc.get('disc_model'),
                disc_color=disc.get('disc_color'),
                notes=disc.get('notes'),
                status=disc['status'],
                location=disc.get('location'),
                registered_date=disc['registered_date'].isoformat() if disc.get('registered_date') else None,
                image_id=disc.get('image_id'),
                image_url=disc.get('image_url'),
                image_path=disc.get('image_path'),
                border_info=disc.get('border_info'),
                cropped_image_path=disc.get('cropped_image_path'),
                created_at=disc['created_at'].isoformat() if disc.get('created_at') else None
            ))

        return DiscListResponse(
            discs=disc_items,
            total=len(disc_items)
        )

    except Exception as e:
        logger.error(f"Error listing discs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing discs: {str(e)}"
        )


@upload_router.post("/upload", response_model=DiscUploadResponse)
async def upload_disc(image: UploadFile = File(...)):
    """
    Upload a new disc image and detect border.

    Creates a disc record with PENDING status, saves the image,
    and runs border detection. The user can then confirm or cancel.

    Args:
        image: Disc image file (PNG, JPG, JPEG)

    Returns:
        DiscUploadResponse with disc_id, border detection results, and image URL
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

    # Use registration service
    matcher = get_disc_matcher()
    service = DiscRegistrationService(disc_matcher=matcher)

    result = service.register_from_bytes(
        image_bytes=contents,
        filename=image.filename or "disc.jpg",
        owner_name="Pending",
        owner_contact="pending@example.com",
        status='registered',
        upload_status='PENDING'
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error_message or "Error processing image"
        )

    disc_id = result.disc_id
    border_detected = result.border_detected

    if border_detected:
        logger.info(f"Border detected for disc {disc_id} (confidence: {result.border_confidence:.2f})")
        message = f"Border detected successfully (confidence: {result.border_confidence:.2f})"
    else:
        logger.info(f"No border detected for disc {disc_id}")
        message = "No border detected. You can still save this disc."

    # Construct image URL
    image_filename = image.filename or "disc.jpg"
    image_url = f"/discs/identification/{disc_id}/images/{image_filename}"

    # Get border info from database if detected
    border_info = None
    if border_detected:
        disc_image = matcher.database.get_disc_image_by_disc_id(disc_id)
        if disc_image:
            border_info = disc_image.get('border_info')

    return DiscUploadResponse(
        disc_id=disc_id,
        border_detected=border_detected,
        border=border_info,
        image_url=image_url,
        message=message
    )


@upload_router.post("/{disc_id}/confirm", response_model=DiscConfirmResponse)
async def confirm_disc(disc_id: int):
    """
    Confirm disc upload and mark as SUCCESS.

    Updates the disc's upload_status from PENDING to SUCCESS,
    making it available for matching.

    Args:
        disc_id: Disc ID to confirm

    Returns:
        DiscConfirmResponse with confirmation status
    """
    try:
        matcher = get_disc_matcher()

        # Check if disc exists and is pending
        disc_info = matcher.database.get_disc_by_id(disc_id)
        if not disc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Disc with ID {disc_id} not found"
            )

        if disc_info.get('upload_status') != 'PENDING':
            raise HTTPException(
                status_code=400,
                detail=f"Disc {disc_id} is not in PENDING status (current: {disc_info.get('upload_status')})"
            )

        # Confirm the upload
        success = matcher.database.confirm_disc_upload(disc_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to confirm disc {disc_id}"
            )

        logger.info(f"Disc {disc_id} confirmed successfully")

        return DiscConfirmResponse(
            disc_id=disc_id,
            status='SUCCESS',
            message="Disc saved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming disc: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error confirming disc: {str(e)}"
        )


@upload_router.delete("/{disc_id}/cancel", response_model=DiscCancelResponse)
async def cancel_disc(disc_id: int):
    """
    Cancel disc upload and delete all data.

    Deletes the disc record and all associated files from the filesystem.
    Only works for discs with PENDING status.

    Args:
        disc_id: Disc ID to cancel

    Returns:
        DiscCancelResponse with deletion status
    """
    try:
        matcher = get_disc_matcher()

        # Check if disc exists
        disc_info = matcher.database.get_disc_by_id(disc_id)
        if not disc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Disc with ID {disc_id} not found"
            )

        # Verify disc is in PENDING status (safety check)
        if disc_info.get('upload_status') != 'PENDING':
            raise HTTPException(
                status_code=400,
                detail=f"Can only cancel discs with PENDING status. Current status: {disc_info.get('upload_status')}"
            )

        # Delete files from filesystem
        disc_dir = os.path.join(Config.UPLOAD_DIR, str(disc_id))
        if os.path.exists(disc_dir):
            shutil.rmtree(disc_dir)
            logger.info(f"Deleted directory for disc {disc_id}: {disc_dir}")

        # Delete from database (CASCADE will delete disc_images too)
        success = matcher.database.delete_disc(disc_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete disc {disc_id} from database"
            )

        logger.info(f"Disc {disc_id} cancelled and deleted successfully")

        return DiscCancelResponse(
            disc_id=disc_id,
            deleted=True,
            message="Disc cancelled and deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling disc: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling disc: {str(e)}"
        )


@upload_router.delete("/{disc_id}", response_model=DiscCancelResponse)
async def delete_disc(disc_id: int):
    """
    Delete a disc and all associated data.

    Deletes the disc record and all associated files from the filesystem.
    Works for discs with any status.
    """
    try:
        matcher = get_disc_matcher()
        disc = matcher.database.get_disc_by_id(disc_id)
        if not disc:
            raise HTTPException(
                status_code=404,
                detail=f"Disc {disc_id} not found"
            )

        # Delete files from filesystem
        disc_dir = os.path.join(Config.UPLOAD_DIR, str(disc_id))
        if os.path.exists(disc_dir):
            shutil.rmtree(disc_dir)
            logger.info(f"Deleted directory for disc {disc_id}: {disc_dir}")

        # Delete from database (CASCADE will delete disc_images too)
        success = matcher.database.delete_disc(disc_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete disc {disc_id} from database"
            )

        logger.info(f"Disc {disc_id} deleted successfully")

        return DiscCancelResponse(
            disc_id=disc_id,
            deleted=True,
            message="Disc deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting disc: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting disc: {str(e)}"
        )


@upload_router.put("/{disc_id}/border", response_model=BorderUpdateResponse)
async def update_disc_border(disc_id: int, request: BorderUpdateRequest):
    """
    Update disc border with manual adjustments and regenerate embeddings.

    This endpoint:
    1. Loads the original image
    2. Applies the new border
    3. Generates cropped image
    4. Generates embeddings for the cropped region
    5. Updates the database

    Args:
        disc_id: Disc ID
        request: New border information

    Returns:
        BorderUpdateResponse with updated border info
    """
    try:
        matcher = get_disc_matcher()

        # Check if disc exists and is PENDING
        disc_info = matcher.database.get_disc_by_id(disc_id)
        if not disc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Disc with ID {disc_id} not found"
            )

        # Allow border updates for both PENDING and SUCCESS (confirmed) discs
        if disc_info.get('upload_status') not in ('PENDING', 'SUCCESS'):
            raise HTTPException(
                status_code=400,
                detail=f"Can only update border for discs with PENDING or SUCCESS status"
            )

        # Get the disc's image record
        disc_image = matcher.database.get_disc_image_by_disc_id(disc_id)
        if not disc_image:
            raise HTTPException(
                status_code=404,
                detail=f"No image found for disc {disc_id}"
            )

        # Load original image from filesystem
        image_path = disc_image.get('image_path')
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found for disc {disc_id}"
            )

        logger.info(f"Loading image from {image_path}")
        pil_image = load_image_with_orientation(image_path)

        # Apply the new border
        border_result = matcher.border_service.apply_border(
            image=pil_image,
            border_info=request.border,
            disc_id=disc_id,
            save_cropped=Config.STORE_CROPPED_IMAGES
        )

        if not border_result.detected or not border_result.cropped_image:
            raise HTTPException(
                status_code=400,
                detail="Failed to apply border and create cropped image"
            )

        # Generate embeddings
        cropped_embedding = None
        if matcher.border_service.should_use_cropped(border_result):
            logger.info(f"Generating embedding for manually adjusted border on disc {disc_id}")
            cropped_embedding = matcher.encoder.encode(border_result.cropped_image)

        # Update database
        success = matcher.database.update_disc_image_border(
            image_id=disc_image['id'],
            border_info=request.border,
            cropped_embedding=cropped_embedding,
            cropped_image_path=border_result.cropped_image_path,
            preprocessing_metadata=border_result.preprocessing_metadata
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update border info for disc {disc_id}"
            )

        logger.info(f"Border updated successfully for disc {disc_id}")

        return BorderUpdateResponse(
            disc_id=disc_id,
            border_info=request.border,
            message="Border updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating border: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating border: {str(e)}"
        )


# OCR Text Detection Endpoints
ocr_router = APIRouter(prefix="/discs/text-detection", tags=["text-detection"])


class AvailableOCRsResponse(BaseModel):
    """Response for available OCR engines."""
    ocrs: List[str]
    total: int


class TextDetectionRequest(BaseModel):
    """Request for text detection."""
    ocr_name: str


class TextDetectionResponse(BaseModel):
    """Response for text detection."""
    texts: List[str]
    confidences: List[float]
    bounding_boxes: List[Dict]
    detected_count: int
    ocr_used: str


@ocr_router.get("/available-ocrs", response_model=AvailableOCRsResponse)
async def get_available_ocrs():
    """
    Get list of available OCR engines.

    Returns:
        AvailableOCRsResponse with list of OCR engine names
    """
    try:
        ocrs = OCRService.get_available_ocrs()
        return AvailableOCRsResponse(
            ocrs=ocrs,
            total=len(ocrs)
        )
    except Exception as e:
        logger.error(f"Error getting available OCRs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting available OCRs: {str(e)}"
        )


@ocr_router.post("", response_model=TextDetectionResponse)
async def detect_text(
    image: UploadFile = File(...),
    ocr_name: str = Form(...)
):
    """
    Detect text in an image using specified OCR engine.

    Upload an image and specify which OCR engine to use for text detection.

    Args:
        image: Image file (PNG, JPG, JPEG)
        ocr_name: Name of OCR engine to use

    Returns:
        TextDetectionResponse with detected texts and metadata
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
        pil_image = load_image_with_orientation(io.BytesIO(contents))

        # Detect text
        result = OCRService.detect_text(pil_image, ocr_name)

        return TextDetectionResponse(
            texts=result.texts,
            confidences=result.confidences,
            bounding_boxes=result.bounding_boxes,
            detected_count=len(result.texts),
            ocr_used=ocr_name
        )

    except ValueError as e:
        # OCR not found or not available
        logger.error(f"OCR validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error detecting text: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
