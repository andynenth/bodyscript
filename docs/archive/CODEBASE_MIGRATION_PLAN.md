# BodyScript Codebase Migration Plan for Web MVP

## Executive Summary
This plan maps existing code to the new web service architecture, maintaining all working functionality while adding web-specific features. Current code processes 636 frames in 43.7 seconds with 95.93% quality - this will be preserved.

## 1. Current Codebase Analysis

### ✅ Assets We Have
```yaml
Processing Core:
  - mediapipe_fast_smart.py: Main processor (4 modes: ultra_fast/fast/smart/quality)
  - frame_extractor.py: Video → frames conversion
  - skeleton_overlay.py: Creates output videos with pose overlay

Web Foundation:
  - creative/web/app.py: Existing FastAPI structure (needs adaptation)

Pipelines:
  - run_mediapipe_fast.sh: Complete processing pipeline (reference)

Supporting:
  - core/: Config, data export, video loading utilities
  - research/: Advanced features (holistic detection)
```

### ⚠️ What's Missing for Web Service
```yaml
Required New Components:
  - Video trimming to 15 seconds
  - Job queue management (Celery)
  - Database models (SQLAlchemy)
  - Progress tracking (WebSocket)
  - Error recovery system
  - File cleanup automation
  - User upload limits
```

## 2. Code Adaptation Requirements

### 📁 File-by-File Migration Tasks

#### A. Core Processing (`src/processors/mediapipe_fast_smart.py`)

**Current State:**
```python
def process_video_fast(self, frames_dir, output_csv, max_frames=None):
    # Synchronous processing
    # Direct file I/O
    # No progress callbacks
```

**Required Changes:**
```python
# [ ] Add async wrapper for Celery
# [ ] Add progress callback mechanism
# [ ] Add error handling and recovery
# [ ] Add memory-efficient streaming for large videos
# [ ] Add job_id tracking throughout
```

**New File:** `web/backend/app/workers/tasks/process_video_task.py`
```python
@celery.task(bind=True)
def process_video_task(self, job_id: str, video_path: str, mode: str = 'smart'):
    # Wrapper around existing MediaPipeFastSmart
    # Adds progress updates to database
    # Handles errors gracefully
```

#### B. Frame Extraction (`src/video/frame_extractor.py`)

**Current State:**
```python
def extract_frames(video_path: str, output_dir: str, ...):
    # Extracts all frames
    # No duration limit
```

**Required Changes:**
```python
# [ ] Add max_duration parameter (15 seconds)
# [ ] Add automatic video trimming with ffmpeg
# [ ] Add frame count estimation for progress
# [ ] Add lower resolution option for web (720p max)
# [ ] Add cleanup of old frames
```

**New File:** `web/backend/app/core/video_processor.py`
```python
async def prepare_video_for_web(video_path: str, job_id: str):
    # Trim to 15 seconds
    # Reduce resolution if needed
    # Extract frames
    # Return frame count for progress tracking
```

#### C. Skeleton Overlay (`src/video/skeleton_overlay.py`)

**Current State:**
```python
# Creates full quality output
# No web optimization
```

**Required Changes:**
```python
# [ ] Add web-optimized output (lower bitrate)
# [ ] Add thumbnail generation
# [ ] Add preview clip (5 seconds)
# [ ] Add watermark option (portfolio branding)
```

#### D. Web API (`creative/web/app.py`)

**Current State:**
```python
# Basic FastAPI structure
# No queue system
# No database
```

**Complete Rewrite Needed:**
```python
# [ ] Integrate with Celery queue
# [ ] Add database models
# [ ] Add WebSocket endpoints
# [ ] Add file size/duration validation
# [ ] Add rate limiting
# [ ] Add health check endpoint
```

## 3. Migration Checklist

### Phase 1: Environment Setup (Day 1)
- [ ] Create `web/` directory structure
- [ ] Set up Python 3.9 virtual environment
- [ ] Install dependencies: `pip install fastapi celery redis sqlalchemy`
- [ ] Set up Docker Compose for local development
- [ ] Test MediaPipe installation works

### Phase 2: Core Adaptation (Day 2-3)

#### Video Processing Pipeline
- [ ] Create `web/backend/app/core/video_processor.py`
  - [ ] Import existing `frame_extractor.py` functionality
  - [ ] Add 15-second trimming with ffmpeg
  - [ ] Add resolution check (max 720p)
  - [ ] Test with sample videos

