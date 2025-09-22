# BodyScript Complete Implementation Plan
## Gallery + Storage + Deployment with Free Tier Focus

**Total Budget: $0/month** (using free tiers)
**Timeline: 2-3 days**
**Architecture: Vercel (Frontend) + Render (Backend) + Cloudflare R2 (Storage)**

---

## Phase 1: Storage Setup with Cloudflare R2 (Day 1 Morning)

### 1.1 Create Cloudflare Account & R2 Bucket
- [ ] Sign up for Cloudflare account at https://cloudflare.com
- [ ] Navigate to R2 Storage in dashboard
- [ ] Create new bucket named `bodyscript-gallery`
- [ ] Configure bucket settings:
  - [ ] Location: Automatic
  - [ ] Storage Class: Standard
  - [ ] Public access: Enabled for gallery bucket
- [ ] Create second bucket `bodyscript-uploads` for user submissions
- [ ] Generate API tokens:
  - [ ] Go to R2 → Manage R2 API Tokens
  - [ ] Create token with Edit permissions
  - [ ] Save credentials:
    ```
    Account ID: _______________
    Access Key ID: _______________
    Secret Access Key: _______________
    Bucket Endpoints: _______________
    ```

### 1.2 Install R2 Dependencies
```bash
# In backend directory
cd backend

# Add to requirements.txt
echo "boto3==1.29.7" >> requirements.txt
echo "python-dotenv==1.0.0" >> requirements.txt

# Install locally for testing
pip install boto3 python-dotenv
```

### 1.3 Create R2 Integration Module
Create `backend/storage_r2.py`:
```python
import boto3
import os
from typing import Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class R2Storage:
    def __init__(self):
        self.account_id = os.getenv('R2_ACCOUNT_ID')
        self.access_key = os.getenv('R2_ACCESS_KEY')
        self.secret_key = os.getenv('R2_SECRET_KEY')

        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='auto'
        )

        self.upload_bucket = 'bodyscript-uploads'
        self.gallery_bucket = 'bodyscript-gallery'

    def upload_file(self, local_path: str, remote_path: str,
                   bucket: str = None) -> str:
        """Upload file to R2 and return public URL"""
        bucket = bucket or self.upload_bucket
        self.s3_client.upload_file(local_path, bucket, remote_path)

        # Return public URL
        if bucket == self.gallery_bucket:
            return f"https://gallery.bodyscript.com/{remote_path}"
        else:
            # Generate signed URL for uploads (expires in 7 days)
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': remote_path},
                ExpiresIn=604800  # 7 days
            )

    def copy_to_gallery(self, job_id: str, display_name: str) -> dict:
        """Copy from uploads to gallery with new name"""
        # Copy all files for this job
        files = ['thumbnail.jpg', 'preview.mp4', 'full.mp4', 'metadata.json']
        urls = {}

        for file in files:
            source = f"{self.upload_bucket}/{job_id}/{file}"
            dest_name = file.replace('.', f'_{display_name}.')
            dest = f"gallery/{display_name}/{dest_name}"

            self.s3_client.copy_object(
                CopySource=source,
                Bucket=self.gallery_bucket,
                Key=dest
            )

            urls[file.split('.')[0]] = f"https://gallery.bodyscript.com/{dest}"

        return urls

    def delete_upload(self, job_id: str):
        """Delete files from upload bucket"""
        # List and delete all objects with job_id prefix
        response = self.s3_client.list_objects_v2(
            Bucket=self.upload_bucket,
            Prefix=f"{job_id}/"
        )

        if 'Contents' in response:
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            self.s3_client.delete_objects(
                Bucket=self.upload_bucket,
                Delete={'Objects': objects}
            )

r2_storage = R2Storage()
```

### 1.4 Create Environment File
Create `backend/.env`:
```bash
# R2 Storage Configuration
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY=your_access_key_here
R2_SECRET_KEY=your_secret_key_here

# Public URLs (update after R2 setup)
R2_PUBLIC_DOMAIN=https://gallery.bodyscript.com

# Environment
ENVIRONMENT=development
```

---

## Phase 2: Backend Video Processing Updates (Day 1 Afternoon)

