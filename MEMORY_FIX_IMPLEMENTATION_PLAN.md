# BodyScript Memory Fix Implementation Plan

## Overview
This plan addresses the critical memory issues causing Render API crashes. Tasks are organized by priority and designed to be completed in 15-30 minute increments.

**Estimated Total Time**: 8-10 hours
**Critical Path**: Phase 1 + 2 (2-3 hours) will prevent most crashes

---

## Phase 0: Immediate Mitigation (30 minutes)
*Do these NOW to stop crashes while implementing fixes*

### Configuration Changes
- [ ] **Reduce MAX_VIDEO_SIZE_MB** in `/backend/app.py` line 53 from 100MB to 30MB
- [ ] **Reduce MAX_VIDEO_DURATION_SECONDS** in `/backend/app.py` line 54 from 15 to 10 seconds
- [ ] **Update Render instance** to at least 2GB RAM (via Render dashboard)
- [ ] **Set Render health check** timeout to 60 seconds (prevents restart during processing)
- [ ] **Add environment variable** `PYTHONUNBUFFERED=1` to Render for better logging

### Quick Wins
- [ ] **Fix numpy import** in `/backend/video_utils.py` - add `import numpy as np` at line 6
- [ ] **Reduce frame extraction interval** in `/backend/process_wrapper.py` line 157 from `interval=1` to `interval=3`
- [ ] **Test deployment** with a small video (<5MB) to verify changes

---

## Phase 1: Critical Memory Leaks (1-2 hours)
*Fix the biggest memory leaks first*

### Task 1.1: Add MediaPipe Cleanup (30 min)
- [ ] **Create cleanup method** in `/cli/src/processors/mediapipe_fast_smart.py`:
  ```python
  def close(self):
      if hasattr(self, 'pose') and self.pose:
          self.pose.close()
          self.pose = None
  ```
- [ ] **Add destructor** to MediaPipeFastSmart class:
  ```python
  def __del__(self):
      self.close()
  ```
- [ ] **Call cleanup** in `/backend/process_wrapper.py` after line 182:
  ```python
  processor.close()  # Add after processing complete
  ```
- [ ] **Test cleanup** by processing a video and checking logs

### Task 1.2: Add WebVideoProcessor Cleanup (20 min)
- [ ] **Add cleanup method** to WebVideoProcessor class in `/backend/process_wrapper.py`:
  ```python
  def cleanup_processor(self):
      # Force cleanup of any processors
      import gc
      gc.collect()
  ```
- [ ] **Call cleanup** in process_video_task after processing (app.py line 289)
- [ ] **Add finally block** to ensure cleanup on errors

### Task 1.3: Implement Job Auto-Cleanup (30 min)
- [ ] **Add timestamp** to job creation in `/backend/app.py` line 211:
  ```python
  "created_timestamp": time.time(),
  ```
- [ ] **Create cleanup function** in app.py:
  ```python
  def cleanup_old_jobs(max_age_seconds=3600):
      current = time.time()
      for job_id in list(jobs_status.keys()):
          age = current - jobs_status[job_id].get('created_timestamp', 0)
          if age > max_age_seconds:
              processor.cleanup_job(job_id)
              del jobs_status[job_id]
  ```
- [ ] **Add periodic cleanup** using BackgroundTasks every 30 minutes
- [ ] **Test cleanup** by creating test jobs and waiting

### Task 1.4: Add Emergency Memory Release (20 min)
- [ ] **Install psutil**: Add `psutil==5.9.6` to requirements.txt
- [ ] **Create memory check** function in app.py:
  ```python
  def check_memory_usage():
      import psutil
      return psutil.Process().memory_info().rss / 1024 / 1024
  ```
- [ ] **Add pre-processing check** before line 266 in app.py:
  ```python
  if check_memory_usage() > 400:  # MB
      cleanup_old_jobs(max_age_seconds=600)  # Aggressive cleanup
      import gc
      gc.collect()
  ```
- [ ] **Test memory check** with concurrent requests

---

## Phase 2: Memory Usage Reduction (1-2 hours)
*Reduce peak memory consumption*

### Task 2.1: Implement Frame Batch Processing (45 min)
- [ ] **Create batch extractor** in `/backend/process_wrapper.py`:
  ```python
  def extract_frames_batch(video_path, start_frame, end_frame, output_dir):
      # Extract only specific frame range
      pass
  ```
