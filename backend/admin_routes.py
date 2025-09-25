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
router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin(token: str = Query(..., alias="auth")):
    """Simple admin authentication"""
    admin_token = os.getenv('ADMIN_TOKEN', 'admin-secret-token-change-this')
    print(f"DEBUG: Received token: '{token}'")
    print(f"DEBUG: Expected token: '{admin_token}'")
    print(f"DEBUG: Tokens match: {token == admin_token}")
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
    videos = []

    # Check environment to decide source
    is_development = os.getenv('ENVIRONMENT', 'development') == 'development'

    # In development, prefer local files even if R2 is configured
    if is_development or not r2_storage.is_configured():
        # Load from local temp directory
        from pathlib import Path
        import json

        # Load list of already approved videos
        approved_file = Path("temp") / "approved_videos.json"
        approved_videos = set()
        if approved_file.exists():
            try:
                with open(approved_file) as f:
                    approved_data = json.load(f)
                    approved_videos = set(approved_data.get('approved', []))
            except:
                pass

        temp_dir = Path("temp")
        if temp_dir.exists():
            for job_dir in temp_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    # Check for metadata file
                    metadata_file = job_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file) as f:
                                metadata = json.load(f)
                                # Add job_id if not present
                                metadata['job_id'] = job_dir.name
                                # Add URLs for local files
                                metadata['urls'] = {
                                    'thumbnail': f"/api/serve/{job_dir.name}/thumbnail.jpg",
                                    'preview': f"/api/serve/{job_dir.name}/preview.mp4",
                                    'full': f"/api/serve/{job_dir.name}/output.mp4"
                                }
                                # Mark if already approved
                                metadata['is_approved'] = job_dir.name in approved_videos

                                # Load saved name and category (check both gallery and a separate metadata file)
                                # First check gallery.json for approved videos
                                gallery_file = Path("temp") / "gallery.json"
                                if gallery_file.exists():
                                    try:
                                        with open(gallery_file) as f:
                                            gallery_data = json.load(f)
                                            for video in gallery_data.get('videos', []):
                                                if video.get('job_id') == job_dir.name:
                                                    metadata['saved_name'] = video.get('id', '')
                                                    metadata['saved_category'] = video.get('category', '')
                                                    metadata['saved_title'] = video.get('title', '')
                                                    break
                                    except:
                                        pass

                                # Also check for saved metadata file (for unapproved videos that had names before)
                                video_metadata_file = Path("temp") / "video_metadata.json"
                                if video_metadata_file.exists() and 'saved_name' not in metadata:
                                    try:
                                        with open(video_metadata_file) as f:
                                            video_metadata = json.load(f)
                                            if job_dir.name in video_metadata:
                                                metadata['saved_name'] = video_metadata[job_dir.name].get('name', '')
                                                metadata['saved_category'] = video_metadata[job_dir.name].get('category', '')
                                    except:
                                        pass

                                videos.append(metadata)
                        except Exception as e:
                            print(f"Error loading metadata for {job_dir.name}: {e}")
                            # Create basic metadata if file doesn't exist or is invalid
                            videos.append({
                                'job_id': job_dir.name,
                                'processed_at': datetime.now().isoformat(),
                                'statistics': {
                                    'detection_rate': 0.8,
                                    'average_quality': 0.75
                                },
                                'video_info': {
                                    'duration': 15,
                                    'size': 0
                                },
                                'urls': {
                                    'thumbnail': f"/api/serve/{job_dir.name}/thumbnail.jpg",
                                    'preview': f"/api/serve/{job_dir.name}/preview.mp4",
                                    'full': f"/api/serve/{job_dir.name}/output.mp4"
                                },
                                'is_approved': job_dir.name in approved_videos
                            })
    else:
        # In production, use R2 storage
        videos = r2_storage.list_pending_uploads()

    # Sort by processed date (newest first)
    videos.sort(key=lambda x: x.get('processed_at', ''), reverse=True)

    # Add detection rate for easier filtering
    for video in videos:
        stats = video.get('statistics', {})
        video['detection_rate'] = stats.get('detection_rate', 0)
        video['average_quality'] = stats.get('average_quality', 0)

    return {'videos': videos}