### 2.1 Add Thumbnail & Preview Generation
Create `backend/video_utils.py`:
```python
import subprocess
import cv2
from pathlib import Path
from typing import Tuple

def generate_thumbnail(video_path: str, output_path: str,
                       size: Tuple[int, int] = (405, 720)) -> bool:
    """Generate thumbnail from first frame"""
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        if ret:
            # Resize maintaining aspect ratio
            resized = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
            cv2.imwrite(output_path, resized)
            cap.release()
            return True
        cap.release()
        return False
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return False

def generate_preview(video_path: str, output_path: str,
                    duration: int = 3, quality: str = "low") -> bool:
    """Generate preview video (3-5 seconds, low quality)"""
    try:
        # Use ffmpeg for better control
        cmd = [
            "ffmpeg", "-i", video_path,
            "-t", str(duration),  # Duration
            "-vf", "scale=360:-1",  # 360p height
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "28",  # Lower quality for smaller size
            "-an",  # No audio
            "-y",  # Overwrite
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Preview generation failed: {e}")
        return False

def get_video_metadata(video_path: str) -> dict:
    """Extract video metadata"""
    cap = cv2.VideoCapture(video_path)
    metadata = {
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
    }
    cap.release()
    return metadata
```

### 2.2 Update Process Wrapper
Update `backend/process_wrapper.py`:
```python
# Add imports
from video_utils import generate_thumbnail, generate_preview, get_video_metadata
from storage_r2 import r2_storage
import json

# Add to process_video method after skeleton video creation:
def process_video(self, ...):
    # ... existing processing code ...

    # After creating skeleton video (around line 180)
    # Generate thumbnail and preview
    thumbnail_path = str(job_dir / "thumbnail.jpg")
    preview_path = str(job_dir / "preview.mp4")

    if progress_callback:
        progress_callback(85, "Generating thumbnail and preview...")

    generate_thumbnail(output_video, thumbnail_path)
    generate_preview(output_video, preview_path, duration=3)

    # Upload to R2
    if progress_callback:
        progress_callback(90, "Uploading to cloud storage...")

    # Upload all files to R2
    urls = {
        'thumbnail': r2_storage.upload_file(
            thumbnail_path,
            f"{job_id}/thumbnail.jpg"
        ),
        'preview': r2_storage.upload_file(
            preview_path,
            f"{job_id}/preview.mp4"
        ),
        'full': r2_storage.upload_file(
            output_video,
            f"{job_id}/full.mp4"
        ),
        'csv': r2_storage.upload_file(
            csv_path,
            f"{job_id}/pose_data.csv"
        )
    }

    # Save metadata
    metadata = {
        'job_id': job_id,
        'processed_at': datetime.now().isoformat(),
        'statistics': statistics,
        'urls': urls,
        'video_info': get_video_metadata(output_video)
    }

    metadata_path = str(job_dir / "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    r2_storage.upload_file(
        metadata_path,
        f"{job_id}/metadata.json"
    )

    # Update return to include URLs
    return {
        'success': True,
        'job_id': job_id,
        'urls': urls,  # Add this
        'output_video': output_video,  # Keep for backward compatibility
        'pose_data_csv': csv_path,
        'statistics': statistics
    }
```

### 2.3 Add Admin Endpoints
Create `backend/admin_routes.py`:
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from storage_r2 import r2_storage
import boto3

router = APIRouter(prefix="/admin", tags=["admin"])

# Simple auth for admin (improve this in production)
def verify_admin(token: str):
    if token != os.getenv('ADMIN_TOKEN', 'your-secret-admin-token'):
        raise HTTPException(status_code=403, detail="Not authorized")
    return True

@router.get("/pending-videos")
async def list_pending_videos(auth: str = Depends(verify_admin)):
    """List all videos in upload bucket for review"""
    client = r2_storage.s3_client

    response = client.list_objects_v2(
        Bucket=r2_storage.upload_bucket,
        Delimiter='/',
        Prefix=''
    )

    videos = []
    if 'CommonPrefixes' in response:
        for prefix in response['CommonPrefixes']:
            job_id = prefix['Prefix'].rstrip('/')

            # Get metadata
            try:
                metadata_obj = client.get_object(
                    Bucket=r2_storage.upload_bucket,
                    Key=f"{job_id}/metadata.json"
                )
                metadata = json.loads(metadata_obj['Body'].read())

                videos.append({
                    'job_id': job_id,
                    'processed_at': metadata.get('processed_at'),
                    'detection_rate': metadata['statistics'].get('detection_rate'),
                    'preview_url': metadata['urls'].get('preview'),
                    'thumbnail_url': metadata['urls'].get('thumbnail')
                })
            except:
                continue

    return {'videos': sorted(videos, key=lambda x: x['processed_at'], reverse=True)}

