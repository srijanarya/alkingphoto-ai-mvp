"""
TalkingPhoto AI MVP - File Service Unit Tests
Comprehensive tests for file upload, storage, and management
"""

import pytest
import os
import tempfile
import hashlib
from unittest.mock import Mock, patch, mock_open
from PIL import Image
import io

from services.file_service import FileService
from models.file import UploadedFile, FileType, FileStatus
from models.user import User, SubscriptionTier


class TestFileService:
    """Test file service functionality"""
    
    @pytest.fixture
    def file_service(self):
        with patch('services.file_service.current_app') as mock_app:
            mock_app.config.get.side_effect = lambda key: {
                'UPLOAD_FOLDER': '/tmp/test_uploads',
                'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB
                'ALLOWED_EXTENSIONS': {'jpg', 'jpeg', 'png', 'gif', 'webp'},
                'CDN_BASE_URL': 'https://cdn.example.com'
            }.get(key, 'default_value')
            return FileService()
    
    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data"""
        img = Image.new('RGB', (1920, 1080), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        return img_buffer.getvalue()
    
    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(
            id='file_test_user',
            email='filetest@example.com',
            password='TestPassword123!',
            subscription_tier=SubscriptionTier.FREE,
            credits_remaining=5
        )
        db_session.add(user)
        db_session.commit()
        return user

    def test_validate_file_type_valid_images(self, file_service):
        """Test file type validation for valid image formats"""
        valid_files = [
            ('image.jpg', 'image/jpeg'),
            ('photo.jpeg', 'image/jpeg'),
            ('picture.png', 'image/png'),
            ('graphic.gif', 'image/gif'),
            ('modern.webp', 'image/webp')
        ]
        
        for filename, content_type in valid_files:
            result = file_service.validate_file_type(filename, content_type)
            assert result['valid'] is True
            assert result['file_type'] == FileType.IMAGE
    
    def test_validate_file_type_invalid_formats(self, file_service):
        """Test file type validation for invalid formats"""
        invalid_files = [
            ('document.pdf', 'application/pdf'),
            ('video.mp4', 'video/mp4'),
            ('audio.mp3', 'audio/mpeg'),
            ('script.exe', 'application/x-executable'),
            ('data.txt', 'text/plain')
        ]
        
        for filename, content_type in invalid_files:
            result = file_service.validate_file_type(filename, content_type)
            assert result['valid'] is False
            assert 'not supported' in result['error'].lower()
    
    def test_validate_file_size_within_limits(self, file_service):
        """Test file size validation within limits"""
        # Test various file sizes within the 10MB limit
        valid_sizes = [
            1024,          # 1KB
            1024 * 1024,   # 1MB
            5 * 1024 * 1024,   # 5MB
            9 * 1024 * 1024    # 9MB
        ]
        
        for size in valid_sizes:
            result = file_service.validate_file_size(size)
            assert result['valid'] is True
    
    def test_validate_file_size_exceeds_limits(self, file_service):
        """Test file size validation for oversized files"""
        invalid_sizes = [
            11 * 1024 * 1024,  # 11MB
            50 * 1024 * 1024,  # 50MB
            100 * 1024 * 1024  # 100MB
        ]
        
        for size in invalid_sizes:
            result = file_service.validate_file_size(size)
            assert result['valid'] is False
            assert 'too large' in result['error'].lower()
    
    def test_generate_secure_filename(self, file_service):
        """Test secure filename generation"""
        test_cases = [
            ('simple.jpg', 'simple.jpg'),
            ('with spaces.png', 'with_spaces.png'),
            ('special!@#$%.jpeg', 'special.jpeg'),
            ('../../malicious.jpg', 'malicious.jpg'),
            ('very_long_filename_that_might_cause_issues.jpg', 'very_long_filename_that_might_cause_issues.jpg')
        ]
        
        for original, expected_pattern in test_cases:
            result = file_service.generate_secure_filename(original)
            
            # Should not contain dangerous characters
            assert '..' not in result
            assert '/' not in result
            assert '\\' not in result
            
            # Should preserve extension
            if '.' in original:
                original_ext = original.split('.')[-1].lower()
                result_ext = result.split('.')[-1].lower()
                assert original_ext == result_ext
            
            # Should be unique when called multiple times
            result2 = file_service.generate_secure_filename(original)
            assert result != result2  # Should include timestamp or UUID
    
    def test_calculate_file_hash(self, file_service, sample_image_data):
        """Test file hash calculation"""
        hash_result = file_service.calculate_file_hash(sample_image_data)
        
        # Should return a valid SHA-256 hash
        assert len(hash_result) == 64  # SHA-256 produces 64-character hex string
        assert all(c in '0123456789abcdef' for c in hash_result)
        
        # Same data should produce same hash
        hash_result2 = file_service.calculate_file_hash(sample_image_data)
        assert hash_result == hash_result2
        
        # Different data should produce different hash
        different_data = b'different content'
        different_hash = file_service.calculate_file_hash(different_data)
        assert hash_result != different_hash
    
    def test_extract_image_metadata(self, file_service, sample_image_data):
        """Test image metadata extraction"""
        metadata = file_service.extract_image_metadata(sample_image_data)
        
        assert metadata['width'] == 1920
        assert metadata['height'] == 1080
        assert metadata['format'] == 'JPEG'
        assert metadata['mode'] == 'RGB'
        assert 'file_size' in metadata
        assert metadata['file_size'] > 0
    
    def test_extract_image_metadata_invalid_data(self, file_service):
        """Test image metadata extraction with invalid data"""
        invalid_data = b'not an image'
        metadata = file_service.extract_image_metadata(invalid_data)
        
        # Should return None or empty dict for invalid image data
        assert metadata is None or metadata == {}
    
    def test_store_file_locally(self, file_service, sample_image_data, temp_upload_dir):
        """Test local file storage"""
        filename = 'test_store.jpg'
        content_type = 'image/jpeg'
        
        with patch.object(file_service, 'upload_folder', temp_upload_dir):
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.open', mock_open()) as mock_file:
                    result = file_service.store_file_locally(
                        sample_image_data, filename, content_type
                    )
        
        assert result['success'] is True
        assert 'path' in result
        assert 'url' in result
        assert filename in result['path']
        mock_file.assert_called_once()
    
    def test_store_file_locally_directory_creation(self, file_service, sample_image_data):
        """Test that storage creates necessary directories"""
        filename = 'test_dir.jpg'
        content_type = 'image/jpeg'
        
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('os.path.exists', return_value=False):
                    result = file_service.store_file_locally(
                        sample_image_data, filename, content_type
                    )
        
        mock_makedirs.assert_called_once()
        assert result['success'] is True
    
    def test_store_file_s3_success(self, file_service, sample_image_data):
        """Test S3 file storage success"""
        filename = 'test_s3.jpg'
        content_type = 'image/jpeg'
        
        with patch('boto3.client') as mock_boto:
            mock_s3 = Mock()
            mock_boto.return_value = mock_s3
            mock_s3.upload_fileobj.return_value = None
            
            result = file_service.store_file_s3(sample_image_data, filename, content_type)
        
        assert result['success'] is True
        assert 'path' in result
        assert 'url' in result
        assert 'cdn_url' in result
        mock_s3.upload_fileobj.assert_called_once()
    
    def test_store_file_s3_failure(self, file_service, sample_image_data):
        """Test S3 file storage failure handling"""
        filename = 'test_s3_fail.jpg'
        content_type = 'image/jpeg'
        
        with patch('boto3.client') as mock_boto:
            mock_s3 = Mock()
            mock_boto.return_value = mock_s3
            mock_s3.upload_fileobj.side_effect = Exception('S3 connection failed')
            
            result = file_service.store_file_s3(sample_image_data, filename, content_type)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'S3 connection failed' in result['error']
    
    def test_get_file_content_local(self, file_service, sample_image_data, temp_upload_dir):
        """Test getting file content from local storage"""
        file_path = os.path.join(temp_upload_dir, 'test_content.jpg')
        
        # Write test file
        with open(file_path, 'wb') as f:
            f.write(sample_image_data)
        
        content = file_service.get_file_content(file_path)
        assert content == sample_image_data
    
    def test_get_file_content_nonexistent(self, file_service):
        """Test getting content from non-existent file"""
        content = file_service.get_file_content('/nonexistent/path/file.jpg')
        assert content is None
    
    def test_delete_file_local(self, file_service, temp_upload_dir):
        """Test local file deletion"""
        file_path = os.path.join(temp_upload_dir, 'test_delete.jpg')
        
        # Create test file
        with open(file_path, 'w') as f:
            f.write('test content')
        
        assert os.path.exists(file_path)
        
        result = file_service.delete_file(file_path)
        assert result['success'] is True
        assert not os.path.exists(file_path)
    
    def test_delete_file_s3(self, file_service):
        """Test S3 file deletion"""
        s3_path = 's3://bucket/path/file.jpg'
        
        with patch('boto3.client') as mock_boto:
            mock_s3 = Mock()
            mock_boto.return_value = mock_s3
            mock_s3.delete_object.return_value = None
            
            result = file_service.delete_file(s3_path)
        
        assert result['success'] is True
        mock_s3.delete_object.assert_called_once()
    
    def test_upload_file_complete_workflow(self, file_service, sample_image_data, test_user, db_session):
        """Test complete file upload workflow"""
        filename = 'complete_test.jpg'
        content_type = 'image/jpeg'
        
        with patch.object(file_service, 'store_file') as mock_store:
            mock_store.return_value = {
                'success': True,
                'path': '/uploads/complete_test_unique.jpg',
                'url': 'https://example.com/uploads/complete_test_unique.jpg',
                'cdn_url': 'https://cdn.example.com/complete_test_unique.jpg'
            }
            
            result = file_service.upload_file(
                file_content=sample_image_data,
                filename=filename,
                content_type=content_type,
                user_id=test_user.id
            )
        
        assert result['success'] is True
        assert 'file_id' in result
        assert 'url' in result
        
        # Verify file record was created in database
        uploaded_file = UploadedFile.query.filter_by(id=result['file_id']).first()
        assert uploaded_file is not None
        assert uploaded_file.user_id == test_user.id
        assert uploaded_file.original_filename == filename
        assert uploaded_file.mime_type == content_type
        assert uploaded_file.file_type == FileType.IMAGE
        assert uploaded_file.status == FileStatus.ACTIVE
    
    def test_upload_file_validation_failures(self, file_service, test_user):
        """Test upload failures due to validation"""
        # Test invalid file type
        invalid_content = b'not an image'
        result = file_service.upload_file(
            file_content=invalid_content,
            filename='document.pdf',
            content_type='application/pdf',
            user_id=test_user.id
        )
        assert result['success'] is False
        assert 'not supported' in result['error']
        
        # Test oversized file
        large_content = b'0' * (15 * 1024 * 1024)  # 15MB
        result = file_service.upload_file(
            file_content=large_content,
            filename='large.jpg',
            content_type='image/jpeg',
            user_id=test_user.id
        )
        assert result['success'] is False
        assert 'too large' in result['error']
    
    def test_get_user_files(self, file_service, test_user, db_session):
        """Test retrieving user's files"""
        # Create test files
        files = []
        for i in range(3):
            file = UploadedFile(
                user_id=test_user.id,
                original_filename=f'test_{i}.jpg',
                filename=f'test_{i}_unique.jpg',
                file_type=FileType.IMAGE,
                mime_type='image/jpeg',
                file_size=1024000,
                file_hash=f'hash_{i}',
                storage_path=f'/uploads/test_{i}_unique.jpg'
            )
            files.append(file)
            db_session.add(file)
        
        db_session.commit()
        
        user_files = file_service.get_user_files(test_user.id)
        
        assert len(user_files) == 3
        for file_data in user_files:
            assert 'id' in file_data
            assert 'original_filename' in file_data
            assert 'file_size' in file_data
            assert 'created_at' in file_data
    
    def test_cleanup_expired_files(self, file_service, test_user, db_session):
        """Test cleanup of expired temporary files"""
        from datetime import datetime, timezone, timedelta
        
        # Create expired file
        expired_file = UploadedFile(
            user_id=test_user.id,
            original_filename='expired.jpg',
            filename='expired_unique.jpg',
            file_type=FileType.IMAGE,
            mime_type='image/jpeg',
            file_size=1024000,
            file_hash='expired_hash',
            storage_path='/uploads/expired_unique.jpg',
            status=FileStatus.TEMPORARY,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        
        # Create recent file
        recent_file = UploadedFile(
            user_id=test_user.id,
            original_filename='recent.jpg',
            filename='recent_unique.jpg',
            file_type=FileType.IMAGE,
            mime_type='image/jpeg',
            file_size=1024000,
            file_hash='recent_hash',
            storage_path='/uploads/recent_unique.jpg',
            status=FileStatus.TEMPORARY,
            created_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        db_session.add_all([expired_file, recent_file])
        db_session.commit()
        
        with patch.object(file_service, 'delete_file') as mock_delete:
            mock_delete.return_value = {'success': True}
            
            cleaned_count = file_service.cleanup_expired_files()
        
        assert cleaned_count == 1  # Only expired file should be cleaned
        mock_delete.assert_called_once_with('/uploads/expired_unique.jpg')
        
        # Verify file status updated
        db_session.refresh(expired_file)
        assert expired_file.status == FileStatus.DELETED