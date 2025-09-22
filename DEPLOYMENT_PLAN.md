# BodyScript Deployment Plan: Vercel (Frontend) + Render (Backend)

## Overview
This plan deploys BodyScript using a modern microservices architecture:
- **Frontend**: Static HTML/JS on Vercel's global CDN
- **Backend**: FastAPI Python app on Render's cloud platform
- **Total Time**: ~45 minutes
- **Cost**: $0 (both platforms offer free tiers)

## Architecture Diagram
```
Users → Vercel CDN (Frontend) → API Calls → Render (Backend) → Process Video → Return Results
         (Global)                             (US Region)
```

---

## Phase 1: Prerequisites & Preparation

### 1.1 Required Accounts (10 minutes)
- [ ] Create GitHub account (if not existing): https://github.com
- [ ] Create Vercel account: https://vercel.com/signup
  - Sign up with GitHub for easier integration
- [ ] Create Render account: https://render.com
  - Sign up with GitHub for easier integration

### 1.2 Required Tools
- [ ] Git installed locally
- [ ] Node.js installed (for Vercel CLI - optional but recommended)
- [ ] Python 3.9-3.11 (for local testing)

### 1.3 Project Preparation (15 minutes)

#### A. Create GitHub Repository
```bash
# In your bodyscript directory
git init
git add .
git commit -m "Initial commit for deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/bodyscript.git
git branch -M main
git push -u origin main
```

#### B. Create Backend-Specific Files