@router.post("/approve-to-gallery")
async def approve_to_gallery(
    job_id: str,
    display_name: str,
    category: str,
    auth: str = Depends(verify_admin)
):
    """Copy video from uploads to gallery"""
    try:
        # Copy to gallery
        urls = r2_storage.copy_to_gallery(job_id, display_name)

        # Update gallery JSON
        await update_gallery_json({
            'id': display_name,
            'title': display_name.replace('-', ' ').title(),
            'category': category,
            'thumbnail': urls['thumbnail'],
            'preview': urls['preview'],
            'full': urls['full'],
            'added_at': datetime.now().isoformat()
        })

        # Delete from uploads
        r2_storage.delete_upload(job_id)

        return {'success': True, 'gallery_urls': urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reject-video/{job_id}")
async def reject_video(job_id: str, auth: str = Depends(verify_admin)):
    """Delete video from uploads"""
    try:
        r2_storage.delete_upload(job_id)
        return {'success': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_gallery_json(video_data: dict):
    """Update the gallery JSON file"""
    # Download current gallery.json
    try:
        obj = r2_storage.s3_client.get_object(
            Bucket=r2_storage.gallery_bucket,
            Key='gallery.json'
        )
        gallery = json.loads(obj['Body'].read())
    except:
        gallery = {'videos': []}

    # Add new video
    gallery['videos'].insert(0, video_data)

    # Keep only latest 50 videos
    gallery['videos'] = gallery['videos'][:50]

    # Upload updated gallery.json
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        json.dump(gallery, f, indent=2)
        f.flush()
        r2_storage.s3_client.upload_file(
            f.name,
            r2_storage.gallery_bucket,
            'gallery.json'
        )
```

### 2.4 Update Main App
Update `backend/app.py`:
```python
# Add imports
from admin_routes import router as admin_router
import time

# Add startup time for uptime tracking
START_TIME = time.time()

# Include admin router
app.include_router(admin_router)

# Enhanced health check
@app.get("/health")
async def health_check():
    """Enhanced health check with uptime and cold start warning"""
    uptime = time.time() - START_TIME
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime,
        "cold_start": uptime < 60,  # True if just started
        "free_tier_note": "Server may sleep after 15 min inactivity",
        "service": "bodyscript-api"
    }

# Pre-load heavy libraries at startup
@app.on_event("startup")
async def startup_event():
    """Pre-load heavy libraries to reduce cold start time"""
    import mediapipe
    import cv2
    import pandas
    print("Heavy libraries loaded, ready to serve")
```

---

## Phase 3: Frontend Gallery Updates (Day 1 Evening)

### 3.1 Create Configuration Module
Create `frontend/config.js`:
```javascript
// Dynamic configuration for different environments
const Config = {
  getApiUrl: () => {
    if (window.location.hostname === 'localhost') {
      return 'http://localhost:8000';
    }
    // Production URL (update after Render deployment)
    return 'https://bodyscript-api.onrender.com';
  },

  getGalleryDataUrl: () => {
    // R2 public URL for gallery JSON
    return 'https://gallery.bodyscript.com/gallery.json';
  },

  // Keep-alive configuration
  keepAlive: {
    enabled: !window.location.hostname.includes('localhost'),
    interval: 600000  // 10 minutes
  },

  // Wake-up message configuration
  wakeUpMessage: {
    enabled: true,
    timeout: 65000,  // 65 seconds
    message: '⏳ Waking up server (free tier may take 30-60 seconds)...'
  }
};

// Set global API URL
window.API_URL = Config.getApiUrl();

// Initialize keep-alive if enabled
if (Config.keepAlive.enabled) {
  setInterval(() => {
    fetch(`${window.API_URL}/health`)
      .catch(() => {}); // Ignore errors silently
  }, Config.keepAlive.interval);
}
```

### 3.2 Update Gallery JavaScript
Update `frontend/assets/gallery-common.js`:
```javascript
// Replace sample data with real gallery loader
let GALLERY_VIDEOS = [];
let isLoading = true;

// Load gallery data from R2
async function loadGalleryData() {
  try {
    const response = await fetch('https://gallery.bodyscript.com/gallery.json');
    if (response.ok) {
      const data = await response.json();
      GALLERY_VIDEOS = data.videos;
      renderGallery();
    } else {
      // Fallback to sample data if gallery.json doesn't exist yet
      console.warn('Gallery data not found, using samples');
      GALLERY_VIDEOS = SAMPLE_VIDEOS;
      renderGallery();
    }
  } catch (error) {
    console.error('Failed to load gallery:', error);
    GALLERY_VIDEOS = SAMPLE_VIDEOS;
    renderGallery();
  } finally {
    isLoading = false;
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  loadGalleryData();
  initializeGallery();
});

// Show loading state
function showLoading() {
  const grid = document.getElementById('videoGrid');
  grid.innerHTML = '<div class="terminal-loading">Loading gallery<span class="loading-dots"></span></div>';
}

// Update the render function to use real data
function renderGallery() {
  const grid = document.getElementById('videoGrid');
  grid.innerHTML = '';

  if (isLoading) {
    showLoading();
    return;
  }

  if (GALLERY_VIDEOS.length === 0) {
    grid.innerHTML = '<div class="no-videos">No videos in gallery yet. Upload and process a video to get started!</div>';
    return;
  }

  // Render actual videos
  GalleryCommon.currentVideos.forEach(video => {
    // ... existing rendering code but with real URLs ...
  });
}
```

### 3.3 Update Upload Page
Update `frontend/upload.html`:
```html
<!-- Add to head section -->
<script src="config.js"></script>

<!-- Update the script section -->
<script>
  // Check API health on load with wake-up message
  async function checkAPIHealth() {
    const terminalOutput = document.getElementById('terminalOutput');

    // Show wake-up message if configured
    if (Config.wakeUpMessage.enabled) {
      addOutputLine(Config.wakeUpMessage.message, 'warning');
    }

    try {
      const response = await fetch(`${window.API_URL}/health`, {
        signal: AbortSignal.timeout(Config.wakeUpMessage.timeout)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.cold_start) {
          addOutputLine('[OK] Server starting up (cold start detected)', 'warning');
        } else {
          addOutputLine('[OK] API Connected and ready', 'success');
        }
      }
    } catch (error) {
      if (error.name === 'AbortSignal.timeout' || error.name === 'TimeoutError') {
        addOutputLine('[ERROR] Server is taking too long. Please refresh the page.', 'error');
      } else {
        addOutputLine('[WARNING] Server may be sleeping. First request will wake it up.', 'warning');
      }
    }
  }

  // Call on page load
  window.addEventListener('DOMContentLoaded', () => {
    checkAPIHealth();
  });

  // Update process video to use real API
  async function processVideo() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Show processing animation
      document.getElementById('processingAnimation').classList.add('show');

      const response = await fetch(`${window.API_URL}/api/upload`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();

        // Poll for status
        pollJobStatus(result.job_id);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      addOutputLine(`[ERROR] ${error.message}`, 'error');
    }
  }

  async function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${window.API_URL}/api/status/${jobId}`);
        const status = await response.json();

        updateProgressBar(status.progress);

        if (status.status === 'completed') {
          clearInterval(interval);
          showResults(status);
        } else if (status.status === 'failed') {
          clearInterval(interval);
          addOutputLine('[ERROR] Processing failed', 'error');
        }
      } catch (error) {
        console.error('Status poll error:', error);
      }
    }, 1000);
  }
</script>
```