#### Pose Processing Wrapper
- [ ] Create `web/backend/app/core/pose_processor.py`
  - [ ] Import `MediaPipeFastSmart` class
  - [ ] Add progress callback system
  - [ ] Add error recovery (retry failed frames)
  - [ ] Add memory monitoring

#### Output Generation
- [ ] Create `web/backend/app/core/output_generator.py`
  - [ ] Import `skeleton_overlay.py` functionality
  - [ ] Add web-optimized video encoding
  - [ ] Add thumbnail generation
  - [ ] Add CSV formatting for download

### Phase 3: Web Service Layer (Day 4-5)

#### Database Models
- [ ] Create `web/backend/app/database/models.py`
  ```python
  class Job:
      id: str (UUID)
      status: str  # pending, processing, completed, failed
      input_filename: str
      video_duration: float
      frames_total: int
      frames_processed: int
      processing_mode: str
      error_message: str
      created_at: datetime
      completed_at: datetime
  ```

#### API Endpoints
- [ ] Create `web/backend/app/api/routes/upload.py`
  - [ ] POST `/api/upload` - Handle video upload
  - [ ] Validate file type (mp4, mov, avi)
  - [ ] Check file size (<100MB)
  - [ ] Create job record
  - [ ] Queue processing task

- [ ] Create `web/backend/app/api/routes/status.py`
  - [ ] GET `/api/jobs/{job_id}` - Get job status
  - [ ] GET `/api/jobs/{job_id}/progress` - Get detailed progress
  - [ ] WebSocket `/ws/progress/{job_id}` - Real-time updates

- [ ] Create `web/backend/app/api/routes/download.py`
  - [ ] GET `/api/download/{job_id}/video` - Download result video
  - [ ] GET `/api/download/{job_id}/csv` - Download pose data
  - [ ] GET `/api/download/{job_id}/preview` - Get thumbnail

#### Celery Tasks
- [ ] Create `web/backend/app/workers/celery_app.py`
  - [ ] Configure Celery with Redis
  - [ ] Set up task routing
  - [ ] Configure retry policy

- [ ] Create `web/backend/app/workers/tasks/process_video.py`
  ```python
  @celery.task(bind=True, max_retries=3)
  def process_video(self, job_id: str):
      # 1. Download from S3/storage
      # 2. Trim to 15 seconds
      # 3. Extract frames
      # 4. Process with MediaPipe
      # 5. Generate output video
      # 6. Upload results
      # 7. Update job status
      # 8. Clean up temp files
  ```

### Phase 4: Frontend Integration (Day 6-7)

#### React Components
- [ ] Create `web/frontend/src/components/VideoUploader.jsx`
  - [ ] Drag-and-drop interface
  - [ ] File validation
  - [ ] Upload progress bar
  - [ ] 15-second limit warning

- [ ] Create `web/frontend/src/components/ProcessingStatus.jsx`
  - [ ] Queue position indicator
  - [ ] Processing progress bar
  - [ ] Estimated time remaining
  - [ ] Error display

- [ ] Create `web/frontend/src/components/ResultsViewer.jsx`
  - [ ] Video player for result
  - [ ] Download buttons
  - [ ] Share link generator
  - [ ] Processing stats display

#### API Client
- [ ] Create `web/frontend/src/services/api.js`
  ```javascript
  class BodyScriptAPI {
    async uploadVideo(file) { }
    async getJobStatus(jobId) { }
    async downloadResult(jobId, type) { }
    connectWebSocket(jobId, onProgress) { }
  }
  ```

### Phase 5: Deployment Setup (Day 8)

#### Docker Configuration
- [ ] Create `web/backend/Dockerfile`
  ```dockerfile
  FROM python:3.9-slim
  # Install system dependencies
  RUN apt-get update && apt-get install -y ffmpeg
  # Copy and install Python deps
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  # Copy application
  COPY . /app
  WORKDIR /app
  ```

- [ ] Create `docker-compose.yml`
  ```yaml
  services:
    redis:
      image: redis:7-alpine

    api:
      build: ./web/backend
      command: uvicorn app.main:app --host 0.0.0.0
      environment:
        - REDIS_URL=redis://redis:6379

    worker:
      build: ./web/backend
      command: celery -A app.workers.celery_app worker
      environment:
        - REDIS_URL=redis://redis:6379

    frontend:
      build: ./web/frontend
      ports:
        - "3000:3000"
  ```

