# Frontend Deployment Guide - BodyScript

## Overview
This guide provides step-by-step instructions for deploying the BodyScript frontend to staging and production environments.

## Pre-Deployment Checklist

### Code Verification
- [x] All refactoring phases complete (1-15)
- [x] 165/165 tests passed
- [x] No console errors
- [x] No 404 resources
- [x] Mobile responsive verified
- [x] Cross-browser tested

### File Structure Verification
```
frontend/
├── css/                    # ✅ 10 modular CSS files
├── js/                     # ✅ 12 modular JS files
├── assets/                 # ✅ Shared resources
├── upload.html             # ✅ 191 lines (was 1,741)
├── index.html              # ✅ 80 lines (was 820)
└── config.js               # ⚠️ UPDATE BEFORE DEPLOY
```

## Environment Configuration

### 1. Update API Configuration

**config.js** - Update for your environment:
```javascript
// Development (default)
window.API_URL = 'http://localhost:8000';

// Staging
window.API_URL = 'https://staging-api.yourdomain.com';

// Production
window.API_URL = 'https://api.yourdomain.com';
```

### 2. Environment-Specific Settings

Create environment configs:
```bash
# config.dev.js
window.API_URL = 'http://localhost:8000';
window.ENV = 'development';

# config.staging.js
window.API_URL = 'https://staging-api.yourdomain.com';
window.ENV = 'staging';

# config.prod.js
window.API_URL = 'https://api.yourdomain.com';
window.ENV = 'production';
```

## Deployment Steps

### Step 1: Local Verification

```bash
# 1. Start local server
cd frontend/
python -m http.server 8001

# 2. Test all pages
# - http://localhost:8001/upload.html
# - http://localhost:8001/index.html
# - http://localhost:8001/admin.html

# 3. Verify API connection
# Ensure backend is running on port 8000
```

### Step 2: Build for Production

```bash
# 1. Clean any temporary files
find . -name "*.tmp" -delete
find . -name ".DS_Store" -delete

# 2. Update config.js with production API URL
cp config.prod.js config.js

# 3. Optional: Minify CSS (preserves originals)
for file in css/**/*.css; do
  csso "$file" -o "${file%.css}.min.css"
done

# 4. Create deployment package
tar -czf frontend-deploy.tar.gz \
  css/ js/ assets/ \
  upload.html index.html admin.html \
  config.js favicon.ico
```

### Step 3: Deploy to Staging

#### Option A: Using rsync
```bash
rsync -avz --delete \
  --exclude='*.md' \
  --exclude='TEST_CHECKLIST.md' \
  --exclude='node_modules' \
  ./ user@staging-server:/var/www/bodyscript-frontend/
```

#### Option B: Using SCP
```bash
scp -r css js assets *.html config.js \
  user@staging-server:/var/www/bodyscript-frontend/
```

#### Option C: Using Git
```bash
git add .
git commit -m "Deploy frontend v2.0 - modular architecture"
git push origin staging
# Then pull on staging server
ssh user@staging-server
cd /var/www/bodyscript-frontend
git pull origin staging
```

### Step 4: Staging Verification

1. **Test Core Functionality**
   - [ ] Upload page loads
   - [ ] Gallery displays videos
   - [ ] File upload works
   - [ ] Video processing completes
   - [ ] Downloads function

2. **Check Network**
   - [ ] API endpoints reachable
   - [ ] No CORS errors
   - [ ] SSL certificates valid
   - [ ] Resources load via HTTPS

3. **Performance Check**
   - [ ] Page load < 3 seconds
   - [ ] GTmetrix score > B
   - [ ] Mobile PageSpeed > 80

### Step 5: Deploy to Production

```bash
# 1. Backup current production
ssh user@prod-server
cd /var/www/
tar -czf bodyscript-frontend-backup-$(date +%Y%m%d).tar.gz bodyscript-frontend/

# 2. Deploy new version
rsync -avz --delete \
  --exclude='*.md' \
  --exclude='TEST_CHECKLIST.md' \
  ./ user@prod-server:/var/www/bodyscript-frontend/

# 3. Clear CDN cache (if applicable)
# CloudFlare, AWS CloudFront, etc.
```

### Step 6: Production Verification

1. **Smoke Tests**
   ```bash
   # Test main pages
   curl -I https://yourdomain.com/upload.html
   curl -I https://yourdomain.com/index.html
   ```

2. **User Flow Test**
   - [ ] Upload test video
   - [ ] Verify processing
   - [ ] Download results
   - [ ] Check gallery display

3. **Monitor Logs**
   ```bash
   # Watch error logs
   tail -f /var/log/nginx/error.log
   tail -f /var/log/apache2/error.log
   ```

## Web Server Configuration

### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    root /var/www/bodyscript-frontend;

    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Compression
    gzip on;
    gzip_types text/css application/javascript;

    # Cache static assets
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Default to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Apache Configuration
```apache
<VirtualHost *:443>
    ServerName yourdomain.com
    DocumentRoot /var/www/bodyscript-frontend

    # Enable compression
    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/css application/javascript
    </IfModule>

    # Cache control
    <FilesMatch "\.(css|js|jpg|jpeg|png|gif|ico|woff2)$">
        Header set Cache-Control "max-age=2592000, public"
    </FilesMatch>

    # Security headers
    Header set X-Content-Type-Options "nosniff"
    Header set X-Frame-Options "DENY"
    Header set X-XSS-Protection "1; mode=block"
</VirtualHost>
```

