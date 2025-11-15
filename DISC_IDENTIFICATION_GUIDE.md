# Disc Golf Disc Identification System - Quick Start Guide

## System Overview

Your disc identification system is now running and ready to use! The system uses pre-trained AI models (CLIP or DINOv2) to match disc golf disc images without any training required.

## What's Running

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL Database**: localhost:5440 (external), postgres:5432 (internal)
- **Current Encoder**: CLIP (switchable to DINOv2)

## Architecture

```
┌──────────────────────────────────────────┐
│  Disc Identification Module             │
│  (Separate from Shape Detection)        │
└──────────────────────────────────────────┘
         │
         ├─ CLIP Encoder (default)
         │   └─ 512D embeddings → padded to 768D
         │
         ├─ DINOv2 Encoder (optional)
         │   └─ 768D embeddings
         │
         └─ PostgreSQL + pgvector
             └─ Fast similarity search
```

## API Endpoints

### 1. Register a Disc
```bash
POST /discs/identification/register
```

**Example:**
```bash
curl -X POST http://localhost:8000/discs/identification/register \
  -F "image=@/path/to/disc.jpg" \
  -F "owner_name=John Doe" \
  -F "owner_contact=john@example.com" \
  -F "disc_model=Innova Destroyer" \
  -F "disc_color=Blue" \
  -F "notes=Custom dye pattern"
```

**Response:**
```json
{
  "disc_id": 1,
  "image_id": 1,
  "model_used": "clip",
  "message": "Disc registered successfully"
}
```

### 2. Search for Matching Discs
```bash
POST /discs/identification/search
```

**Example:**
```bash
curl -X POST http://localhost:8000/discs/identification/search \
  -F "image=@/path/to/found_disc.jpg" \
  -F "top_k=5" \
  -F "min_similarity=0.7"
```

**Response:**
```json
{
  "matches": [
    {
      "disc_id": 1,
      "owner_name": "John Doe",
      "owner_contact": "john@example.com",
      "disc_model": "Innova Destroyer",
      "disc_color": "Blue",
      "similarity": 0.92,
      "status": "registered"
    }
  ],
  "total_matches": 1,
  "model_used": "clip"
}
```

### 3. Get Disc Information
```bash
GET /discs/identification/{disc_id}
```

**Example:**
```bash
curl http://localhost:8000/discs/identification/1
```

### 4. Mark Disc as Stolen
```bash
PATCH /discs/identification/{disc_id}/status
```

**Example:**
```bash
curl -X PATCH http://localhost:8000/discs/identification/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "stolen"}'
```

### 5. Add Additional Images
```bash
POST /discs/identification/{disc_id}/images
```

**Example:**
```bash
curl -X POST http://localhost:8000/discs/identification/1/images \
  -F "image=@/path/to/another_angle.jpg"
```

### 6. Health Check
```bash
GET /discs/identification/health/check
```

**Example:**
```bash
curl http://localhost:8000/discs/identification/health/check
```

## Switching Between CLIP and DINOv2

To switch encoder models:

1. Create a `.env` file in `backend/` directory:
```bash
cd backend
cp .env.example .env
```

2. Edit `.env` and change:
```bash
ENCODER_TYPE=dinov2  # or 'clip'
```

3. Rebuild and restart:
```bash
docker-compose down
docker-compose up --build -d
```

## Database Access

Access PostgreSQL directly:
```bash
docker exec -it shapes-postgres psql -U postgres -d disc_identification
```

View all discs:
```sql
SELECT id, owner_name, disc_model, status FROM discs;
```

View all images:
```sql
SELECT id, disc_id, model_name FROM disc_images;
```

## Testing with Sample Images

### Step 1: Register a disc
```bash
# Create a test image or use an existing one
curl -X POST http://localhost:8000/discs/identification/register \
  -F "image=@/path/to/my_disc.jpg" \
  -F "owner_name=Test User" \
  -F "owner_contact=test@example.com" \
  -F "disc_model=Test Disc"
```

### Step 2: Search for the same disc
```bash
curl -X POST http://localhost:8000/discs/identification/search \
  -F "image=@/path/to/my_disc.jpg" \
  -F "top_k=5"
```

You should see a high similarity score (>0.9) when searching with the same image!

## Interactive API Documentation

Visit http://localhost:8000/docs in your browser to:
- See all available endpoints
- Test endpoints directly from the browser
- View request/response schemas
- Try different parameters

## Performance Notes

**First Run:**
- The first time you use an endpoint, it will download the CLIP model (~500MB)
- This happens automatically and only once
- Subsequent requests will be much faster

**Speed (CPU-only on M-series Mac):**
- Image encoding: ~200-500ms per image
- Database search: ~10-50ms for 1,000 discs
- Total time for search: ~300-600ms

**GPU Support:**
If you have a GPU-enabled environment, the system will automatically use it and be 5-10x faster.

## File Structure

```
backend/
├── app/
│   ├── disc_identification/     # ← New disc identification module
│   │   ├── encoders/
│   │   │   ├── base_encoder.py
│   │   │   ├── clip_encoder.py
│   │   │   ├── dinov2_encoder.py
│   │   │   └── encoder_factory.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── disc_matcher.py
│   │   ├── routes.py
│   │   └── README.md
│   ├── ml/                      # ← Existing shape detection
│   └── services/
├── db/
│   └── init.sql                 # ← Database schema
└── uploads/
    └── discs/                   # ← Uploaded disc images

docker-compose.yml               # ← Updated with PostgreSQL
```

## Configuration Options

All configurable via environment variables in `.env`:

```bash
# Encoder selection
ENCODER_TYPE=clip                    # 'clip' or 'dinov2'

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/disc_identification

# Image settings
UPLOAD_DIR=/app/uploads/discs
MAX_IMAGE_SIZE_MB=10

# Search settings
DEFAULT_TOP_K=10                     # Number of results to return
MIN_SIMILARITY_THRESHOLD=0.7         # Minimum similarity (0.0-1.0)
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs backend
docker-compose logs postgres
```

### Database connection issues
```bash
# Check if PostgreSQL is healthy
docker-compose ps

# Restart services
docker-compose restart
```

### Model download issues
If CLIP model download fails, the container needs internet access. Check:
```bash
docker exec shapes-backend ping -c 3 huggingface.co
```

## Next Steps

1. **Test the system** with real disc images
2. **Build a frontend** to make it user-friendly
3. **Add authentication** for production use
4. **Deploy to production** when ready
5. **Add more features**:
   - Email notifications for matches
   - Mobile app integration
   - OCR for phone numbers on discs
   - Geographic search

## Cost & Scaling

**Current Setup (Free):**
- Handles 100-1,000 users easily
- Good for local disc golf community
- Runs on free hosting tiers

**To Scale:**
- Add GPU for faster processing
- Use managed PostgreSQL
- Add CDN for images
- Costs: $50-250/month for 1,000-10,000 users

## Support

- API Docs: http://localhost:8000/docs
- Module README: `backend/app/disc_identification/README.md`
- Database Schema: `backend/db/init.sql`

## Example Use Cases

1. **Lost & Found**: Someone finds a disc, searches the system, reunites it with owner
2. **Theft Prevention**: Owner registers discs, marks as stolen if stolen, buyers can verify before purchasing
3. **Collection Management**: Users catalog their entire collection with photos
4. **Tournament Recovery**: After tournaments, found discs can be matched to owners

Enjoy your disc identification system! 🥏
