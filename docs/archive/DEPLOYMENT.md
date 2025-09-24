# BodyScript Deployment Guide

## Backend Deployment (Render.com)

### 1. Push to GitHub
First, make sure your code is on GitHub:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Deploy to Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: bodyscript-api
   - **Root Directory**: leave blank
   - **Runtime**: Python
   - **Build Command**: `./build.sh`
   - **Start Command**: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

5. Add Environment Variables (click "Advanced"):
   - `R2_ACCOUNT_ID`: 91cb378ba9983dc724f9898e779a55bc
   - `R2_ACCESS_KEY`: c9097414a7147b9da102fb6dfc140449
   - `R2_SECRET_KEY`: [your secret key]
   - `ADMIN_TOKEN`: [generate a secure token]
   - `ENVIRONMENT`: production

6. Click **Create Web Service**

Your backend will be deployed at: `https://bodyscript-api.onrender.com`

## Frontend Deployment (Vercel)

### 1. Update API URL
Edit `frontend/config.js`:
```javascript
// Change line 16 from localhost to your Render URL:
return 'https://bodyscript-api.onrender.com';
```

### 2. Deploy to Vercel

Option A - Using Vercel CLI:
```bash
npm i -g vercel
cd frontend
vercel
```

Option B - Using GitHub:
1. Go to [vercel.com](https://vercel.com)
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Other
5. Click **Deploy**

Your frontend will be deployed at: `https://bodyscript.vercel.app`

## Post-Deployment

1. **Test the deployment**:
   - Visit your frontend URL
   - Upload a test video
   - Check processing works

2. **Monitor logs**:
   - Render: Dashboard → Logs
   - Vercel: Project → Functions → Logs

3. **Custom Domain** (optional):
   - Vercel: Settings → Domains → Add your domain
   - Render: Settings → Custom Domains

## Important Notes

- **Free Tier Limitations**:
  - Render: Spins down after 15 min inactivity (cold starts)
  - Vercel: 100GB bandwidth/month
  - Both are fine for development/testing

- **Scaling Up**:
  - Render: Upgrade to Starter ($7/month) for always-on
  - Vercel: Pro plan for more bandwidth

## Troubleshooting

If backend is slow to respond:
- This is normal on free tier (cold start)
- The frontend shows "Waking up server" message
- Takes 30-60 seconds on first request

If uploads fail:
- Check Render logs for errors
- Verify environment variables are set
- Check R2 credentials are correct