### 3.4 Create Admin Interface
Create `frontend/admin.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BodyScript Admin - Gallery Curation</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'JetBrains Mono', monospace;
      background: #0a0a0a;
      color: #27c93f;
      padding: 2rem;
    }
    .admin-header {
      text-align: center;
      margin-bottom: 2rem;
    }
    .pending-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 2rem;
    }
    .video-card {
      background: #1e1e1e;
      border: 1px solid #333;
      padding: 1rem;
      border-radius: 8px;
    }
    .video-preview {
      width: 100%;
      height: 200px;
      object-fit: cover;
      margin-bottom: 1rem;
    }
    .video-stats {
      color: #999;
      font-size: 0.9rem;
      margin: 0.5rem 0;
    }
    .actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }
    .btn {
      padding: 0.5rem 1rem;
      border: 1px solid #27c93f;
      background: transparent;
      color: #27c93f;
      cursor: pointer;
      font-family: inherit;
    }
    .btn:hover {
      background: #27c93f;
      color: #000;
    }
    .btn.reject {
      border-color: #ff5f56;
      color: #ff5f56;
    }
    .btn.reject:hover {
      background: #ff5f56;
    }
    .auth-form {
      max-width: 400px;
      margin: 0 auto;
      padding: 2rem;
      background: #1e1e1e;
      border: 1px solid #333;
      border-radius: 8px;
    }
    .auth-input {
      width: 100%;
      padding: 0.5rem;
      background: #000;
      border: 1px solid #333;
      color: #27c93f;
      font-family: inherit;
      margin-bottom: 1rem;
    }
  </style>
</head>
<body>
  <div class="admin-header">
    <h1>BodyScript Admin</h1>
    <p>Gallery Curation Dashboard</p>
  </div>

  <!-- Auth Form -->
  <div id="authForm" class="auth-form">
    <h2>Admin Login</h2>
    <input type="password" id="adminToken" class="auth-input" placeholder="Enter admin token">
    <button class="btn" onclick="authenticate()">Login</button>
  </div>

  <!-- Pending Videos Grid -->
  <div id="pendingVideos" class="pending-grid" style="display: none;">
    <!-- Videos loaded here -->
  </div>

  <script src="config.js"></script>
  <script>
    let adminToken = '';

    async function authenticate() {
      adminToken = document.getElementById('adminToken').value;

      try {
        const response = await fetch(`${window.API_URL}/admin/pending-videos?auth=${adminToken}`);
        if (response.ok) {
          document.getElementById('authForm').style.display = 'none';
          document.getElementById('pendingVideos').style.display = 'grid';
          loadPendingVideos();
        } else {
          alert('Invalid admin token');
        }
      } catch (error) {
        alert('Failed to authenticate');
      }
    }

    async function loadPendingVideos() {
      try {
        const response = await fetch(`${window.API_URL}/admin/pending-videos?auth=${adminToken}`);
        const data = await response.json();

        const grid = document.getElementById('pendingVideos');
        grid.innerHTML = '';

        if (data.videos.length === 0) {
          grid.innerHTML = '<p>No pending videos for review</p>';
          return;
        }

        data.videos.forEach(video => {
          const card = document.createElement('div');
          card.className = 'video-card';
          card.innerHTML = `
            <video src="${video.preview_url}" class="video-preview" controls></video>
            <div class="video-stats">Job ID: ${video.job_id}</div>
            <div class="video-stats">Detection: ${(video.detection_rate * 100).toFixed(1)}%</div>
            <div class="video-stats">Processed: ${new Date(video.processed_at).toLocaleDateString()}</div>

            <input type="text" id="name_${video.job_id}" placeholder="Display name (e.g., dance-performance-1)" class="auth-input">
            <select id="category_${video.job_id}" class="auth-input">
              <option value="dance">Dance</option>
              <option value="sports">Sports</option>
              <option value="yoga">Yoga</option>
              <option value="martial">Martial Arts</option>
            </select>

            <div class="actions">
              <button class="btn" onclick="approveVideo('${video.job_id}')">Approve to Gallery</button>
              <button class="btn reject" onclick="rejectVideo('${video.job_id}')">Reject</button>
            </div>
          `;
          grid.appendChild(card);
        });
      } catch (error) {
        console.error('Failed to load videos:', error);
      }
    }

    async function approveVideo(jobId) {
      const displayName = document.getElementById(`name_${jobId}`).value;
      const category = document.getElementById(`category_${jobId}`).value;

      if (!displayName) {
        alert('Please enter a display name');
        return;
      }

      try {
        const response = await fetch(`${window.API_URL}/admin/approve-to-gallery`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            job_id: jobId,
            display_name: displayName,
            category: category
          })
        });

        if (response.ok) {
          alert('Video added to gallery!');
          loadPendingVideos();
        }
      } catch (error) {
        alert('Failed to approve video');
      }
    }

    async function rejectVideo(jobId) {
      if (!confirm('Delete this video?')) return;

      try {
        const response = await fetch(`${window.API_URL}/admin/reject-video/${jobId}?auth=${adminToken}`, {
          method: 'DELETE'
        });

        if (response.ok) {
          loadPendingVideos();
        }
      } catch (error) {
        alert('Failed to reject video');
      }
    }
  </script>
</body>
</html>
```

