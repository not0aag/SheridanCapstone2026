import boto3
from botocore.exceptions import ClientError
import os
from app.config import settings

class S3Handler:
    """Handle S3 operations for video storage"""
    
    def __init__(self):
        self.use_s3 = getattr(settings, 'USE_S3', False)
        
        if self.use_s3:
            self.s3_client = boto3.client('s3')
            self.bucket_name = getattr(settings, 'S3_BUCKET_NAME', 'safedrive-videos-dev')
        else:
            # Use local storage for development
            self.local_storage_path = './videos'
            os.makedirs(self.local_storage_path, exist_ok=True)
    
    def upload_video(self, file_path: str, object_key: str) -> dict:
        """
        Upload video to S3 or local storage
        
        Args:
            file_path: Path to local video file
            object_key: S3 key (filename in bucket)
            
        Returns:
            dict with 'success', 'location', 'bucket', 'key'
        """
        try:
            if self.use_s3:
                # Upload to S3
                self.s3_client.upload_file(file_path, self.bucket_name, object_key)
                location = f"s3://{self.bucket_name}/{object_key}"
                return {
                    "success": True,
                    "location": location,
                    "bucket": self.bucket_name,
                    "key": object_key
                }
            else:
                # Save locally for development
                local_path = os.path.join(self.local_storage_path, object_key)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Copy file to local storage
                import shutil
                shutil.copy(file_path, local_path)
                
                return {
                    "success": True,
                    "location": f"local://{local_path}",
                    "bucket": "local",
                    "key": object_key
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_video_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generate pre-signed URL for video access
        
        Args:
            object_key: S3 key (filename)
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Pre-signed URL or local file path
        """
        try:
            if self.use_s3:
                # Generate pre-signed URL
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': object_key},
                    ExpiresIn=expiration
                )
                return url
            else:
                # Return local file path
                local_path = os.path.join(self.local_storage_path, object_key)
                return f"file://{local_path}"
                
        except Exception as e:
            raise Exception(f"Error generating video URL: {str(e)}")
    
    def delete_video(self, object_key: str) -> bool:
        """Delete video from S3 or local storage"""
        try:
            if self.use_s3:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            else:
                local_path = os.path.join(self.local_storage_path, object_key)
                if os.path.exists(local_path):
                    os.remove(local_path)
            return True
        except Exception as e:
            print(f"Error deleting video: {str(e)}")
            return False

# Global S3 handler instance
s3_handler = S3Handler()
