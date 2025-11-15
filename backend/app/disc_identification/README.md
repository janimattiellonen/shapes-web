# Disc Golf Disc Identification System

A computer vision-based system for identifying stolen or lost disc golf discs using image matching.

## How It Works

1. **Register Discs**: Users upload images of their discs to create a searchable database
2. **Image Embeddings**: Pre-trained models (CLIP or DINOv2) extract feature vectors from images
3. **Vector Search**: When searching, the system finds visually similar discs using cosine similarity
4. **Match Results**: Returns ranked matches with similarity scores

## Features

- **Zero-Training Approach**: Uses pre-trained models (no ML training required)
- **Swappable Encoders**: Easy switching between CLIP and DINOv2 models
- **Vector Database**: Fast similarity search with PostgreSQL + pgvector
- **RESTful API**: Complete CRUD operations for discs
- **Status Tracking**: Mark discs as registered, stolen, or found

## Architecture

```
┌─────────────────┐
│  Upload Image   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CLIP/DINOv2     │  ← Pre-trained model (switchable)
│ Encoder         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 768D Embedding  │  ← Feature vector
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PostgreSQL      │  ← Vector similarity search
│ + pgvector      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ranked Matches  │  ← Top-K results
└─────────────────┘
```

## API Endpoints

### Register a Disc
```
POST /discs/identification/register
```
Upload an image and metadata to register a disc.

### Search for Matches
```
POST /discs/identification/search
```
Upload an image to find matching discs in the database.

### Get Disc Info
```
GET /discs/identification/{disc_id}
```
Retrieve detailed information about a specific disc.

### Update Disc Status
```
PATCH /discs/identification/{disc_id}/status
```
Mark a disc as stolen, found, or registered.

### Add Additional Image
```
POST /discs/identification/{disc_id}/images
```
Add more images to improve matching accuracy.

### Health Check
```
GET /discs/identification/health/check
```
Check service status and current encoder configuration.

## Configuration

Set environment variables in `.env` file:

```bash
# Switch between models (clip or dinov2)
ENCODER_TYPE=clip

# Database connection
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/disc_identification

# Image settings
UPLOAD_DIR=/app/uploads/discs
MAX_IMAGE_SIZE_MB=10

# Search settings
DEFAULT_TOP_K=10
MIN_SIMILARITY_THRESHOLD=0.7
```

## Switching Models

To switch from CLIP to DINOv2 (or vice versa):

1. Update `.env` file:
   ```bash
   ENCODER_TYPE=dinov2  # or 'clip'
   ```

2. Restart the service

That's it! The system automatically uses the configured model.

## Module Structure

```
disc_identification/
├── encoders/
│   ├── base_encoder.py      # Abstract encoder interface
│   ├── clip_encoder.py      # CLIP implementation
│   ├── dinov2_encoder.py    # DINOv2 implementation
│   └── encoder_factory.py   # Factory pattern for creating encoders
├── config.py                # Configuration management
├── database.py              # Database operations
├── disc_matcher.py          # Core matching logic
└── routes.py                # FastAPI routes
```

## Database Schema

### `discs` table
- Stores disc metadata (owner, model, color, status, etc.)

### `disc_images` table
- Stores image embeddings and references
- Each disc can have multiple images
- Indexed by model type for fast searches

## Cost

- **100% Free** for development and small-scale use
- All models are open-source (CLIP, DINOv2)
- PostgreSQL + pgvector are free
- Runs on CPU (GPU optional for speed)

## Performance

**CLIP (CPU-only):**
- Encoding: ~200-500ms per image
- Search: ~10-50ms for 1,000 discs

**DINOv2 (CPU-only):**
- Encoding: ~300-600ms per image
- Search: ~10-50ms for 1,000 discs

**With GPU:**
- 5-10x faster encoding
- Similar search speeds

## Usage Examples

### Python
```python
from disc_identification.disc_matcher import DiscMatcher
from PIL import Image

# Initialize matcher
matcher = DiscMatcher()

# Register a disc
image = Image.open("my_disc.jpg")
result = matcher.add_disc(
    image=image,
    owner_name="John Doe",
    owner_contact="john@example.com",
    disc_model="Innova Destroyer",
    disc_color="Blue"
)

# Search for matches
found_image = Image.open("found_disc.jpg")
matches = matcher.find_matches(found_image, top_k=5)

for match in matches:
    print(f"Match: {match['owner_name']} ({match['similarity']:.2%})")
```

### cURL
```bash
# Register a disc
curl -X POST http://localhost:8000/discs/identification/register \
  -F "image=@my_disc.jpg" \
  -F "owner_name=John Doe" \
  -F "owner_contact=john@example.com" \
  -F "disc_model=Innova Destroyer"

# Search for matches
curl -X POST http://localhost:8000/discs/identification/search \
  -F "image=@found_disc.jpg" \
  -F "top_k=5"
```

## Future Enhancements

- [ ] Add OCR for text/phone numbers on discs
- [ ] Mobile app integration
- [ ] Batch image upload
- [ ] Email notifications for matches
- [ ] Geographic clustering
- [ ] Image deduplication
- [ ] Support for more encoder models