from pydantic import BaseModel

class ApproveRequest(BaseModel):
    job_id: str
    display_name: str
    category: str
    title: Optional[str] = None

@router.post("/approve-to-gallery")
async def approve_to_gallery(
    request: ApproveRequest,
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
        # Always use local URLs since we're not using R2
        urls = {
            'thumbnail': f"/api/serve/{request.job_id}/thumbnail.jpg",
            'preview': f"/api/serve/{request.job_id}/preview.mp4",
            'full': f"/api/serve/{request.job_id}/output.mp4"
        }

        # Prepare gallery metadata
        # For local development, always use local file paths
        local_urls = {
            'thumbnail': f"/api/serve/{request.job_id}/thumbnail.jpg",
            'preview': f"/api/serve/{request.job_id}/preview.mp4",
            'full': f"/api/serve/{request.job_id}/output.mp4",
        }

        gallery_entry = {
            'id': request.display_name,
            'title': request.title or request.display_name.replace('-', ' ').title(),
            'category': request.category,
            'thumbnail': local_urls.get('thumbnail', ''),
            'preview': local_urls.get('preview', ''),
            'full': local_urls.get('full', ''),
            'job_id': request.job_id,  # Store job_id for file serving
            'added_at': datetime.now().isoformat(),
            'accuracy': 95.0,
            'views': '0',
            'likes': '0',
            'duration': '0:30'
        }

        # Try to get actual statistics from local metadata
        try:
            # Load from local pending videos
            pending_videos = []
            temp_dir = Path("temp")
            if temp_dir.exists():
                metadata_file = temp_dir / request.job_id / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        metadata['job_id'] = request.job_id
                        pending_videos.append(metadata)

            for video in pending_videos:
                if video['job_id'] == request.job_id:
                    stats = video.get('statistics', {})
                    gallery_entry['accuracy'] = round(stats.get('detection_rate', 0) * 100, 1)
                    video_info = video.get('video_info', {})
                    duration = video_info.get('duration', 30)
                    gallery_entry['duration'] = f"{int(duration // 60)}:{int(duration % 60):02d}"
                    break
        except:
            pass

        # Always save locally for local development
        from pathlib import Path
        import json

        gallery_file = Path("temp") / "gallery.json"

        # Load existing gallery or create new
        if gallery_file.exists():
            with open(gallery_file) as f:
                gallery_data = json.load(f)
        else:
            gallery_data = {"videos": []}

        # Add new entry
        gallery_data["videos"].insert(0, gallery_entry)

        # Save updated gallery
        with open(gallery_file, 'w') as f:
            json.dump(gallery_data, f, indent=2)

        # Track approved videos
        approved_file = Path("temp") / "approved_videos.json"
        approved_data = {'approved': []}
        if approved_file.exists():
            try:
                with open(approved_file) as f:
                    approved_data = json.load(f)
            except:
                pass

        # Add this video to approved list
        if request.job_id not in approved_data.get('approved', []):
            approved_data.setdefault('approved', []).append(request.job_id)
            with open(approved_file, 'w') as f:
                json.dump(approved_data, f, indent=2)

        success = True

        return {
            'success': success,
            'gallery_entry': gallery_entry,
            'message': f"Video '{request.display_name}' added to gallery"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unapprove/{job_id}")
async def unapprove_video(job_id: str, auth: bool = Depends(verify_admin)):
    """
    Remove video from gallery (unapprove it)

    Args:
        job_id: Job ID to remove from gallery

    Returns:
        Success status
    """
    try:
        from pathlib import Path
        import json

        # Remove from approved list
        approved_file = Path("temp") / "approved_videos.json"
        if approved_file.exists():
            with open(approved_file) as f:
                approved_data = json.load(f)

            approved_list = approved_data.get('approved', [])
            if job_id in approved_list:
                approved_list.remove(job_id)
                approved_data['approved'] = approved_list

                with open(approved_file, 'w') as f:
                    json.dump(approved_data, f, indent=2)

        # Save the name and category before removing from gallery
        saved_name = ''
        saved_category = ''

        # Remove from gallery
        gallery_file = Path("temp") / "gallery.json"
        if gallery_file.exists():
            with open(gallery_file) as f:
                gallery_data = json.load(f)

            # Find and save the video metadata before removing
            for video in gallery_data.get('videos', []):
                if video.get('job_id') == job_id:
                    saved_name = video.get('id', '')
                    saved_category = video.get('category', '')
                    break

            # Filter out this video
            gallery_data['videos'] = [
                v for v in gallery_data.get('videos', [])
                if v.get('job_id') != job_id
            ]

            with open(gallery_file, 'w') as f:
                json.dump(gallery_data, f, indent=2)

        # Save the metadata for future use
        if saved_name or saved_category:
            video_metadata_file = Path("temp") / "video_metadata.json"
            video_metadata = {}
            if video_metadata_file.exists():
                try:
                    with open(video_metadata_file) as f:
                        video_metadata = json.load(f)
                except:
                    pass

            video_metadata[job_id] = {
                'name': saved_name,
                'category': saved_category
            }

            with open(video_metadata_file, 'w') as f:
                json.dump(video_metadata, f, indent=2)

        return {
            'success': True,
            'message': f"Video {job_id} removed from gallery"
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
    import shutil
    from pathlib import Path

    # Delete from R2 if configured
    r2_deleted = False
    if r2_storage.is_configured():
        r2_deleted = r2_storage.delete_upload(job_id)

    # Always delete local files
    local_path = Path("temp") / job_id
    local_deleted = False
    if local_path.exists():
        try:
            shutil.rmtree(local_path)
            local_deleted = True
        except Exception as e:
            print(f"Error deleting local files: {e}")

    if r2_storage.is_configured():
        # Production mode - both should be deleted
        if r2_deleted and local_deleted:
            return {'success': True, 'message': f"Video {job_id} deleted from cloud and local storage"}
        elif r2_deleted:
            return {'success': True, 'message': f"Video {job_id} deleted from cloud (no local files found)"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete video from cloud")
    else:
        # Local mode - only local files matter
        if local_deleted:
            return {'success': True, 'message': f"Video {job_id} deleted from local storage"}
        else:
            return {'success': True, 'message': f"Video {job_id} not found in local storage"}


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
        import shutil
        from pathlib import Path

        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)

        if r2_storage.is_configured():
            # Production: Clean up R2 and local
            pending_videos = r2_storage.list_pending_uploads()

            for video in pending_videos:
                try:
                    processed_at = datetime.fromisoformat(video.get('processed_at', ''))
                    if processed_at < cutoff_date:
                        job_id = video['job_id']
                        # Delete from R2
                        if r2_storage.delete_upload(job_id):
                            deleted_count += 1
                        # Also delete local files
                        local_path = Path("temp") / job_id
                        if local_path.exists():
                            shutil.rmtree(local_path, ignore_errors=True)
                except:
                    continue
        else:
            # Local mode: Clean up local temp directory
            temp_dir = Path("temp")
            if temp_dir.exists():
                for job_dir in temp_dir.iterdir():
                    if job_dir.is_dir():
                        try:
                            # Check metadata file for date
                            metadata_file = job_dir / "metadata.json"
                            if metadata_file.exists():
                                with open(metadata_file) as f:
                                    metadata = json.load(f)
                                processed_at = datetime.fromisoformat(metadata.get('processed_at', ''))
                                if processed_at < cutoff_date:
                                    shutil.rmtree(job_dir)
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