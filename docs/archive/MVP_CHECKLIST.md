# MVP Implementation Checklist

## Quick Progress Tracker

### 🔴 Day 1: Environment Setup
- [ ] Create web/ directory structure
- [ ] Set up Python 3.9 venv: `python3.9 -m venv venv_web`
- [ ] Install core deps: `pip install fastapi uvicorn celery redis sqlalchemy`
- [ ] Create docker-compose.yml for local dev
- [ ] Test MediaPipe works: `python -c "import mediapipe"`
- [ ] Set up free service accounts:
  - [ ] Render.com
  - [ ] Railway.app
  - [ ] Neon.tech (PostgreSQL)
  - [ ] Upstash (Redis)
  - [ ] Vercel

### 🟡 Day 2-3: Backend Core

#### Adapt Existing Code
- [ ] Create `web/backend/app/core/video_trimmer.py`
  ```python
  # Import from src/video/frame_extractor.py
  # Add: trim_video_to_15_seconds(input_path, output_path)
  # Add: reduce_resolution_if_needed(video_path, max_width=720)
  ```

- [ ] Create `web/backend/app/core/pose_processor_wrapper.py`
  ```python
  # Import from src/processors/mediapipe_fast_smart.py
  # Add: process_with_progress(frames_dir, job_id, update_callback)
  ```

- [ ] Create `web/backend/app/core/video_generator.py`
  ```python
  # Import from src/video/skeleton_overlay.py
  # Add: generate_web_optimized_video(input_video, pose_csv, output_path)
  ```

#### Database Setup
- [ ] Create `web/backend/app/database/models.py`
- [ ] Create `web/backend/app/database/connection.py`
- [ ] Test database connection

#### API Endpoints
- [ ] Create `web/backend/app/main.py` (FastAPI app)
- [ ] Create upload endpoint: `POST /api/upload`
- [ ] Create status endpoint: `GET /api/jobs/{job_id}`
- [ ] Create download endpoint: `GET /api/download/{job_id}`

#### Celery Worker
- [ ] Create `web/backend/app/workers/celery_app.py`
- [ ] Create main task: `process_video_task(job_id)`
- [ ] Test task execution locally

### 🟢 Day 4-5: Frontend

#### React Setup
- [ ] `npx create-react-app web/frontend`
- [ ] Install deps: `npm install axios tailwindcss`
- [ ] Create basic layout

#### Core Components
- [ ] `VideoUploader.jsx` - Drag & drop upload
- [ ] `QueueStatus.jsx` - Show position in queue
- [ ] `ProgressBar.jsx` - Processing progress
- [ ] `ResultsView.jsx` - Download links

#### API Integration
- [ ] Create `api.js` service class
- [ ] Test upload functionality
- [ ] Test progress polling
- [ ] Test download

### 🔵 Day 6: Integration

#### Docker Setup
- [ ] Create `web/backend/Dockerfile`
- [ ] Create `web/frontend/Dockerfile`
- [ ] Update `docker-compose.yml`
- [ ] Test full stack locally: `docker-compose up`

#### Error Handling
- [ ] Add file size validation (100MB max)
- [ ] Add video format validation
- [ ] Add error messages for common failures
- [ ] Add retry logic for processing

### ⚫ Day 7: Deployment

#### Backend Deployment (Render)
- [ ] Push to GitHub
- [ ] Connect Render to repo
- [ ] Configure environment variables
- [ ] Deploy and test API

#### Worker Deployment (Railway)
- [ ] Connect Railway to repo
- [ ] Add Redis database
- [ ] Configure worker
- [ ] Test processing

#### Frontend Deployment (Vercel)
- [ ] Connect Vercel to repo
- [ ] Configure API endpoint
- [ ] Deploy and test

### ⚪ Day 8-10: Polish & Testing

#### Testing
- [ ] Upload 10 second video → Should work
- [ ] Upload 30 second video → Should trim to 15
- [ ] Upload 200MB video → Should reject
- [ ] Process during interview demo → Should complete in 3 min

#### UI Polish
- [ ] Add loading animations
- [ ] Add sample video links
- [ ] Add "How it works" section
- [ ] Add GitHub/portfolio links
- [ ] Mobile responsive check

#### Performance
- [ ] Test cold start (first request after idle)
- [ ] Optimize Docker image size
- [ ] Add caching where possible
- [ ] Monitor memory usage

## Critical Path Items

### 🚨 Must Work for Demo
1. **Upload** → Can upload video file
2. **Queue** → Shows "Processing 1 of 1"
3. **Progress** → Updates from 0% to 100%
4. **Download** → Can download result video
5. **Error** → Shows clear error if fails

### ⏱️ Time Targets
- Cold start: < 30 seconds
- Processing 15-sec video: < 3 minutes
- Total demo time: < 5 minutes

## Testing Commands

```bash
# Local development
cd web/backend
uvicorn app.main:app --reload

# Test upload
curl -X POST localhost:8000/api/upload \
  -F "file=@test_video.mp4"

# Start worker
celery -A app.workers.celery_app worker --loglevel=info

# Full stack
docker-compose up
```

## Deployment URLs

After deployment, your services will be at:
- Frontend: `https://bodyscript.vercel.app`
- API: `https://bodyscript-api.onrender.com`
- Worker: Railway (no public URL)

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| MediaPipe import error | Use Python 3.9, not 3.13 |
| Redis connection failed | Check REDIS_URL env var |
| Render sleeping | Add wake-up message in UI |
| Out of memory | Reduce frame extraction FPS |
| Slow processing | Use 'fast' mode, not 'quality' |

## Success Metrics

### Minimum Viable
- [x] Processes a video
- [x] Shows progress
- [x] Returns result
- [x] Handles errors
- [x] Free hosting

### Nice to Have
- [ ] Beautiful UI
- [ ] Multiple videos queued
- [ ] History of processed videos
- [ ] Share results link

---

## Daily Standup Template

**Day X Completed:**
- ✅ Task 1
- ✅ Task 2
- ⚠️ Blocked on: [issue]

**Day X+1 Plan:**
- 🎯 Priority 1
- 🎯 Priority 2

**Current Status:** X% complete

---

💡 **Remember:** This is for portfolio. It needs to WORK during live demo, not be perfect.