- [ ] **Modify processing loop** to work in batches of 30 frames
- [ ] **Delete frames** immediately after processing each batch
- [ ] **Add progress tracking** for batched processing
- [ ] **Test batch processing** with a medium-sized video

### Task 2.2: Optimize DataFrame Memory (20 min)
- [ ] **Use generator** instead of list in `/cli/src/processors/mediapipe_fast_smart.py` line 226
- [ ] **Write results incrementally** to CSV instead of storing all in memory
- [ ] **Add dtype optimization** for DataFrame columns:
  ```python
  dtype={'frame_id': 'uint16', 'landmark_id': 'uint8',
         'x': 'float32', 'y': 'float32', 'z': 'float32'}
  ```
- [ ] **Test memory usage** with large video

### Task 2.3: Reduce Video Copies (30 min)
- [ ] **Delete original** after trimming in `/backend/process_wrapper.py` line 138
- [ ] **Delete trimmed** after resizing (if resized) line 144
- [ ] **Use in-place operations** where possible
- [ ] **Add explicit deletion**:
  ```python
  os.remove(input_video_path)  # After trimming
  del trimmed_video  # Remove reference
  ```
- [ ] **Test file cleanup** during processing

### Task 2.4: Optimize Frame Format (20 min)
- [ ] **Change frame format** from PNG to JPEG in line 158:
  ```python
  format='jpg'  # Instead of 'png'
  ```
- [ ] **Add compression** quality parameter:
  ```python
  quality=85  # JPEG quality
  ```
- [ ] **Calculate memory savings** (JPEG ~10x smaller than PNG)
- [ ] **Test quality** impact on pose detection

---

## Phase 3: Resource Management (1-2 hours)
*Proper resource lifecycle management*

### Task 3.1: Add Context Managers (30 min)
- [ ] **Create context manager** for MediaPipeFastSmart:
  ```python
  def __enter__(self):
      return self
  def __exit__(self, exc_type, exc_val, exc_tb):
      self.close()
  ```
- [ ] **Use with statement** in process_wrapper.py:
  ```python
  with MediaPipeFastSmart(mode=mode) as processor:
      # process video
  ```
- [ ] **Add VideoCapture context** manager for safe release
- [ ] **Test context managers** with normal and error cases

### Task 3.2: Fix VideoCapture Leaks (20 min)
- [ ] **Add try-finally** to all VideoCapture usage in `/backend/video_utils.py`
- [ ] **Ensure cap.release()** in all error paths
- [ ] **Add release check**:
  ```python
  if cap and cap.isOpened():
      cap.release()
  ```
- [ ] **Test with invalid** video files

### Task 3.3: Add Resource Pooling (30 min)
- [ ] **Create processor pool** instead of creating new instances:
  ```python
  class ProcessorPool:
      def __init__(self, size=2):
          self.processors = []
      def get_processor(self):
          # Return available processor
      def return_processor(self, proc):
          # Return to pool after use
  ```
- [ ] **Implement pool** in WebVideoProcessor
- [ ] **Test pool** with concurrent requests
- [ ] **Monitor reuse** effectiveness

### Task 3.4: Add Garbage Collection (15 min)
- [ ] **Import gc** module in process_wrapper.py
- [ ] **Add gc.collect()** after major operations:
  - After frame deletion
  - After DataFrame creation
  - After video processing
- [ ] **Configure gc** threshold for aggressive collection
- [ ] **Test memory** release timing

---

## Phase 4: Monitoring & Alerts (1 hour)
*Visibility into memory usage*

### Task 4.1: Add Memory Health Endpoint (20 min)
- [ ] **Create endpoint** `/health/memory` in app.py:
  ```python
  @app.get("/health/memory")
  async def memory_health():
      import psutil
      proc = psutil.Process()
      return {
          "memory_mb": proc.memory_info().rss / 1024 / 1024,
          "memory_percent": proc.memory_percent(),
          "jobs_count": len(jobs_status),
          "status": "critical" if proc.memory_percent() > 80 else "ok"
      }
  ```
- [ ] **Add to root** endpoint list
- [ ] **Test endpoint** response
- [ ] **Add to Render** health checks

### Task 4.2: Add Memory Logging (20 min)
- [ ] **Create logger** for memory tracking
- [ ] **Log memory** at key points:
  ```python
  logger.info(f"Memory before processing: {check_memory_usage():.1f}MB")
  logger.info(f"Memory after frames: {check_memory_usage():.1f}MB")
  logger.info(f"Memory after cleanup: {check_memory_usage():.1f}MB")
  ```
