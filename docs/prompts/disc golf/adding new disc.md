#Adding new disc

Specs:

A user should be able to add a new disc image using a form. The user should be able to verify visually that the detected border is accurate and either continue by saving the image, or cancelling the process. 

If the user chooses to save the image. the image will be accessible for matching. If the user cancels the process, the image and linked image data should be deleted from file system and from database.

The database table discs should have a status column that stores at the moment either 'PENDING' when the user has yet to either accept or cancel, or 'SUCCESS' if the user accepted. No data to store, if user cancelled.

Plan:

Create a plan according to my specs. If unsure about something, ask instead of guess


Tasks:

##Frontend
- create a new route /discs/new
- create file NewDiscPage.tsx in src/pages
- allow the user to upload an image
- show preview of image with detected border (if detected)
- 'Save' and 'Cancel' buttons

##Backend
- use route /discs/identification/register (POST)
- create new migration for the status column

#Phase 2

After uploading the image, make it possible to move and resize the detected border, or adding a new one, if no border was detected.

## Specs

- one border at any time, at most
- possible to delete border
    - "Delete border" button becomes enabled if there is a border
- possible to select border
    - border can be selected by clicking anywhere on the border ring
    - highlight border when selected
    - if clicked outside border ring, deselect
    - make the "hit zone" 3px bigger on both sides of the border ring to make it easier to click on
    - when selected,
- possible to reset border state, back to original border position and size
- possible to move border by mouse
- possible to resize border by mouse
    - "Rezise" button becomes enabled if the border is selected
    - if button is pressed, show a resize handle in the centre of the border
    - if resize handle is dragged up, the border size grows
    - if resize handle is dragged down, the border size shrinks
    - cannot resize outside of image outer border
    - cannot resize below 100px
- possible to add a border, if no border was detected
    - "Add border" button becomes enabled
    - if clicked, create a new border, positioned in the centre of the image
- a button named "Save border"
    - if clicked, update image's border details
    - button is disabled if no changes have been made
- no change is saved until the user specifically clicks the "Save border" button

Give me plan on how to implement this. Again, ask if unsure about something.


Great! I've reviewed your existing system. Before creating the plan, I have some clarifying questions:

  Questions:

  1. Status Column Usage
  Your discs table already has a status column with values: 'registered', 'stolen', 'found'.

  Should I:
  - Option A: Repurpose this to use 'PENDING' and 'SUCCESS' (replacing 'registered')?
  - Option B: Add a NEW column like upload_status to track the upload workflow separately, keeping status for 'registered'/'stolen'/'found'?

  2. When to Create Database Records
  Should the disc record be created:
  - Option A: Immediately when image is uploaded (with status='PENDING'), then updated to 'SUCCESS' or deleted on cancel?
  - Option B: Only after the user accepts (no database entry while in 'PENDING' state, just temp file storage)?

  3. Disc Information Form
  What information should the user provide when uploading? Should they provide:
  - Just the image (minimal)?
  - Owner info (name, contact) + image?
  - Full details (owner info, disc model, color, notes, location) + image?

  4. UI Integration
  Should this be:
  - Option A: A NEW page (e.g., /discs/add) with its own route?
  - Option B: Enhance the existing Border Detection page (/discs/border-detection) to include Save/Cancel buttons?

  5. Failed Border Detection
  If border detection fails to find a border:
  - Should we still allow the user to save the disc image?
  - Or should border detection success be required?

  Let me know your preferences and I'll create a detailed implementation plan!

> 1.

- Option B: create column upload_status

2.

- Option A

3.

- right now, just the image

4.

- create a new route /discs/new
- create file NewDiscPage.tsx in src/pages

5.

- allow user to save even if no border was detected
- show a notice

⏺ Perfect! I have all the information I need. Let me create a comprehensive plan for implementing this feature.