**Create `backend/render.yaml`:**
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
```

**Create `backend/runtime.txt`:**
```
python-3.11.8
```

**Update `backend/.gitignore`:**
```
__pycache__/
*.pyc
temp/
*.mp4
*.csv
.env
```

#### C. Create Frontend Configuration

**Create `frontend/vercel.json`:**
```json
{
  "name": "bodyscript-frontend",
  "buildCommand": "",
  "outputDirectory": ".",
  "framework": null,
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Create `frontend/.env.production`:**
```
VITE_API_URL=https://bodyscript-api.onrender.com
```

**Create `frontend/.env.development`:**
```
VITE_API_URL=http://localhost:8000
```

---

## Phase 2: Backend Deployment to Render (15 minutes)

### 2.1 Prepare Backend Code

#### A. Update File Paths for Cloud Environment
**Edit `backend/process_wrapper.py`:**
```python
# Line 29 - Update temp directory
def __init__(self, temp_dir: str = "/tmp/bodyscript"):  # Changed from "backend/temp"
```

#### B. Add Health Check Endpoint
**Add to `backend/app.py`:**
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bodyscript-api"}
```

#### C. Update Requirements
**Ensure `backend/requirements.txt` includes:**
```
# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1

# Processing dependencies
opencv-python-headless==4.8.1  # Changed from opencv-python
mediapipe==0.10.7
pandas==2.1.3
numpy==1.24.3
```

### 2.2 Deploy to Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +" → "Web Service"**
3. **Connect GitHub repository**
4. **Configure service:**
   - Name: `bodyscript-api`
   - Environment: `Python 3`
   - Region: `Oregon (US West)`
   - Branch: `main`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables:**
   - Add `PYTHON_VERSION` = `3.11.8`
   - Add `PORT` = `10000` (Render will override this)
6. **Select Free Plan**
7. **Click "Create Web Service"**

### 2.3 Wait for Deployment
- First deployment takes 5-10 minutes
- Check logs for any errors
- Test endpoint: `https://bodyscript-api.onrender.com/health`

---

## Phase 3: Frontend Deployment to Vercel (10 minutes)

### 3.1 Prepare Frontend Code

#### A. Create Environment Variable Handler
**Create `frontend/config.js`:**
```javascript
// Dynamic API URL configuration
const getApiUrl = () => {
  if (window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  // Production URL - UPDATE THIS after Render deployment
  return 'https://bodyscript-api.onrender.com';
};

window.API_URL = getApiUrl();
```

#### B. Update Frontend API Calls
**Edit `frontend/index.html`:**
```javascript
// Line 214 - Replace:
const API_URL = 'http://localhost:8000';

// With:
const API_URL = window.API_URL || 'https://bodyscript-api.onrender.com';
```

**Add to `<head>` section:**
```html
<script src="config.js"></script>
```

### 3.2 Deploy to Vercel

#### Option A: Via Vercel CLI (Recommended)
```bash
# Install Vercel CLI
npm install -g vercel

# In frontend directory
cd frontend
vercel

# Follow prompts:
# - Set up and deploy: Y
# - Which scope: Your account
# - Link to existing project: N
# - Project name: bodyscript-frontend
# - Directory: ./
# - Build command: (leave blank)
# - Output directory: (leave blank)
# - Development command: (leave blank)
```

#### Option B: Via GitHub Integration
1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import Git Repository → Select your repo
4. Configure:
   - Framework Preset: `Other`
   - Root Directory: `frontend`
   - Build Command: (leave empty)
   - Output Directory: `./`
5. Click "Deploy"

### 3.3 Get Deployment URLs
- Frontend: `https://bodyscript-frontend.vercel.app`
- Backend: `https://bodyscript-api.onrender.com`

---

## Phase 4: Configuration & Testing (5 minutes)

### 4.1 Update CORS Settings (if needed)
**Edit `backend/app.py` for production:**
```python
# Line 31 - Update CORS origins
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

### 4.2 Test Complete Flow
1. Open frontend URL: `https://bodyscript-frontend.vercel.app`
2. Upload a small test video (< 5MB)
3. Check processing works
4. Download results

### 4.3 Monitor Logs
- **Render logs**: Dashboard → Your Service → Logs
- **Vercel logs**: Dashboard → Your Project → Functions

---

## Phase 5: Troubleshooting Guide

### Common Issues & Solutions

#### 1. "CORS Error" in Browser Console
```javascript
// Solution: Update backend CORS settings
allow_origins=["https://your-frontend.vercel.app"]
```

#### 2. "502 Bad Gateway" from Render
```bash
# Check Render logs for startup errors
# Common: Missing dependency or wrong Python version
```

#### 3. "Module not found" on Render
```bash
# Add missing module to requirements.txt
# Redeploy
```

#### 4. Large Video Upload Fails
```python
# Add to backend/app.py:
app.add_middleware(
    CORSMiddleware,
    max_age=3600,
)

# Increase upload limit:
@app.post("/upload")
async def upload(file: UploadFile = File(..., max_length=52428800)):  # 50MB
```

#### 5. Render Free Tier Sleeping
```javascript
// Add keep-alive to frontend (optional):
setInterval(() => {
  fetch(`${API_URL}/health`)
    .catch(() => {}); // Ignore errors
}, 600000); // Every 10 minutes
```

---

## Phase 6: Post-Deployment Checklist

### Security
- [ ] Remove `allow_origins=["*"]` from CORS
- [ ] Add specific domain allowlist
- [ ] Set up environment variables for sensitive data
- [ ] Enable HTTPS (automatic on both platforms)

### Performance
- [ ] Test with various video sizes
- [ ] Monitor response times
- [ ] Check Render memory usage
- [ ] Optimize video processing timeout

### Monitoring
- [ ] Set up Render notifications for failures
- [ ] Enable Vercel analytics
- [ ] Add error tracking (optional: Sentry)

### Documentation
- [ ] Update README with production URLs
- [ ] Document API endpoints
- [ ] Add deployment instructions to repo

---

## Cost Analysis

### Free Tier Limits
**Vercel (Frontend):**
- ✅ Unlimited bandwidth
- ✅ 100GB-hours compute
- ✅ Automatic HTTPS
- ✅ Global CDN

**Render (Backend):**
- ⚠️ 750 hours/month (enough for 24/7 single service)
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ 100GB bandwidth/month
- ✅ Automatic HTTPS

### When You'll Need to Pay
- More than ~1000 video processes/month
- Need always-on service (no cold starts)
- Videos larger than 15 seconds
- Multiple concurrent users

### Upgrade Path
1. **Render Starter**: $7/month (no sleep, better performance)
2. **Vercel Pro**: $20/month (team features, more compute)

---

## Quick Commands Reference

```bash
# Local Testing
cd backend && uvicorn app:app --reload
cd frontend && python -m http.server 3000

# Deploy Backend (after changes)
git add backend/
git commit -m "Update backend"
git push origin main
# Render auto-deploys

# Deploy Frontend (after changes)
cd frontend
vercel --prod

# View Logs
# Render: https://dashboard.render.com
# Vercel: https://vercel.com/dashboard

# Test Endpoints
curl https://bodyscript-api.onrender.com/health
curl https://bodyscript-frontend.vercel.app
```

---

## Next Steps

1. **Custom Domain** (Optional)
   - Add custom domain in Vercel settings
   - Add custom domain in Render settings
   - Update CORS origins

2. **Enhanced Features**
   - Add user authentication
   - Implement video queue system
   - Add progress WebSocket

3. **Scaling**
   - Consider CDN for video delivery
   - Add Redis for caching
   - Implement background workers

---

## Support Resources

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **CORS Guide**: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS

---

## Estimated Timeline

| Phase | Time | Description |
|-------|------|-------------|
| Prerequisites | 10 min | Create accounts, install tools |
| Preparation | 15 min | Set up GitHub, create config files |
| Backend Deploy | 15 min | Deploy to Render, wait for build |
| Frontend Deploy | 10 min | Deploy to Vercel |
| Testing | 5 min | Verify everything works |
| **Total** | **~45 min** | **Full deployment complete** |

---

## Success Criteria

✅ Frontend loads at `https://bodyscript-frontend.vercel.app`
✅ Backend responds at `https://bodyscript-api.onrender.com/health`
✅ Video upload and processing works
✅ Results download successfully
✅ No CORS errors in browser console

---

*Last Updated: December 2024*
*Platform Versions: Render v2, Vercel v3*