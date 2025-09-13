"""
TalkingPhoto AI MVP - File Service
AWS S3 integration with CDN support and local fallback
"""

import os
import boto3
import hashlib
from datetime import datetime, timedelta
from flask import current_app
from botocore.exceptions import ClientError, NoCredentialsError
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()


class FileService:
    """
    File storage service with S3 and local storage support
    """
    
    def __init__(self):
        self.s3_client = None
        self.bucket_name = current_app.config.get('S3_BUCKET_NAME')
        self.cloudfront_domain = current_app.config.get('CLOUDFRONT_DOMAIN')
        self.use_s3 = bool(self.bucket_name and current_app.config.get('AWS_ACCESS_KEY_ID'))
        
        if self.use_s3:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=current_app.config.get('AWS_REGION', 'us-east-1')
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize S3 client", error=str(e))
                self.use_s3 = False
        
        # Ensure local upload directory exists
        self.local_upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(self.local_upload_dir, exist_ok=True)
    
    def store_file(self, file_content: bytes, filename: str, content_type: str, 
                   folder: str = '') -> Dict[str, Any]:
        """
        Store file using S3 or local storage with automatic fallback
        """
        try:
            if self.use_s3:
                return self._store_file_s3(file_content, filename, content_type, folder)
            else:
                return self._store_file_local(file_content, filename, content_type, folder)
        except Exception as e:
            logger.error("File storage failed", filename=filename, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _store_file_s3(self, file_content: bytes, filename: str, content_type: str, 
                       folder: str = '') -> Dict[str, Any]:
        """
        Store file in AWS S3
        """
        try:
            # Generate S3 key with folder structure
            s3_key = self._generate_s3_key(filename, folder)
            
            # Calculate file hash for integrity
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Upload to S3
            extra_args = {
                'ContentType': content_type,
                'Metadata': {
                    'original-filename': filename,
                    'upload-timestamp': datetime.utcnow().isoformat(),
                    'file-hash': file_hash
                }
            }
            
            # Set cache control for images and videos
            if content_type.startswith(('image/', 'video/')):
                extra_args['CacheControl'] = 'max-age=31536000'  # 1 year
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                **extra_args
            )
            
            # Generate URLs
            s3_url = f"https://s3.{current_app.config.get('AWS_REGION', 'us-east-1')}.amazonaws.com/{self.bucket_name}/{s3_key}"
            cdn_url = None
            
            if self.cloudfront_domain:
                cdn_url = f"https://{self.cloudfront_domain}/{s3_key}"
            
            logger.info("File stored successfully in S3", 
                       filename=filename, s3_key=s3_key)
            
            return {
                'success': True,
                'path': s3_key,
                'url': s3_url,
                'cdn_url': cdn_url,
                'storage_provider': 's3',
                'file_hash': file_hash
            }
            
        except NoCredentialsError:
            logger.error("AWS credentials not found, falling back to local storage")
            self.use_s3 = False
            return self._store_file_local(file_content, filename, content_type, folder)
        except ClientError as e:
            logger.error("S3 upload failed", error=str(e), filename=filename)
            return {'success': False, 'error': f'S3 upload failed: {str(e)}'}
        except Exception as e:
            logger.error("Unexpected error during S3 upload", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _store_file_local(self, file_content: bytes, filename: str, content_type: str, 
                         folder: str = '') -> Dict[str, Any]:
        """
        Store file locally with folder organization
        """
        try:
            # Create folder structure
            storage_folder = os.path.join(self.local_upload_dir, folder) if folder else self.local_upload_dir
            os.makedirs(storage_folder, exist_ok=True)
            
            # Generate local file path
            file_path = os.path.join(storage_folder, filename)
            
            # Ensure filename is unique
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(file_path):
                new_filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(storage_folder, new_filename)
                filename = new_filename
                counter += 1
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Calculate file hash
            file_hash = hashlib.md5(file_content).hexdigest()
            
            logger.info("File stored successfully locally", 
                       filename=filename, path=file_path)
            
            return {
                'success': True,
                'path': file_path,
                'url': None,  # Local files don't have public URLs by default
                'cdn_url': None,
                'storage_provider': 'local',
                'file_hash': file_hash
            }
            
        except Exception as e:
            logger.error("Local file storage failed", error=str(e), filename=filename)
            return {'success': False, 'error': str(e)}
    
    def get_file_content(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve file content from storage
        """
        try:
            if self.use_s3 and not file_path.startswith('/'):
                # S3 path
                return self._get_file_content_s3(file_path)
            else:
                # Local path
                return self._get_file_content_local(file_path)
        except Exception as e:
            logger.error("File retrieval failed", path=file_path, error=str(e))
            return None
    
    def _get_file_content_s3(self, s3_key: str) -> Optional[bytes]:
        """
        Get file content from S3
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            logger.error("S3 file retrieval failed", s3_key=s3_key, error=str(e))
            return None
    
    def _get_file_content_local(self, file_path: str) -> Optional[bytes]:
        """
        Get file content from local storage
        """
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error("Local file retrieval failed", path=file_path, error=str(e))
            return None
    
    def generate_signed_url(self, file_path: str, expiration_hours: int = 1) -> Optional[str]:
        """
        Generate signed URL for secure file access
        """
        try:
            if self.use_s3 and not file_path.startswith('/'):
                # S3 signed URL
                return self._generate_s3_signed_url(file_path, expiration_hours)
            else:
                # For local files, would need to implement token-based access
                # For MVP, return None (files should be served through Flask routes)
                return None
        except Exception as e:
            logger.error("Signed URL generation failed", path=file_path, error=str(e))
            return None
    
    def _generate_s3_signed_url(self, s3_key: str, expiration_hours: int) -> Optional[str]:
        """
        Generate S3 pre-signed URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration_hours * 3600
            )
            return url
        except Exception as e:
            logger.error("S3 signed URL generation failed", s3_key=s3_key, error=str(e))
            return None
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete file from storage
        """
        try:
            if self.use_s3 and not file_path.startswith('/'):
                return self._delete_file_s3(file_path)
            else:
                return self._delete_file_local(file_path)
        except Exception as e:
            logger.error("File deletion failed", path=file_path, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _delete_file_s3(self, s3_key: str) -> Dict[str, Any]:
        """
        Delete file from S3
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info("File deleted from S3", s3_key=s3_key)
            return {'success': True}
        except Exception as e:
            logger.error("S3 file deletion failed", s3_key=s3_key, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _delete_file_local(self, file_path: str) -> Dict[str, Any]:
        """
        Delete local file
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Local file deleted", path=file_path)
            return {'success': True}
        except Exception as e:
            logger.error("Local file deletion failed", path=file_path, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _generate_s3_key(self, filename: str, folder: str = '') -> str:
        """
        Generate S3 key with organized folder structure
        """
        # Organize files by date and type
        now = datetime.utcnow()
        date_folder = f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        if folder:
            return f"{folder}/{date_folder}/{filename}"
        else:
            # Auto-detect folder based on content type
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                folder = 'images'
            elif filename.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
                folder = 'videos'
            else:
                folder = 'files'
            
            return f"{folder}/{date_folder}/{filename}"
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get file information and metadata
        """
        try:
            if self.use_s3 and not file_path.startswith('/'):
                return self._get_s3_file_info(file_path)
            else:
                return self._get_local_file_info(file_path)
        except Exception as e:
            logger.error("File info retrieval failed", path=file_path, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _get_s3_file_info(self, s3_key: str) -> Dict[str, Any]:
        """
        Get S3 file information
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'success': True,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {}),
                'etag': response['ETag'].strip('"')
            }
        except Exception as e:
            logger.error("S3 file info retrieval failed", s3_key=s3_key, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _get_local_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get local file information
        """
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            stat = os.stat(file_path)
            
            return {
                'success': True,
                'size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime)
            }
        except Exception as e:
            logger.error("Local file info retrieval failed", path=file_path, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def cleanup_expired_files(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Cleanup files older than specified days (for data retention compliance)
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = 0
            
            if self.use_s3:
                # List and delete old S3 objects
                paginator = self.s3_client.get_paginator('list_objects_v2')
                
                for page in paginator.paginate(Bucket=self.bucket_name):
                    if 'Contents' not in page:
                        continue
                    
                    for obj in page['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            self.s3_client.delete_object(
                                Bucket=self.bucket_name, 
                                Key=obj['Key']
                            )
                            deleted_count += 1
            else:
                # Cleanup local files
                for root, dirs, files in os.walk(self.local_upload_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) < cutoff_date.timestamp():
                            os.remove(file_path)
                            deleted_count += 1
            
            logger.info("File cleanup completed", deleted_count=deleted_count)
            return {'success': True, 'deleted_count': deleted_count}
            
        except Exception as e:
            logger.error("File cleanup failed", error=str(e))
            return {'success': False, 'error': str(e)}