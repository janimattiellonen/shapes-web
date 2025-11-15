# Testing Your Disc Identification System

## Quick Start

You have **3 ways** to test the system with your disc image:

### Option 1: Python Script (Recommended)
```bash
python3 test_disc.py /path/to/your/disc_image.jpg
```

### Option 2: Bash Script
```bash
./test_disc_identification.sh /path/to/your/disc_image.jpg
```

### Option 3: Manual cURL Commands
See examples below.

---

## Using Your Disc Image

Your disc appears to be a **Clash Vanilla Distance Driver** (white, steady).

### Save your image first:
If you have the image in your clipboard or Downloads folder, note its path. For example:
```bash
~/Downloads/vanilla_disc.jpg
```

### Run the test:
```bash
cd /Users/janimattiellonen/Documents/Development/Keras/shapes-web

# Using Python (shows nice output)
python3 test_disc.py ~/Downloads/vanilla_disc.jpg

# Or using bash
./test_disc_identification.sh ~/Downloads/vanilla_disc.jpg
```

---

## Manual Testing Steps

### 1. Register Your Disc
```bash
curl -X POST http://localhost:8000/discs/identification/register \
  -F "image=@/path/to/disc.jpg" \
  -F "owner_name=Your Name" \
  -F "owner_contact=your@email.com" \
  -F "disc_model=Clash Vanilla" \
  -F "disc_color=White" \
  -F "notes=Distance driver - 11 speed, steady"
```

**Expected Response:**
```json
{
  "disc_id": 1,
  "image_id": 1,
  "model_used": "clip",
  "message": "Disc registered successfully"
}
```

### 2. Search for Your Disc
```bash
curl -X POST http://localhost:8000/discs/identification/search \
  -F "image=@/path/to/disc.jpg" \
  -F "top_k=5"
```

**Expected Response:**
```json
{
  "matches": [
    {
      "disc_id": 1,
      "owner_name": "Your Name",
      "disc_model": "Clash Vanilla",
      "similarity": 0.99,
      "status": "registered"
    }
  ],
  "total_matches": 1,
  "model_used": "clip"
}
```

The similarity should be **very high (>0.95)** when searching with the exact same image!

### 3. Get Disc Details
```bash
curl http://localhost:8000/discs/identification/1
```

### 4. Mark as Stolen (optional)
```bash
curl -X PATCH http://localhost:8000/discs/identification/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "stolen"}'
```

---

## Interactive Testing (Browser)

Visit: **http://localhost:8000/docs**

1. Click on **POST /discs/identification/register**
2. Click **"Try it out"**
3. Upload your image
4. Fill in the form
5. Click **"Execute"**
6. See the response!

Then try **POST /discs/identification/search** with the same image.

---

## What to Expect

### First Time Running:
- The system will download the CLIP model (~500MB)
- This takes 1-2 minutes
- Only happens once!

### After That:
- Registration: ~500ms
- Search: ~300-500ms
- Very high similarity when searching with same image (>0.95)

### Real-World Testing:
- Take multiple photos of the same disc (different angles)
- Register one photo
- Search with another photo
- Similarity should still be high (0.7-0.9) if it's the same disc

---

## Troubleshooting

### "Connection refused"
```bash
# Check if backend is running
docker-compose ps

# Start if needed
docker-compose up -d
```

### "Model download taking too long"
First time only - be patient. Check logs:
```bash
docker-compose logs -f backend
```

### "Low similarity scores"
- Normal for completely different discs
- Should be high (>0.9) for exact same image
- 0.7-0.9 for different photos of same disc
- <0.7 for different discs

### Check database
```bash
# See registered discs
docker exec shapes-postgres psql -U postgres -d disc_identification \
  -c "SELECT id, owner_name, disc_model, status FROM discs;"

# See images
docker exec shapes-postgres psql -U postgres -d disc_identification \
  -c "SELECT id, disc_id, model_name FROM disc_images;"
```

---

## Testing Different Scenarios

### Scenario 1: Lost & Found
```bash
# 1. Register your disc
python3 test_disc.py disc.jpg

# 2. Someone finds it and searches
# (same image for now, different photo in real life)
curl -X POST http://localhost:8000/discs/identification/search \
  -F "image=@disc.jpg"

# Should find high similarity!
```

### Scenario 2: Verify Before Buying
```bash
# Seller sends you photo of disc
# You search to see if it's reported stolen

curl -X POST http://localhost:8000/discs/identification/search \
  -F "image=@sellers_disc.jpg" \
  -F "status_filter=stolen"

# If match found with status=stolen, it's reported stolen!
```

### Scenario 3: Multiple Discs
```bash
# Register several discs
python3 test_disc.py disc1.jpg
python3 test_disc.py disc2.jpg
python3 test_disc.py disc3.jpg

# Search with any disc
python3 test_disc.py disc2.jpg

# Should match only disc2 with high similarity
```

---

## Performance Testing

```bash
# Time a registration
time curl -X POST http://localhost:8000/discs/identification/register \
  -F "image=@disc.jpg" \
  -F "owner_name=Test" \
  -F "owner_contact=test@test.com"

# Time a search
time curl -X POST http://localhost:8000/discs/identification/search \
  -F "image=@disc.jpg"
```

Expected: 300-600ms on M-series Mac (CPU only)

---

## Next Steps

1. **Test with your actual disc image**
2. **Try with different photos** of the same disc
3. **Test with different discs** to see low similarity
4. **Explore the API docs** at http://localhost:8000/docs
5. **Build a frontend** to make it user-friendly

---

## Quick Commands Reference

```bash
# Health check
curl http://localhost:8000/discs/identification/health/check

# Check backend logs
docker-compose logs -f backend

# Check database
docker exec -it shapes-postgres psql -U postgres -d disc_identification

# Restart system
docker-compose restart

# Rebuild (after code changes)
docker-compose up --build -d

# Stop everything
docker-compose down
```

Enjoy testing! 🥏