---

## Phase 4: Deployment Configuration (Day 2 Morning)

### 4.1 Prepare for Deployment

#### Create GitHub Repository
- [ ] Initialize git if not already done
- [ ] Create `.gitignore`:
  ```
  __pycache__/
  *.pyc
  .env
  venv/
  temp/
  *.mp4
  *.jpg
  *.csv
  node_modules/
  .DS_Store
  ```
- [ ] Create repository on GitHub
- [ ] Push code:
  ```bash
  git add .
  git commit -m "Initial deployment setup"
  git remote add origin https://github.com/YOUR_USERNAME/bodyscript.git
  git push -u origin main
  ```

### 4.2 Backend Deployment Files

#### Create `backend/render.yaml`:
```yaml
services:
  - type: web
    name: bodyscript-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.8
      - key: R2_ACCOUNT_ID
        sync: false  # Add manually in dashboard
      - key: R2_ACCESS_KEY
        sync: false
      - key: R2_SECRET_KEY
        sync: false
      - key: ADMIN_TOKEN
        sync: false
```

#### Create `backend/runtime.txt`:
```
python-3.11.8
```

#### Update `backend/requirements.txt`:
```
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1

# Processing
opencv-python-headless==4.8.1
mediapipe==0.10.7
pandas==2.1.3
numpy==1.24.3

# Storage
boto3==1.29.7
python-dotenv==1.0.0

# Utils
Pillow==10.1.0
```

