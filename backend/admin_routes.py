"""
Admin routes for gallery curation and video management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict
from datetime import datetime
import os
import json

from storage_r2 import r2_storage

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin(token: str = Query(..., alias="auth")):
    """Simple admin authentication"""
    admin_token = os.getenv('ADMIN_TOKEN', 'admin-secret-token-change-this')
    if token != admin_token:
        raise HTTPException(status_code=403, detail="Not authorized")
    return True


@router.get("/pending-videos")
async def list_pending_videos(auth: bool = Depends(verify_admin)):
    """
    List all videos in upload bucket awaiting review

    Returns:
        List of video metadata for curation
    """
    videos = r2_storage.list_pending_uploads()

    # Sort by processed date (newest first)
    videos.sort(key=lambda x: x.get('processed_at', ''), reverse=True)

    # Add detection rate for easier filtering
    for video in videos:
        stats = video.get('statistics', {})
        video['detection_rate'] = stats.get('detection_rate', 0)
        video['average_quality'] = stats.get('average_quality', 0)

    return {'videos': videos}


@router.post("/approve-to-gallery")
async def approve_to_gallery(
    job_id: str,
    display_name: str,
    category: str,
    title: Optional[str] = None,
    auth: bool = Depends(verify_admin)
):
    """
    Copy video from uploads to gallery with curation metadata

    Args:
        job_id: Original job ID from processing
        display_name: URL-safe name for gallery (e.g., 'dance-performance-1')
        category: Category for filtering ('dance', 'sports', 'yoga', 'martial')
        title: Display title (defaults to formatted display_name)

    Returns:
        Success status and gallery URLs
    """
    try:
        # Copy files to gallery bucket
        urls = r2_storage.copy_to_gallery(job_id, display_name)

        if not urls:
            raise HTTPException(status_code=500, detail="Failed to copy to gallery")

        # Prepare gallery metadata
        gallery_entry = {
            'id': display_name,
            'title': title or display_name.replace('-', ' ').title(),
            'category': category,
            'thumbnail': urls.get('thumbnail', ''),
            'preview': urls.get('preview', ''),
            'full': urls.get('full', ''),
            'added_at': datetime.now().isoformat(),
            'accuracy': 95.0,  # Default, should get from metadata
            'views': '0',
            'likes': '0',
            'duration': '0:30'  # Default, should calculate
        }

        # Try to get actual statistics from metadata
        try:
            pending_videos = r2_storage.list_pending_uploads()
            for video in pending_videos:
                if video['job_id'] == job_id:
                    stats = video.get('statistics', {})
                    gallery_entry['accuracy'] = round(stats.get('detection_rate', 0) * 100, 1)
                    video_info = video.get('video_info', {})
                    duration = video_info.get('duration', 30)
                    gallery_entry['duration'] = f"{int(duration // 60)}:{int(duration % 60):02d}"
                    break
        except:
            pass

        # Update gallery.json
        success = r2_storage.update_gallery_json(gallery_entry)

        if success:
            # Delete from uploads to save space
            r2_storage.delete_upload(job_id)

        return {
            'success': success,
            'gallery_entry': gallery_entry,
            'message': f"Video '{display_name}' added to gallery"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reject-video/{job_id}")
async def reject_video(job_id: str, auth: bool = Depends(verify_admin)):
    """
    Delete video from uploads without adding to gallery

    Args:
        job_id: Job ID to delete

    Returns:
        Success status
    """
    success = r2_storage.delete_upload(job_id)

    if success:
        return {'success': True, 'message': f"Video {job_id} deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete video")


@router.get("/gallery-stats")
async def get_gallery_stats(auth: bool = Depends(verify_admin)):
    """
    Get statistics about gallery and uploads

    Returns:
        Statistics about storage usage and content
    """
    try:
        # Get pending uploads count
        pending_videos = r2_storage.list_pending_uploads()
        pending_count = len(pending_videos)

        # Calculate total pending size (estimate)
        pending_size = sum(
            video.get('video_info', {}).get('size', 0)
            for video in pending_videos
        ) / (1024 * 1024)  # Convert to MB

        # Get gallery videos count (would need to download gallery.json)
        gallery_count = 0
        try:
            # This would need implementation in r2_storage
            pass
        except:
            pass

        return {
            'pending_videos': pending_count,
            'pending_size_mb': round(pending_size, 2),
            'gallery_videos': gallery_count,
            'storage_usage': {
                'uploads_bucket': f"{pending_size:.1f} MB",
                'gallery_bucket': "Unknown",
                'total': f"{pending_size:.1f} MB"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-old-uploads")
async def cleanup_old_uploads(
    days_old: int = 7,
    auth: bool = Depends(verify_admin)
):
    """
    Delete uploads older than specified days

    Args:
        days_old: Delete videos older than this many days

    Returns:
        Number of videos deleted
    """
    try:
        from datetime import timedelta

        pending_videos = r2_storage.list_pending_uploads()
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)

        for video in pending_videos:
            try:
                processed_at = datetime.fromisoformat(video.get('processed_at', ''))
                if processed_at < cutoff_date:
                    if r2_storage.delete_upload(video['job_id']):
                        deleted_count += 1
            except:
                continue

        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f"Deleted {deleted_count} videos older than {days_old} days"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))