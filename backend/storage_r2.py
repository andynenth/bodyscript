"""
Cloudflare R2 Storage Integration for BodyScript
Handles video storage, gallery management, and file operations
"""

import boto3
import os
import json
import tempfile
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class R2Storage:
    """Manages file storage in Cloudflare R2 buckets"""

    def __init__(self):
        """Initialize R2 client with credentials from environment"""
        self.account_id = os.getenv('R2_ACCOUNT_ID')
        self.access_key = os.getenv('R2_ACCESS_KEY')
        self.secret_key = os.getenv('R2_SECRET_KEY')

        # Initialize S3 client (R2 is S3-compatible)
        # Check if credentials are real values (not placeholders)
        if (self.account_id and self.access_key and self.secret_key and
            'your_' not in self.account_id and
            'your_' not in self.access_key and
            'your_' not in self.secret_key):
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name='auto'
            )
        else:
            print("Warning: R2 credentials not configured. Storage disabled.")
            self.s3_client = None

        # Bucket names
        self.upload_bucket = 'bodyscript-uploads'
        self.gallery_bucket = 'bodyscript-gallery'

        # Public domain (update after R2 setup)
        self.public_domain = os.getenv('R2_PUBLIC_DOMAIN', 'https://gallery.bodyscript.com')

    def is_configured(self) -> bool:
        """Check if R2 storage is properly configured"""
        return self.s3_client is not None

    def upload_file(self, local_path: str, remote_path: str,
                   bucket: str = None) -> Optional[str]:
        """
        Upload file to R2 and return public URL

        Args:
            local_path: Path to local file
            remote_path: Path in R2 bucket
            bucket: Bucket name (defaults to upload_bucket)

        Returns:
            Public URL or signed URL depending on bucket
        """
        if not self.is_configured():
            print("R2 not configured, skipping upload")
            return None

        bucket = bucket or self.upload_bucket

        try:
            # Upload file
            self.s3_client.upload_file(local_path, bucket, remote_path)

            # Return appropriate URL
            if bucket == self.gallery_bucket:
                # Gallery bucket is public
                return f"{self.public_domain}/{remote_path}"
            else:
                # Upload bucket needs signed URL (7 days expiry)
                return self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': remote_path},
                    ExpiresIn=604800  # 7 days
                )
        except Exception as e:
            print(f"Failed to upload {local_path}: {e}")
            return None

    def copy_to_gallery(self, job_id: str, display_name: str) -> Dict[str, str]:
        """
        Copy video from uploads to gallery with new name

        Args:
            job_id: Original job ID in uploads bucket
            display_name: New display name for gallery

        Returns:
            Dictionary of URLs for gallery files
        """
        if not self.is_configured():
            return {}

        urls = {}
        files_to_copy = {
            'thumbnail': 'thumbnail.jpg',
            'preview': 'preview.mp4',
            'full': 'full.mp4',
            'metadata': 'metadata.json'
        }

        for key, filename in files_to_copy.items():
            try:
                # Source and destination paths
                source = {'Bucket': self.upload_bucket, 'Key': f"{job_id}/{filename}"}
                dest_key = f"gallery/{display_name}/{filename}"

                # Copy object
                self.s3_client.copy_object(
                    CopySource=source,
                    Bucket=self.gallery_bucket,
                    Key=dest_key
                )

                # Store public URL
                urls[key] = f"{self.public_domain}/{dest_key}"

            except Exception as e:
                print(f"Failed to copy {filename}: {e}")

        return urls

    def delete_upload(self, job_id: str) -> bool:
        """
        Delete all files for a job from uploads bucket

        Args:
            job_id: Job ID to delete

        Returns:
            True if successful
        """
        if not self.is_configured():
            return False

        try:
            # List all objects with job_id prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.upload_bucket,
                Prefix=f"{job_id}/"
            )

            if 'Contents' in response:
                # Delete all objects
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                self.s3_client.delete_objects(
                    Bucket=self.upload_bucket,
                    Delete={'Objects': objects}
                )

            return True

        except Exception as e:
            print(f"Failed to delete {job_id}: {e}")
            return False

    def list_pending_uploads(self) -> List[Dict]:
        """
        List all pending videos in uploads bucket

        Returns:
            List of video metadata dictionaries
        """
        if not self.is_configured():
            return []

        videos = []

        try:
            # List all folders (job IDs) in upload bucket
            response = self.s3_client.list_objects_v2(
                Bucket=self.upload_bucket,
                Delimiter='/'
            )

            if 'CommonPrefixes' in response:
                for prefix in response['CommonPrefixes']:
                    job_id = prefix['Prefix'].rstrip('/')

                    # Try to get metadata for this job
                    try:
                        metadata_obj = self.s3_client.get_object(
                            Bucket=self.upload_bucket,
                            Key=f"{job_id}/metadata.json"
                        )
                        metadata = json.loads(metadata_obj['Body'].read())

                        videos.append({
                            'job_id': job_id,
                            'processed_at': metadata.get('processed_at'),
                            'statistics': metadata.get('statistics', {}),
                            'urls': metadata.get('urls', {}),
                            'video_info': metadata.get('video_info', {})
                        })
                    except:
                        # Skip if metadata not found
                        continue

        except Exception as e:
            print(f"Failed to list uploads: {e}")

        return videos

    def update_gallery_json(self, video_data: Dict) -> bool:
        """
        Update the gallery.json file with new video

        Args:
            video_data: Video information to add

        Returns:
            True if successful
        """
        if not self.is_configured():
            return False

        try:
            # Download current gallery.json
            gallery = {'videos': []}

            try:
                obj = self.s3_client.get_object(
                    Bucket=self.gallery_bucket,
                    Key='gallery.json'
                )
                gallery = json.loads(obj['Body'].read())
            except:
                # File doesn't exist yet, use empty gallery
                pass

            # Add new video at the beginning
            gallery['videos'].insert(0, video_data)

            # Keep only latest 50 videos
            gallery['videos'] = gallery['videos'][:50]

            # Upload updated gallery.json
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(gallery, f, indent=2)
                temp_path = f.name

            self.s3_client.upload_file(
                temp_path,
                self.gallery_bucket,
                'gallery.json',
                ExtraArgs={'ContentType': 'application/json'}
            )

            # Clean up temp file
            os.unlink(temp_path)

            return True

        except Exception as e:
            print(f"Failed to update gallery.json: {e}")
            return False


# Global instance
r2_storage = R2Storage()