### 4.3 Frontend Deployment Files

#### Create `frontend/vercel.json`:
```json
{
  "name": "bodyscript-frontend",
  "buildCommand": "",
  "outputDirectory": ".",
  "framework": null,
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=3600"
        }
      ]
    }
  ]
}
```

#### Update `frontend/config.js` with production URL:
```javascript
// After backend is deployed, update this URL
return 'https://bodyscript-api.onrender.com';
```

---

## Phase 5: Deploy to Production (Day 2 Afternoon)

### 5.1 Deploy Backend to Render
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Configure:
  - [ ] Name: `bodyscript-api`
  - [ ] Environment: `Python 3`
  - [ ] Region: `Oregon (US West)`
  - [ ] Branch: `main`
  - [ ] Root Directory: `backend`
  - [ ] Build Command: `pip install -r requirements.txt`
  - [ ] Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- [ ] Add Environment Variables:
  - [ ] `PYTHON_VERSION` = `3.11.8`
  - [ ] `R2_ACCOUNT_ID` = (your R2 account ID)
  - [ ] `R2_ACCESS_KEY` = (your R2 access key)
  - [ ] `R2_SECRET_KEY` = (your R2 secret key)
  - [ ] `ADMIN_TOKEN` = (create secure admin token)
  - [ ] `ENVIRONMENT` = `production`
- [ ] Select **Free Plan**
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (5-10 minutes)
- [ ] Test: `https://bodyscript-api.onrender.com/health`

### 5.2 Deploy Frontend to Vercel
- [ ] Install Vercel CLI: `npm install -g vercel`
- [ ] In frontend directory:
  ```bash
  cd frontend
  vercel
  ```
- [ ] Follow prompts:
  - [ ] Set up and deploy: Y
  - [ ] Scope: Your account
  - [ ] Link to existing project: N
  - [ ] Project name: `bodyscript-frontend`
  - [ ] Directory: `./`
  - [ ] Build command: (leave blank)
  - [ ] Output directory: (leave blank)
- [ ] Get production URL (e.g., `https://bodyscript-frontend.vercel.app`)

### 5.3 Update CORS Settings
- [ ] Edit `backend/app.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "https://bodyscript-frontend.vercel.app",
          "http://localhost:3000",
          "http://localhost:8000"
      ],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- [ ] Commit and push:
  ```bash
  git add backend/app.py
  git commit -m "Update CORS for production"
  git push origin main
  ```
- [ ] Render will auto-deploy

### 5.4 Configure R2 Public Access
- [ ] Go to Cloudflare R2 dashboard
- [ ] Click on `bodyscript-gallery` bucket
- [ ] Settings → Public Access
- [ ] Enable public access
- [ ] Add custom domain (optional):
  - [ ] Add CNAME: `gallery.yourdomain.com` → `pub-xxx.r2.dev`
  - [ ] Update URLs in code

---

## Phase 6: Testing & Validation (Day 2 Evening)

### 6.1 Test Complete Flow
- [ ] Open frontend: `https://bodyscript-frontend.vercel.app`
- [ ] Check API health indicator
- [ ] Upload test video (< 5MB)
- [ ] Monitor processing
- [ ] Check video appears in R2 uploads bucket
- [ ] Access admin panel: `/admin.html`
- [ ] Approve video to gallery
- [ ] Verify gallery displays video