- [ ] **Add to process_video_task** start and end
- [ ] **Test logging** output in Render logs

### Task 4.3: Add Processing Limits (20 min)
- [ ] **Create semaphore** to limit concurrent processing:
  ```python
  processing_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent
  ```
- [ ] **Check memory before** accepting new jobs:
  ```python
  if check_memory_usage() > 450:
      raise HTTPException(503, "Server at capacity, try again later")
  ```
- [ ] **Add queue size** limit (max 10 pending jobs)
- [ ] **Test limits** with multiple uploads

### Task 4.4: Add Metrics Collection (20 min)
- [ ] **Track metrics** per job:
  - Peak memory usage
  - Processing time
  - Frame count
  - Error rate
- [ ] **Create endpoint** `/api/metrics` for monitoring
- [ ] **Calculate averages** for capacity planning
- [ ] **Test metrics** accuracy

---

## Phase 5: Testing & Validation (1 hour)
*Ensure fixes work correctly*

### Task 5.1: Create Memory Test Suite (30 min)
- [ ] **Create test script** `test_memory.py`:
  ```python
  def test_single_video():
      # Upload, process, check memory
  def test_concurrent_videos():
      # Upload 3 videos simultaneously
  def test_large_video():
      # Test with 30MB video
  def test_memory_cleanup():
      # Verify memory returns to baseline
  ```
- [ ] **Add memory assertions** for each test
- [ ] **Run locally** first
- [ ] **Run on Render** staging

### Task 5.2: Load Testing (20 min)
- [ ] **Install locust**: `pip install locust`
- [ ] **Create locustfile.py** for load testing
- [ ] **Test scenarios**:
  - 5 concurrent uploads
  - 20 sequential uploads
  - Mixed sizes (5MB, 10MB, 20MB)
- [ ] **Monitor memory** during load test
- [ ] **Document limits** found

### Task 5.3: Create Monitoring Dashboard (10 min)
- [ ] **Create simple HTML** page for monitoring
- [ ] **Display**:
  - Current memory usage
  - Active jobs
  - Queue size
  - Recent errors
- [ ] **Auto-refresh** every 30 seconds
- [ ] **Deploy** as `/monitor` endpoint

---

## Phase 6: Documentation & Deployment (30 min)
*Document and deploy fixes*

### Task 6.1: Update Documentation (15 min)
- [ ] **Document memory limits** in README
- [ ] **Add troubleshooting** section
- [ ] **Update API docs** with new endpoints
- [ ] **Create runbook** for memory issues

### Task 6.2: Deploy to Staging (10 min)
- [ ] **Create git branch** `fix/memory-issues`
- [ ] **Commit all changes** with clear messages
- [ ] **Deploy to staging** environment
- [ ] **Run test suite** on staging

### Task 6.3: Production Deployment (5 min)
- [ ] **Merge to main** after testing
- [ ] **Deploy to production** during low traffic
- [ ] **Monitor memory** for 1 hour
- [ ] **Rollback plan** ready

---

## Success Metrics

### Immediate (After Phase 1-2):
- [ ] No OOM crashes for videos < 30MB
- [ ] Memory usage stays below 500MB for single video
- [ ] Jobs auto-cleanup after 1 hour

### Short-term (After Phase 3-4):
- [ ] Support 3 concurrent video processing
- [ ] Memory returns to baseline after processing
- [ ] Memory monitoring dashboard available

### Long-term (After all phases):
- [ ] 90% reduction in memory-related crashes
- [ ] Support 5+ concurrent users
- [ ] Average memory usage < 400MB
- [ ] Peak memory usage < 800MB

---

## Rollback Plan

If issues occur after deployment:

1. **Immediate**: Revert to previous version via Render
2. **Data**: Jobs in memory will be lost (acceptable for MVP)
3. **Monitoring**: Keep memory endpoint for diagnosis
4. **Fallback**: Increase RAM to 4GB temporarily

---

## Notes

- **Priority**: Complete Phase 0-2 first (prevents 90% of crashes)
- **Testing**: Test each phase on staging before production
- **Monitoring**: Check memory after each phase completion
- **Communication**: Notify users of temporary limits during fixes

**Total Tasks**: 67 checkboxes
**Critical Path**: Phase 0 + 1 + 2 (24 tasks, ~3 hours)
**Full Implementation**: All phases (67 tasks, ~8-10 hours)