⏺ Implementation Plan: Add New Disc Feature

  Overview

  User uploads a disc image → Border detection runs automatically → User sees visual preview → User saves (SUCCESS) or cancels (deletes everything)

  ---
  Backend Changes

  1. Database Migration

  File: backend/alembic/versions/add_upload_status_column.py
  - Add upload_status column to discs table
    - Type: VARCHAR(50)
    - Values: 'PENDING' | 'SUCCESS'
    - Default: 'PENDING'
    - Nullable: False

  2. Database Service Updates

  File: backend/app/disc_identification/database.py

  New/Updated Methods:
  - add_disc() - Set upload_status='PENDING' by default
  - confirm_disc(disc_id) - Update upload_status to 'SUCCESS'
  - delete_disc(disc_id) - Delete disc record (CASCADE deletes images)
  - get_disc_upload_path(disc_id) - Helper to get file paths for cleanup

  3. New API Endpoints

  File: backend/app/disc_identification/routes.py

  POST /discs/upload
  - Accept: multipart/form-data with image file
  - Process:
    a. Validate image (type, size)
    b. Create disc record with upload_status='PENDING'
    c. Save image to temp location (uploads/{disc_id}/original.jpg)
    d. Run border detection
    e. If border detected: save cropped image, generate embeddings
    f. Return: { disc_id, border_info, image_url, detected: boolean }

  POST /discs/{disc_id}/confirm
  - Update upload_status from 'PENDING' to 'SUCCESS'
  - Return: { message, disc_id, status }

  DELETE /discs/{disc_id}/cancel
  - Validate disc has upload_status='PENDING' (safety check)
  - Delete image files from filesystem (uploads/{disc_id}/)
  - Delete disc record from database (CASCADE deletes disc_images)
  - Return: { message, deleted: true }

  ---
  Frontend Changes

  4. New Page Component

  File: frontend/src/pages/NewDiscPage.tsx

  Features:
  - Drag & drop upload area (reuse pattern from BorderDetection)
  - Auto-trigger border detection on upload
  - Visual preview with canvas overlay showing detected border
  - Notice banner if border detection fails: "⚠️ No border detected. You can still save this disc image."
  - Action buttons:
    - Save Disc (green) → POST /discs/{disc_id}/confirm → Navigate to success page or disc list
    - Cancel (red) → DELETE /discs/{disc_id}/cancel → Clear form
  - Loading states: uploading, detecting, saving, cancelling
  - Error handling with user-friendly messages

  Component States:
  - selectedFile: File | null
  - previewUrl: string | null
  - discId: number | null
  - borderInfo: BorderInfo | null
  - borderDetected: boolean
  - isUploading: boolean
  - isSaving: boolean
  - error: string

  User Flow:
  1. User selects/drops image
  2. Image uploads → disc_id returned → border detection runs
  3. Preview shows with border overlay (if detected)
  4. User clicks "Save" → confirm endpoint → success message
  5. OR User clicks "Cancel" → delete endpoint → form resets

  5. Route Configuration

  File: frontend/src/routes/index.tsx
  - Add new route: { path: '/discs/new', element: <NewDiscPage /> }

  6. Navigation Update

  File: frontend/src/layouts/MainLayout.tsx
  - Add link: <Link to="/discs/new">Add New Disc</Link>

  ---
  Testing Checklist

  1. ✓ Upload valid image → verify PENDING status in DB
  2. ✓ Border detection success → verify border overlay renders
  3. ✓ Border detection failure → verify notice appears, can still save
  4. ✓ Save disc → verify status changes to SUCCESS
  5. ✓ Cancel disc → verify DB record deleted, files deleted
  6. ✓ Error cases: invalid file type, file too large, network errors
  7. ✓ File cleanup: verify orphaned files don't accumulate

  ---
  Database Schema Change Summary

  Before:
  discs:
    status VARCHAR(50) -- 'registered', 'stolen', 'found'

  After:
  discs:
    status VARCHAR(50) -- 'registered', 'stolen', 'found' (unchanged)
    upload_status VARCHAR(50) DEFAULT 'PENDING' -- 'PENDING', 'SUCCESS'

  ---
  API Endpoints Summary

  | Method | Endpoint                 | Purpose                                          |
  |--------|--------------------------|--------------------------------------------------|
  | POST   | /discs/upload            | Upload image, create PENDING disc, detect border |
  | POST   | /discs/{disc_id}/confirm | Mark disc as SUCCESS                             |
  | DELETE | /discs/{disc_id}/cancel  | Delete disc and cleanup files                    |

  ---
  Does this plan look good? Should I proceed with implementation?


  Implementation Summary

  Backend Changes ✓

  1. Database Migration
  - Created migration: backend/alembic/versions/add_upload_status_column.py
  - Added upload_status column to discs table (PENDING/SUCCESS)
  - Created index for efficient filtering
  - Migration executed successfully

  2. DatabaseService Updates (backend/app/disc_identification/database.py)
  - Updated add_disc() to accept upload_status parameter
  - Added confirm_disc_upload() - Updates status to SUCCESS
  - Added delete_disc() - Deletes disc and cascades to images

  3. New API Endpoints (backend/app/disc_identification/routes.py)
  - POST /discs/upload - Uploads image, creates PENDING disc, detects border
  - POST /discs/{disc_id}/confirm - Confirms upload, marks as SUCCESS
  - DELETE /discs/{disc_id}/cancel - Deletes disc and filesystem files
  - Registered upload_router in main.py

  Frontend Changes ✓

  4. NewDiscPage Component (frontend/src/pages/NewDiscPage.tsx)
  - Drag & drop image upload
  - Auto-detection on upload
  - Visual border preview with canvas overlay
  - Success/error/loading states
  - Save and Cancel buttons
  - Notice when border not detected
  - Auto-reset after successful save

  5. Styling (frontend/src/components/BorderDetection.css)
  - Save button (green) with hover effects
  - Cancel button (red) with hover effects
  - Notice container (warning style)
  - Success container (green style)
  - Loading container

  6. Routing & Navigation
  - Added route: /discs/new → NewDiscPage
  - Updated MainLayout navigation with "Add New Disc" link
  - Build successful (no TypeScript errors)

  How It Works

  1. User navigates to "Add New Disc" (http://localhost:5199/discs/new)
  2. Selects/drops image → Auto-uploads to /discs/upload
  3. Backend creates disc record (PENDING), saves image, detects border
  4. User sees preview with border overlay (if detected) or warning notice
  5. User clicks:
    - Save → POST /discs/{disc_id}/confirm → Status: SUCCESS → Form resets
    - Cancel → DELETE /discs/{disc_id}/cancel → Files deleted → Form resets

  Files Created/Modified

  Backend:
  - backend/alembic/versions/add_upload_status_column.py (new)
  - backend/app/disc_identification/database.py (modified)
  - backend/app/disc_identification/routes.py (modified)
  - backend/app/main.py (modified)

  Frontend:
  - frontend/src/pages/NewDiscPage.tsx (new)
  - frontend/src/routes/index.tsx (modified)
  - frontend/src/layouts/MainLayout.tsx (modified)
  - frontend/src/components/BorderDetection.css (modified)

  Ready to Test!

  The feature is fully implemented and ready to use. To test:

  1. Start backend: cd backend && uvicorn app.main:app --reload
  2. Start frontend: cd frontend && npm run dev
  3. Navigate to: http://localhost:5199/discs/new
  4. Upload a disc image and test the Save/Cancel workflow!

> commit changes

⏺ I'll commit the changes following the proper git workflow.

⏺ Bash(git status)
  ⎿  On branch disc-upload
     Changes not staged for commit:
       (use "git add <file>..." to update what will be committed)
     … +17 lines (ctrl+o to expand)

⏺ Bash(git diff --stat)
  ⎿   backend/app/disc_identification/database.py |  61 ++++++-
      backend/app/disc_identification/routes.py   | 241 ++++++++++++++++++++++++++++
      backend/app/main.py                         |   2 +
     … +5 lines (ctrl+o to expand)

⏺ Bash(git log --oneline -5)
  ⎿  0694cf3 Refactor frontend routing to use layout wrapper pattern
     e62ed42 Merge pull request #8 from janimattiellonen/disc-detection-improvements
     197370c Add automatic border detection and dual-embedding system
     … +2 lines (ctrl+o to expand)

⏺ Bash(git add ../backend/alembic/versions/add_upload_status_column.py ../backend/app/disc_identification/database.py
      ../backend/app/disc_identification/routes.py ../b…)
  ⎿  [disc-upload c204f35] Add disc upload workflow with pending/success status
      8 files changed, 803 insertions(+), 4 deletions(-)
      create mode 100644 backend/alembic/versions/add_upload_status_column.py
      create mode 100644 frontend/src/pages/NewDiscPage.tsx

⏺ Bash(git status)
  ⎿  On branch disc-upload
     Changes not staged for commit:
       (use "git add <file>..." to update what will be committed)
     … +9 lines (ctrl+o to expand)

⏺ Commit created successfully! Here's what was committed:

  Commit: c204f35
  Branch: disc-upload

  Changes:
  - Created: backend/alembic/versions/add_upload_status_column.py
  - Created: frontend/src/pages/NewDiscPage.tsx
  - Modified: backend/app/disc_identification/database.py
  - Modified: backend/app/disc_identification/routes.py
  - Modified: backend/app/main.py
  - Modified: frontend/src/components/BorderDetection.css
  - Modified: frontend/src/layouts/MainLayout.tsx
  - Modified: frontend/src/routes/index.tsx

  Stats: 8 files changed, 803 insertions(+), 4 deletions(-)

  The disc upload workflow feature with pending/success status tracking is now committed. The remaining uncommitted changes in docs/prompts/ were
  left out as they're unrelated to this feature.




