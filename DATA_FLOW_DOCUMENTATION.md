# BodyScript Data Flow Documentation
*Based on verified code analysis - no assumptions*

## Data Tracing: Input → Output

### 1. INPUT STAGE
**Entry Point:** `/api/upload` endpoint in `app.py`
```python
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...))
```

**Input Data:**
- **Video File**: Uploaded as `UploadFile` object
- **File Constraints**: None enforced at API level (constraints applied later)
- **Job ID**: Generated UUID4 string for tracking

**Data Storage:**
```python
# File saved to temp location
file_path = f"temp/{job_id}_{file.filename}"
with open(file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
```

---

### 2. PROCESSING PIPELINE
**Controller:** `WebVideoProcessor.process_video()` in `process_wrapper.py`

#### Step 1: Video Trimming
**Input:** Original video file
**Process:**
```python
def trim_video(self, input_path: str, output_path: str, max_seconds: int = 15)
# Uses ffmpeg with "-c", "copy" (no re-encoding)
```
**Output:** `trimmed.mp4` (max 15 seconds)
**Data Modified:** Duration only, codec unchanged

#### Step 2: Resolution Check/Reduction
**Input:** Trimmed video
**Process:**
```python
def reduce_resolution_if_needed(self, video_path: str, max_width: int = 720)
# Uses ffmpeg scale filter if width > 720px
"-vf", f"scale={new_width}:{new_height}"
```
**Output:** Same file (overwritten if resized)
**Data Modified:** Resolution (maintains aspect ratio)

#### Step 3: Frame Extraction
**Input:** Processed video file
**Process:**
```python
extract_frames(
    trimmed_video,
    output_dir=frames_dir,
    interval=1,  # Process ALL frames
    format='jpg',
    quality=85
)
```
**Output:** Directory of JPEG files (`frame_XXXXXX.jpg`)
**Data Format:** Individual JPEG frames, quality=85

#### Step 4: MediaPipe Processing
**Input:** Frame directory
**Process:**
```python
processor = MediaPipeFastSmart(mode=mode)
results_df = processor.process_video_fast(
    frames_dir,
    csv_path,
    max_frames=None,
    progress_callback=mediapipe_progress
)
```
**Output:** Pandas DataFrame + CSV file
**Data Structure:**
- DataFrame with `visibility` column (verified)
- 33 landmarks per frame (inferred from detection_rate calculation)
- CSV at `{job_dir}/pose_data.csv`

#### Step 5: Statistics Calculation
**Input:** Results DataFrame
**Process:**
```python
avg_quality = results_df['visibility'].mean() if not results_df.empty else 0
detection_rate = len(results_df) / (frames_extracted * 33) if frames_extracted > 0 else 0
```
**Output:** Numerical metrics
**Data:** Average visibility, detection rate percentage

#### Step 6: Skeleton Overlay Generation
**Input:** Original video + CSV data
**Process:**
```python
self.create_skeleton_video(trimmed_video, csv_path, output_video)
# Falls back to copying trimmed video if overlay fails
```
**Output:** `output.mp4` with skeleton overlay
**Data:** Video with pose landmarks drawn on frames

#### Step 7: Thumbnail/Preview Generation
**Input:** Output video
**Process:**
```python
generate_thumbnail(output_video, thumbnail_path, size=(405, 720))
generate_preview(output_video, preview_path, duration=3, quality='low')
```
**Output:**
- `thumbnail.jpg` (405x720)
- `preview.mp4` (3-second, low quality)

---

### 3. METADATA CREATION
**Input:** All processing results
**Process:**
```python
metadata = {
    'job_id': job_id,
    'processed_at': datetime.now().isoformat(),
    'statistics': {
        'frames_processed': frames_extracted,
        'average_quality': float(avg_quality),
        'detection_rate': float(detection_rate),
        'processing_time': time.time() - start_time,
        'processing_mode': mode,
        'video_was_trimmed': trim_info['was_trimmed'],
        'video_was_resized': was_resized,
        'original_duration': trim_info['original_duration'],
        'processed_duration': trim_info['trimmed_duration']
    },
    'urls': {
        'thumbnail': f"/api/serve/{job_id}/thumbnail.jpg",
        'preview': f"/api/serve/{job_id}/preview.mp4",
        'full': f"/api/serve/{job_id}/output.mp4",
        'csv': f"/api/serve/{job_id}/pose_data.csv"
    }
}
```

---

### 4. OUTPUT STAGE
**File Structure Created:**
```
temp/{job_id}/
├── trimmed.mp4          # Processed input video
├── frames/              # Directory of extracted frames
│   ├── frame_000000.jpg
│   ├── frame_000001.jpg
│   └── ...
├── pose_data.csv        # MediaPipe landmark data
├── output.mp4           # Video with skeleton overlay
├── thumbnail.jpg        # 405x720 preview image
└── preview.mp4          # 3-second preview video
```

**API Endpoints for Access:**
- `GET /api/download/{job_id}/video` → `output.mp4`
- `GET /api/download/{job_id}/csv` → `pose_data.csv`
- `GET /api/serve/{job_id}/{filename}` → Any file in job directory
- `GET /api/gallery` → Metadata for all processed jobs

---

### 5. DATA FORMATS

#### CSV Structure (Inferred from code):
- **Rows:** 33 landmarks × number of frames
- **Columns:** Must include `visibility` (verified), others unknown
- **File:** UTF-8 encoded CSV

#### Video Output:
- **Container:** MP4
- **Content:** Original frames with skeleton overlay drawn
- **Fallback:** Original trimmed video if overlay fails

#### Metadata JSON:
- **Storage:** In-memory Python dict (`jobs_status`)
- **Persistence:** None (lost on server restart)
- **Structure:** As shown in metadata creation section

---

### 6. RESOURCE MANAGEMENT

#### Memory Cleanup:
```python
# Delete original after trimming
if os.path.exists(input_video_path) and input_video_path != trimmed_video:
    os.remove(input_video_path)

# Force garbage collection
import gc
gc.collect()

# Clean up MediaPipe resources
processor.close()
```

#### Job Retention:
```python
JOB_MAX_AGE_SECONDS = 3600  # 1 hour
CLEANUP_INTERVAL_SECONDS = 1800  # 30 minutes
```

---

### 7. UNVERIFIED COMPONENTS

**Cannot trace these data flows (referenced but not accessible):**
- Internal MediaPipe landmark detection algorithms
- Frame extraction implementation details
- Skeleton overlay drawing logic
- CLI module data structures
- Frontend data consumption patterns

**Data assumptions NOT verified:**
- Exact CSV column names/structure
- Landmark coordinate systems
- Error handling data flows
- WebSocket data streaming (if implemented)

---

## Summary: Verified Data Path

**Input:** Video file (any format/size)
↓
**Stage 1:** Trim to 15 seconds, reduce to ≤720p
↓
**Stage 2:** Extract JPEG frames (quality=85)
↓
**Stage 3:** Process frames → CSV + DataFrame (visibility metrics)
↓
**Stage 4:** Generate skeleton overlay video + thumbnails
↓
**Output:** 5 files + metadata (accessible via REST API)

**Note:** This documentation reflects only what can be verified from the accessible backend code. The actual MediaPipe processing, frontend integration, and CLI implementation details remain black boxes in this analysis.