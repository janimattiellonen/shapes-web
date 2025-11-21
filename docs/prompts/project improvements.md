#Project improvements

##Database migrations

- Alembic is now in use

## Automatic border detection and removal of non-disc data

Each image of a disc will contain a varying background, that may consist of floor, cloth, sand, table etc and might interfere with disc
identification.

We need to somehow identify what parts of the image contain the actual disc.

Assuming the whole disc fits the image, the border of the disc should be pretty close to the boundaries of the image. That is, the discs takes most
of the image's area and is most likely centered.

We have two options:

1) identify the border and delete any image data outside of it
2) identify theborder and only use the data inside that border for image comparion later on

Image format:

Is it possible that the image format (png, jpeg etc) may interfere with matcning discs?


What do you suggest?

⏺ I'll help you design a solution for disc border detection and handling non-disc background data in your images. Let me first explore the codebase
to understand the current implementation.

⏺ Explore(Explore disc image processing)
⎿  Done (31 tool uses · 52.2k tokens · 2m 19s)

⏺ Based on my exploration, I can see you already have a border detection implementation! Now let me provide recommendations for your specific
questions:

My Recommendations

Option 2: Use mask-based region extraction (recommended)

I recommend identifying the border and only using data inside that border for several reasons:

1. Preserves Original Images: Your original images stay intact for user viewing and verification
2. More Flexible: You can re-process images with different border detection parameters without losing data
3. Better for ML Models: Modern encoders (CLIP/DINOv2) can handle masked regions efficiently
4. Storage Efficient: No need to store multiple versions of the same image

Implementation Strategy

Here's what I suggest:

1. Extend Current Border Detection (disc_border_detector.py:1)
   Add a masking feature to your existing border detection:

# In addition to returning border coordinates, generate a binary mask
def create_disc_mask(image: Image.Image, border_info: dict) -> Image.Image:
"""Creates a binary mask where disc area is white, background is black"""
mask = Image.new('L', image.size, 0)  # Black background
draw = ImageDraw.Draw(mask)

      if border_info['type'] == 'circle':
          # Draw filled circle
          center = border_info['center']
          radius = border_info['radius']
          draw.ellipse([
              center['x'] - radius, center['y'] - radius,
              center['x'] + radius, center['y'] + radius
          ], fill=255)
      elif border_info['type'] == 'ellipse':
          # Draw filled ellipse
          # ... similar implementation

      return mask

2. Apply Mask Before Encoding
   Modify your encoder preprocessing in base_encoder.py:1:

def preprocess_image(self, image: Image.Image, mask: Optional[Image.Image] = None):
if mask:
# Create white background
background = Image.new('RGB', image.size, (255, 255, 255))
# Composite: disc pixels from image, white elsewhere
image = Image.composite(image, background, mask)

      # Continue with normal preprocessing (RGB conversion, etc.)
      return self._process_for_model(image)

3. Workflow Integration

Upload → Border Detection → Generate Mask → Apply Mask → Encode → Store Embedding
↓
Store original + border info (optional)

Image Format Impact

Yes, image format CAN affect matching, but your current setup handles this well:

Current Protection (in your codebase):
- Both encoders convert to RGB: base_encoder.py
- This normalizes JPEG, PNG, etc. to the same color space
- Embeddings are format-agnostic after encoding

Potential Issues:
- JPEG compression artifacts: Can slightly affect embeddings, especially with low quality
- PNG transparency: Handled by RGB conversion (transparent → black)
- Color profiles: Different color spaces could cause slight variations

My Recommendation:
- Store originals as PNG (lossless, no artifacts)
- When processing for matching: Convert to RGB as you currently do
- Set consistent quality: Your quality=95 for JPEG saves is good

Enhanced Border Detection Suggestions

Looking at disc_border_detector.py:1, here are some improvements:

1. Add Confidence Thresholding:
   - Only use border detection if confidence > 0.6
   - Otherwise, use full image (better than bad cropping)
2. Add Manual Override:
   - Let users manually adjust border if detection fails
   - Store border coordinates in database
3. Multiple Border Strategies:
   - Try circle first (discs are circular)
   - Fall back to ellipse (camera angle distortion)
   - Fall back to contour-based (irregular shapes)
   - Your current two-stage approach is already good!

Proposed Database Schema Addition

ALTER TABLE disc_images ADD COLUMN border_info JSONB;
ALTER TABLE disc_images ADD COLUMN border_confidence FLOAT;

This lets you:
- Store border detection results per image
- Re-process embeddings if you improve border detection
- Show users which images had poor border detection

Summary: My Recommendation

✅ Use Option 2: Mask-based approach (non-destructive)
✅ Apply masking before encoding (not after)
✅ Store border info in database for reprocessing
✅ Keep originals as PNG when possible
✅ Add confidence thresholds for border detection

Would you like me to implement these improvements to your existing border detection system?


Vastaus 17.11.2025 klo 18.45:

Updated Analysis: Current State of Your Disc Border Detection System

  Based on my fresh exploration, here's what I found:

  Critical Discovery: You Have Border Detection, But It's Not Being Used! ⚠️

  Your codebase has a fully functional border detection system (disc_border_detector.py:1-309), but it's completely disconnected
  from your encoding pipeline. Currently:

  - ✅ Border detection works (circle + ellipse detection)
  - ✅ Cropping function exists (crop_to_border() at line 269)
  - ❌ Never called during disc registration or search
  - ❌ Full images (with backgrounds) are encoded directly

  Current Architecture

  Upload → Validate → PIL Image → CLIP/DINOv2 Encoder → 768D Embedding → Database
                                         ↑
                                (includes full background!)

  Border Detection Endpoint exists separately but unused ↓
  POST /discs/border-detection → Returns coordinates but doesn't affect encoding

  Specific Recommendations Based on Your Code

  Option 1: Integrate Border Detection into Encoding Pipeline (Recommended)

  Modify disc_matcher.py:34-96 (the add_disc method):

  # Current code at line 61-63:
  def add_disc(self, image, owner_name, owner_contact, ...):
      # Extract embedding
      embedding = self.encoder.encode(image)  # ← Uses full image!

  # Proposed change:
  def add_disc(self, image, owner_name, owner_contact, ...):
      # NEW: Detect and crop to disc border
      border_info = self.border_detector.detect_border(image)
      if border_info and border_info.get('confidence', 0) > 0.6:
          image = self.border_detector.crop_to_border(image, border_info)

      # Extract embedding from cropped image
      embedding = self.encoder.encode(image)

  Option 2: Add Masking to Base Encoder

  Extend base_encoder.py:43-62 to support optional masking:

  def preprocess_image(
      self,
      image: Image.Image,
      border_info: Optional[dict] = None,
      target_size: Optional[tuple] = None
  ) -> Image.Image:
      """Preprocess image with optional disc masking"""

      # NEW: Apply circular/elliptical mask if border detected
      if border_info:
          mask = self._create_mask(image.size, border_info)
          # Composite: disc on white background
          background = Image.new('RGB', image.size, (255, 255, 255))
          image = Image.composite(image, background, mask)

      # Existing RGB conversion (line 55)
      if image.mode != 'RGB':
          image = image.convert('RGB')

      # Existing resize (line 60)
      if target_size:
          image = image.resize(target_size, Image.Resampling.LANCZOS)

      return image

  def _create_mask(self, size, border_info):
      """Create binary mask from border detection results"""
      mask = Image.new('L', size, 0)  # Black background
      draw = ImageDraw.Draw(mask)

      if border_info['type'] == 'circle':
          center = border_info['center']
          radius = border_info['radius']
          bbox = [
              center['x'] - radius, center['y'] - radius,
              center['x'] + radius, center['y'] + radius
          ]
          draw.ellipse(bbox, fill=255)
      elif border_info['type'] == 'ellipse':
          # Similar for ellipse...
          pass

      return mask

  Option 3: Database Schema Enhancement

  Add border metadata storage (currently not tracked):

  -- New migration needed
  ALTER TABLE disc_images
  ADD COLUMN border_info JSONB,
  ADD COLUMN border_confidence FLOAT,
  ADD COLUMN preprocessing_applied VARCHAR(50);

  This would let you:
  - Track which images had border detection applied
  - Re-process embeddings if you improve border detection later
  - A/B test cropped vs. masked vs. full-image approaches

  Image Format Impact (Updated Analysis)

  Your current setup handles formats well:

  ✅ What's working:
  - All images converted to RGB before encoding (base_encoder.py:55)
  - Saved with quality=95 JPEG (disc_matcher.py:240)
  - Format-agnostic after RGB conversion

  ⚠️ Potential issues:
  - JPEG artifacts from quality=95 could slightly affect embeddings
  - No deduplication: Same disc uploaded twice creates duplicate embeddings
  - Background variation (floor/table/cloth) affects embeddings more than it should

  Recommendation: Keep current format handling, but add border preprocessing to reduce background noise impact.

  Which Option Should You Choose?

  | Approach                        | Pros                                                | Cons                             |
  Recommendation              |
  |---------------------------------|-----------------------------------------------------|----------------------------------|------
  -----------------------|
  | Option 1: Crop before encoding  | Simple, reduces computation, smaller images         | Destructive, can't adjust later  | ⭐
  Best for storage/speed    |
  | Option 2: Mask before encoding  | Preserves original, adjustable, same embedding size | More complex, slight overhead    | ⭐
  Best for flexibility      |
  | Option 3: Store border metadata | Enables reprocessing, analytics                     | Doesn't improve current matching | ⭐
  Add this to either option |

  My Top Recommendation

  Combine Options 1 + 3:

  1. Modify disc_matcher.py:61-63 to crop to border before encoding
  2. Add database columns to track border info and preprocessing
  3. Add config flag to enable/disable border preprocessing
  4. Keep the standalone endpoint for debugging/visualization

  This gives you:
  - Immediate improvement in matching accuracy (less background noise)
  - Ability to A/B test cropped vs. non-cropped
  - Historical data on border detection confidence
  - Option to reprocess old images with new border detection params

  Implementation Priority

  Priority 1: Integrate cropping into add_disc() and find_matches()
  Priority 2: Add database columns for border metadata
  Priority 3: Add config flag for toggling preprocessing
  Priority 4: Create migration script to reprocess existing images

  Would you like me to implement Priority 1 (integrate border detection into the encoding pipeline)? I can modify the specific files
   with the exact changes needed.