#### Free Service Deployment
- [ ] Deploy backend to Render.com
  - [ ] Connect GitHub repo
  - [ ] Set build command: `pip install -r requirements.txt`
  - [ ] Set start command: `uvicorn app.main:app`

- [ ] Deploy worker to Railway.app
  - [ ] Set up Redis add-on
  - [ ] Configure Celery worker

- [ ] Deploy frontend to Vercel
  - [ ] Connect GitHub repo
  - [ ] Set build settings for React

### Phase 6: Testing & Polish (Day 9-10)

#### Functionality Tests
- [ ] Test video upload (various formats)
- [ ] Test 15-second trimming
- [ ] Test processing modes (fast/smart)
- [ ] Test progress tracking
- [ ] Test error handling
- [ ] Test file cleanup
- [ ] Test concurrent users

#### Performance Tests
- [ ] Measure cold start time
- [ ] Measure processing speed
- [ ] Check memory usage
- [ ] Monitor Redis queue
- [ ] Test with 100MB video

#### User Experience
- [ ] Add loading animations
- [ ] Add helpful error messages
- [ ] Add sample videos
- [ ] Add "How it works" section
- [ ] Add GitHub link
- [ ] Add portfolio branding

## 4. Code Reuse Mapping

| Existing File | Web Service Component | Modifications Needed |
|--------------|----------------------|---------------------|
| `mediapipe_fast_smart.py` | Core processor | Add progress callbacks |
| `frame_extractor.py` | Video prep | Add 15-sec trim |
| `skeleton_overlay.py` | Output generator | Add web optimization |
| `run_mediapipe_fast.sh` | Reference for flow | Convert to Python tasks |
| `creative/web/app.py` | API structure | Major refactor needed |

## 5. Risk Mitigation

### Technical Risks
| Risk | Mitigation |
|------|------------|
| MediaPipe failures | Implement retry logic, fallback to CPU mode |
| Memory overflow | Stream process frames, limit to 720p |
| Slow processing | Show accurate progress, set expectations |
| Storage fills up | Auto-cleanup after 1 hour |
| Service sleeping | Show "Waking up..." message |

## 6. Success Metrics

### MVP Must-Haves
- [x] Processes 15-second videos
- [x] Shows queue position
- [x] Real-time progress updates
- [x] Downloads results
- [x] Handles errors gracefully
- [x] Works on free tier services
- [x] Costs < $1/month

### Nice-to-Haves
- [ ] Multiple processing modes
- [ ] Batch upload
- [ ] Result history
- [ ] Social sharing
- [ ] API documentation

## 7. File Structure After Migration

```
bodyscript/
├── src/                    # Existing processing code
│   ├── processors/         # MediaPipe processors
│   └── video/             # Video utilities
│
├── web/                   # NEW: Web application
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/       # FastAPI routes
│   │   │   ├── core/      # Adapted processors
│   │   │   ├── database/  # Models
│   │   │   └── workers/   # Celery tasks
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── frontend/
│       ├── src/
│       │   ├── components/ # React components
│       │   └── services/   # API client
│       └── package.json
│
└── docker-compose.yml     # Local development
```

## 8. Command Reference

### Development Commands
```bash
# Start local development
docker-compose up

# Run processing test
python -m web.backend.app.workers.tasks.process_video test_job_123

# Test API endpoint
curl -X POST localhost:8000/api/upload -F "file=@test.mp4"

# Monitor Celery
celery -A web.backend.app.workers.celery_app flower
```

### Deployment Commands
```bash
# Deploy to Render (backend)
git push render main

# Deploy to Vercel (frontend)
vercel --prod

# Check logs
render logs --tail
railway logs
```

## 9. Timeline Summary

| Day | Tasks | Deliverable |
|-----|-------|------------|
| 1 | Environment setup | Docker running locally |
| 2-3 | Core adaptation | Processing works via CLI |
| 4-5 | Web service layer | API endpoints working |
| 6-7 | Frontend | Full UI functional |
| 8 | Deployment | Live on free services |
| 9-10 | Testing & polish | Portfolio-ready |

## 10. Next Steps

1. **Immediate:** Set up development environment
2. **Tomorrow:** Start core adaptation
3. **This week:** Complete MVP
4. **Next week:** Deploy and test with real users

---

**Success Criteria:** When a recruiter can upload a 15-second video during your interview and see it processed live with pose detection overlay within 2-3 minutes.