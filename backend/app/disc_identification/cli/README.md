# Disc Identification CLI Tools

Command-line tools for managing disc identification database.

## Batch Import Tool

Import multiple disc images from a directory in a single operation.

### Features

- Processes all supported image files (JPG, JPEG, PNG) in a directory
- Automatic border detection for each image
- Progress reporting every 100 images (configurable)
- Continues processing on errors (non-blocking)
- Generates a detailed process report with successes and failures
- Validates image files before processing
- Applies EXIF orientation corrections automatically

### Usage

**Important**: Run the script from the `backend` directory, not from within the `cli` directory.

#### Basic Usage

```bash
cd /path/to/backend
python batch_import_discs.py /path/to/images/directory
```

Or using Python module syntax:

```bash
cd /path/to/backend
python -m app.disc_identification.cli.batch_import /path/to/images/directory
```

#### With Custom Owner Information

```bash
cd /path/to/backend
python batch_import_discs.py /path/to/images \
  --owner "John Doe" \
  --contact "john@example.com"
```

#### Change Progress Reporting Interval

```bash
# Report progress every 50 images instead of 100
cd /path/to/backend
python batch_import_discs.py /path/to/images --progress-interval 50
```

#### Enable Verbose Logging

```bash
cd /path/to/backend
python batch_import_discs.py /path/to/images --verbose
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `directory` | Directory containing images to import (required) | - |
| `--owner` | Default owner name for imported discs | "Batch Import" |
| `--contact` | Default owner contact for imported discs | "batch@example.com" |
| `--progress-interval` | Print progress every N images | 100 |
| `--verbose` | Enable verbose logging | false |

### Output

The tool generates a process report file in the source directory with the format:

```
process-report-[YYYY-MM-DD_HH-MM-SS].txt
```

The report includes:

- Summary statistics (total, successful, failed, duration)
- List of all successful imports with disc IDs
- List of all failed imports with error messages

### Example Output

```
================================================================================
BATCH IMPORT STARTED
================================================================================
Directory: /Users/john/disc-images
Total images found: 243
Progress will be reported every 100 images
================================================================================

Progress: 100/243 images processed
  Successful: 98
  Failed: 2
  Skipped: 0

Progress: 200/243 images processed
  Successful: 195
  Failed: 5
  Skipped: 0

Progress: 243/243 images processed
  Successful: 238
  Failed: 5
  Skipped: 0

================================================================================
BATCH IMPORT COMPLETED
================================================================================
Total files: 243
Processed: 243
Successful: 238
Failed: 5
Skipped: 0
Duration: 182.45 seconds
================================================================================

Process report saved to: /Users/john/disc-images/process-report-2025-01-21_14-32-15.txt
```

### Process Report Format

```
================================================================================
DISC BATCH IMPORT REPORT
================================================================================

Directory: /Users/john/disc-images
Timestamp: 2025-01-21_14-32-15
Duration: 182.45 seconds

Total files found: 243
Files processed: 243
Successful imports: 238
Failed imports: 5
Skipped files: 0

================================================================================
SUCCESSFUL IMPORTS
================================================================================

[SUCCESS] disc_001.jpg -> Disc ID: 1
[SUCCESS] disc_002.jpg -> Disc ID: 2
...

================================================================================
FAILED IMPORTS
================================================================================

[FAILED] corrupted.jpg
  Error: Error processing image: cannot identify image file

[FAILED] too_large.jpg
  Error: File too large: 12582912 bytes (max: 10485760 bytes)
```

### Exit Codes

- `0`: All images processed successfully
- `1`: One or more images failed to process (check report for details)

### Running from Docker

If you're running the backend in Docker, you can execute the batch import tool using:

```bash
# 1. Copy images from your local machine to the container
docker cp /path/to/local/images <container-name>:/tmp/import-images

# 2. Run the batch import inside the container
docker exec <container-name> python /app/app/batch_import_discs.py /tmp/import-images

# 3. Copy the process report back to your host
docker cp <container-name>:/tmp/import-images/process-report-*.txt .
```

Replace `<container-name>` with your actual Docker container name (e.g., `shapes-backend` or `shapes-web-backend-1`).

#### Complete Example:

```bash
# Copy test images to container
docker cp /Users/username/Desktop/disc-images shapes-backend:/tmp/disc-images

# Run batch import with custom owner info
docker exec shapes-backend python /app/app/batch_import_discs.py /tmp/disc-images \
  --owner "Tournament Collection" \
  --contact "tournament@example.com"

# Copy report to current directory
docker cp shapes-backend:/tmp/disc-images/process-report-*.txt .
```

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)

Files are matched case-insensitively (e.g., `.JPG`, `.Jpg`, `.jpg` all work).

### Configuration

The tool uses the same configuration as the main application:

- `UPLOAD_DIR`: Where images are stored
- `MAX_IMAGE_SIZE_MB`: Maximum file size (default: 10MB)
- `BORDER_DETECTION_ENABLED`: Whether to run border detection
- `ENCODER_TYPE`: Which encoder to use (clip or dinov2)

See `config.py` for all configuration options.

### Error Handling

The tool continues processing even if individual images fail. Common error scenarios:

1. **File not found**: Skipped, logged in report
2. **Invalid format**: Failed, logged with error message
3. **File too large**: Failed, logged with size details
4. **Corrupted image**: Failed, logged with PIL error
5. **Database error**: Failed, logged with database error

All errors are captured in the process report for review.

### Performance Considerations

- Processing speed depends on:
  - Image size and count
  - Border detection complexity
  - Encoder type (CLIP vs DINOv2)
  - Database performance
  - Disk I/O speed

- Typical performance:
  - ~1-2 seconds per image with border detection
  - ~0.5-1 second per image without border detection
  - ~600-1200 images per 20 minutes

### Troubleshooting

#### "No module named uvicorn" or import errors

Make sure you're in the correct Python environment:

```bash
# Activate the virtual environment
source venv/bin/activate  # or your environment activation command

# Install dependencies
pip install -r requirements.txt
```

#### "Database connection failed"

Ensure the database is running and the `DATABASE_URL` is configured correctly:

```bash
# Check database status
docker-compose ps postgres

# Check connection
psql $DATABASE_URL -c "SELECT 1"
```

#### Images are being skipped

Check that:
1. Images are in supported formats (JPG, JPEG, PNG)
2. Images are under the size limit (default 10MB)
3. Files have the correct extensions

### Best Practices

1. **Test with a small batch first** to ensure everything works
2. **Use descriptive owner names** to identify batch imports later
3. **Keep the source directory** until you verify the import was successful
4. **Review the process report** for any failed images
5. **Monitor disk space** as cropped images are also stored