## CDN Configuration (Optional)

### CloudFlare Settings
1. **Caching Level**: Standard
2. **Browser Cache TTL**: 1 month
3. **Always Online**: Enabled
4. **Auto Minify**: CSS, JavaScript
5. **Brotli**: Enabled

### Cache Purge After Deploy
```bash
# CloudFlare API
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

## Rollback Procedure

### Quick Rollback (< 5 minutes)
```bash
# 1. SSH to server
ssh user@prod-server

# 2. Restore backup
cd /var/www/
mv bodyscript-frontend bodyscript-frontend-failed
tar -xzf bodyscript-frontend-backup-$(date +%Y%m%d).tar.gz

# 3. Clear cache
# nginx -s reload
# service apache2 reload
```

### Git-based Rollback
```bash
# 1. Find last working commit
git log --oneline

# 2. Revert to previous version
git revert HEAD
git push origin production

# 3. Pull on server
ssh user@prod-server
cd /var/www/bodyscript-frontend
git pull origin production
```

## Post-Deployment Monitoring

### First Hour
- [ ] Check error logs every 15 minutes
- [ ] Monitor server CPU/memory
- [ ] Watch for 404/500 errors
- [ ] Verify API response times

### First 24 Hours
- [ ] Review analytics for anomalies
- [ ] Check user feedback channels
- [ ] Monitor performance metrics
- [ ] Verify backup systems

### Monitoring Commands
```bash
# Server resources
htop
df -h

# Error logs
tail -f /var/log/nginx/error.log
journalctl -u nginx -f

# Access patterns
tail -f /var/log/nginx/access.log | grep -E "4[0-9]{2}|5[0-9]{2}"

# API health
curl -s https://api.yourdomain.com/health
```

## Troubleshooting

### Common Issues

#### 1. Module Loading Errors
**Symptom**: "Failed to load module script"
**Solution**: Ensure web server sends correct MIME type
```nginx
location ~ \.js$ {
    add_header Content-Type application/javascript;
}
```

#### 2. CORS Errors
**Symptom**: "Access blocked by CORS policy"
**Solution**: Configure API server CORS headers
```python
# FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 3. 404 on Resources
**Symptom**: CSS/JS files not found
**Solution**: Check file paths are relative
```html
<!-- Correct -->
<link rel="stylesheet" href="css/main.css">

<!-- Incorrect -->
<link rel="stylesheet" href="/frontend/css/main.css">
```

#### 4. Slow Load Times
**Symptom**: Page takes > 3 seconds to load
**Solution**: Enable compression and caching
```bash
# Check gzip is enabled
curl -H "Accept-Encoding: gzip" -I https://yourdomain.com/css/main.css
```

## Performance Optimization

### Optional Optimizations
1. **Image Optimization**
   ```bash
   # Optimize images
   find . -name "*.png" -exec optipng {} \;
   find . -name "*.jpg" -exec jpegoptim {} \;
   ```

2. **Lazy Loading**
   - Implement for gallery videos
   - Use Intersection Observer API

3. **Service Worker**
   - Cache static assets
   - Offline functionality

4. **HTTP/2 Push**
   ```nginx
   location = /index.html {
       http2_push /css/main.css;
       http2_push /js/pages/gallery-page.js;
   }
   ```

## Security Checklist

- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] API endpoints use authentication
- [ ] Input validation on all forms
- [ ] XSS protection enabled
- [ ] SQL injection prevented (backend)
- [ ] Rate limiting configured
- [ ] Error messages don't leak info

## Success Criteria

### Deployment is successful when:
- ✅ All pages load without errors
- ✅ Upload functionality works end-to-end
- ✅ Gallery displays all videos
- ✅ Mobile experience is smooth
- ✅ No console errors in production
- ✅ Page load time < 3 seconds
- ✅ All tests from TEST_CHECKLIST pass
- ✅ No user complaints in first 24 hours

## Support Contacts

### Emergency Contacts
- **DevOps Lead**: [contact info]
- **Backend Team**: [contact info]
- **Frontend Team**: [contact info]

### Escalation Path
1. Check logs and monitoring
2. Attempt quick fix if obvious
3. Rollback if issue persists > 15 min
4. Contact team lead
5. Post-mortem within 48 hours

---

## Deployment Sign-off

### Pre-deployment
- [ ] Code review completed
- [ ] Tests passed (165/165)
- [ ] Staging verified
- [ ] Rollback plan ready
- [ ] Team notified

### Deployment
- **Date**: _______________
- **Time**: _______________
- **Deployed By**: _______________
- **Version**: 2.0 (Modular Architecture)
- **Environment**: _______________

### Post-deployment
- [ ] Production verified
- [ ] Monitoring active
- [ ] No critical issues
- [ ] Performance acceptable
- [ ] Users notified (if needed)

---

**Deployment Status**: READY FOR DEPLOYMENT ✅

The frontend has been successfully refactored, tested, and documented. Follow this guide for a smooth deployment to production.