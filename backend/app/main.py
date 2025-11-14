from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import logging

from app.services.shape_predictor import ShapePredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Shape Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Shape Detection API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


class HelloWorldRequest(BaseModel):
    message: str


class HelloWorldResponse(BaseModel):
    response: str


@app.post("/hello-world", response_model=HelloWorldResponse)
async def hello_world(request: HelloWorldRequest):
    reversed_message = request.message[::-1]
    current_date = datetime.now().strftime("%d.%m.%Y %H.%M.%S")
    response_text = f"{reversed_message} {current_date}"
    return HelloWorldResponse(response=response_text)


class ShapeDetectionResponse(BaseModel):
    shape: str
    confidence: float
    probabilities: Dict[str, float]


# Initialize predictor on startup
predictor = None


@app.on_event("startup")
async def startup_event():
    """Initialize the shape predictor when the app starts."""
    global predictor
    try:
        logger.info("Initializing shape predictor...")
        predictor = ShapePredictor.get_instance()
        logger.info("Shape predictor initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize shape predictor: {e}")
        raise


@app.post("/detect-shape", response_model=ShapeDetectionResponse)
async def detect_shape(image: UploadFile = File(...)):
    """
    Detect the shape in an uploaded image.

    Args:
        image: Uploaded image file (PNG, JPG, JPEG)

    Returns:
        ShapeDetectionResponse with shape name, confidence, and probabilities
    """
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg"]
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {image.content_type}. Only PNG, JPG, JPEG are supported."
        )

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    contents = await image.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is 10MB."
        )

    try:
        # Make prediction
        logger.info(f"Processing image: {image.filename}")
        result = predictor.predict(contents)
        logger.info(f"Prediction: {result['shape']} (confidence: {result['confidence']:.2f})")

        return ShapeDetectionResponse(**result)

    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
