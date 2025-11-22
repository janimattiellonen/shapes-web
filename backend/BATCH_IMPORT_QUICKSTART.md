# Batch Import Quick Start

Quick reference for batch importing disc images.

## Docker (Recommended)

```bash
# 1. Copy images to container
docker cp /path/to/your/images shapes-backend:/tmp/import

# 2. Run batch import
docker exec shapes-backend python /app/app/batch_import_discs.py /tmp/import

# 3. Get the report
docker cp shapes-backend:/tmp/import/process-report-*.txt .
```

## With Custom Options

```bash
docker exec shapes-backend python /app/app/batch_import_discs.py /tmp/import \
  --owner "Your Name" \
  --contact "your@email.com" \
  --progress-interval 50 \
  --verbose
```

## What Gets Created

For each successfully imported image:
- **Disc record** in database
- **Original image** saved to disk
- **Embeddings** for image matching
- **Cropped version** (if border detected)
- **Border metadata** (if border detected)

## Output

```
Progress: 100/243 images processed
  Successful: 98
  Failed: 2
  Skipped: 0
```

Process report saved as: `process-report-[YYYY-MM-DD_HH-MM-SS].txt`

## Full Documentation

See `app/disc_identification/cli/README.md` for complete documentation.