### 6.2 Performance Testing
- [ ] Test cold start time (first request after 15 min)
- [ ] Verify keep-alive prevents sleeping
- [ ] Check thumbnail/preview generation
- [ ] Test download speeds from R2

### 6.3 Error Testing
- [ ] Upload invalid file format
- [ ] Upload oversized file
- [ ] Test network disconnection during upload
- [ ] Verify error messages display correctly

---

## Phase 7: Final Polish (Day 3)

### 7.1 Optimization Checklist
- [ ] Enable Vercel Analytics (free tier)
- [ ] Set up UptimeRobot for monitoring (free)
- [ ] Add robots.txt and sitemap.xml
- [ ] Optimize images with WebP format
- [ ] Enable gzip compression
- [ ] Add Open Graph meta tags

### 7.2 Documentation
- [ ] Update README with production URLs
- [ ] Document API endpoints
- [ ] Create user guide
- [ ] Add troubleshooting section

### 7.3 Backup & Recovery
- [ ] Export R2 bucket list
- [ ] Backup gallery.json regularly
- [ ] Document recovery procedures
- [ ] Set up automated backups (optional)

---

## Cost Analysis

### Monthly Costs (Free Tier)
| Service | Free Tier | Usage | Cost |
|---------|-----------|-------|------|
| Cloudflare R2 | 10GB storage, 10M requests | ~1000 videos | $0 |
| Render | 750 hours, sleeps after 15min | Backend API | $0 |
| Vercel | 100GB bandwidth | Frontend hosting | $0 |
| **Total** | | | **$0/month** |

### When You'll Need to Pay
- R2: Over 10GB storage ($0.015/GB/month after)
- Render: Need always-on ($7/month Starter)
- Vercel: Over 100GB bandwidth ($20/month Pro)

### Scale Estimates
With free tier you can handle:
- ~1000 processed videos stored
- ~100 uploads per day
- ~10,000 gallery views per month

---

## Quick Reference Commands

```bash
# Local Development
cd backend && uvicorn app:app --reload
cd frontend && python -m http.server 3000

# Deploy Backend (auto-deploy on push)
git add backend/
git commit -m "Update backend"
git push origin main

# Deploy Frontend
cd frontend && vercel --prod

# View Logs
# Render: https://dashboard.render.com → Your Service → Logs
# Vercel: https://vercel.com/dashboard → Your Project → Functions

# R2 Management
# Use Cloudflare dashboard or AWS CLI with R2 endpoints

# Test Endpoints
curl https://bodyscript-api.onrender.com/health
curl https://bodyscript-frontend.vercel.app
```

---

## Troubleshooting Guide

### Issue: CORS Error
**Solution**: Update allow_origins in backend/app.py with your frontend URL

### Issue: R2 Upload Fails
**Solution**: Check API credentials and bucket permissions

### Issue: Server Sleeps Too Often
**Solution**: Ensure keep-alive is running in frontend config.js

### Issue: Gallery Not Loading
**Solution**: Check gallery.json exists in R2 and is publicly accessible

### Issue: Admin Panel 403 Error
**Solution**: Verify ADMIN_TOKEN environment variable matches

---

## Success Metrics

✅ **Deployment Complete When:**
- [ ] Frontend loads at Vercel URL
- [ ] Backend responds at `/health`
- [ ] Upload → Process → Review → Gallery flow works
- [ ] Gallery displays curated videos
- [ ] Admin can approve/reject videos
- [ ] Keep-alive prevents excessive sleeping
- [ ] All free tier limits respected

---

## Future Enhancements (After MVP)

1. **User Accounts** - Allow users to see their processing history
2. **Batch Processing** - Process multiple videos at once
3. **WebSocket Progress** - Real-time processing updates
4. **Custom Domains** - Add your own domain names
5. **Email Notifications** - Notify when processing complete
6. **Advanced Analytics** - Track usage patterns
7. **API Rate Limiting** - Prevent abuse
8. **Video Comments** - Allow feedback on gallery videos

---

*Last Updated: December 2024*
*Total Implementation Time: 2-3 days*
*Total Monthly Cost: $0 (free tier)*