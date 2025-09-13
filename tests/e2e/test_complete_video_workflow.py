"""
TalkingPhoto AI MVP - End-to-End Video Generation Workflow Tests
Complete user journey tests from registration to video download
"""

import pytest
import os
import time
import json
import tempfile
from unittest.mock import Mock, patch
import streamlit as st
from PIL import Image
import io

from tests.mocks.ai_providers import create_ai_service_mocks
from core.credits import CreditTier, TransactionManager
from models.user import User, SubscriptionTier
from models.video import VideoGeneration, AIProvider, VideoStatus, VideoQuality, AspectRatio
from models.file import UploadedFile, FileType, FileStatus


@pytest.mark.e2e
class TestCompleteVideoWorkflow:
    """End-to-end tests for complete video generation workflow"""
    
    @pytest.fixture(scope="class")
    def ai_mocks(self):
        """Create AI service mocks for E2E testing"""
        return create_ai_service_mocks(failure_rates={
            'nano_banana': 0.02,  # 2% failure rate
            'veo3': 0.05,         # 5% failure rate
            'runway': 0.03,       # 3% failure rate
            'elevenlabs': 0.01,   # 1% failure rate
            'azure_speech': 0.01, # 1% failure rate
            'stripe': 0.02        # 2% payment failure rate
        })
    
    @pytest.fixture
    def test_image_file(self, temp_upload_dir):
        """Create a test image file"""
        # Create a simple test image
        img = Image.new('RGB', (1920, 1080), color='blue')
        image_path = os.path.join(temp_upload_dir, 'test_portrait.jpg')
        img.save(image_path, 'JPEG')
        return image_path
    
    @pytest.fixture
    def new_user_data(self):
        """Test data for new user registration"""
        return {
            'email': 'e2e_user@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'E2E',
            'last_name': 'Test',
            'gdpr_consent': True
        }

    def test_new_user_complete_journey(self, client, ai_mocks, test_image_file, new_user_data):
        """Test complete journey for a new user from registration to video creation"""
        
        # Step 1: User Registration
        response = client.post('/api/auth/register', json=new_user_data)
        assert response.status_code == 201
        user_data = response.json['user']
        user_id = user_data['id']
        
        # Verify user starts with free tier
        assert user_data['subscription_tier'] == 'free'
        assert user_data['credits_remaining'] == 1
        
        # Step 2: User Login
        login_response = client.post('/api/auth/login', json={
            'email': new_user_data['email'],
            'password': new_user_data['password']
        })
        assert login_response.status_code == 200
        auth_token = login_response.json['tokens']['access_token']
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Step 3: Upload Image
        with open(test_image_file, 'rb') as f:
            files = {'file': ('test_portrait.jpg', f, 'image/jpeg')}
            upload_response = client.post('/api/upload', files=files, headers=headers)
        
        assert upload_response.status_code == 200
        file_data = upload_response.json
        assert file_data['success'] is True
        file_id = file_data['file_id']
        
        # Step 4: Create Video Generation Request
        video_request = {
            'source_file_id': file_id,
            'script_text': 'Hello everyone! Welcome to our amazing AI video platform. This technology can bring any photo to life with natural speech and realistic animations.',
            'ai_provider': 'veo3',
            'video_quality': 'standard',
            'aspect_ratio': 'landscape',
            'voice_settings': {
                'provider': 'azure',
                'voice_name': 'en-US-JennyNeural',
                'emotion': 'cheerful'
            }
        }
        
        # Mock the video generation service
        with patch('services.ai_service.AIService') as mock_ai_service:
            mock_ai_service.return_value.generate_video.return_value = {
                'success': True,
                'output_file_path': 'videos/test_video.mp4',
                'output_file_url': 'https://example.com/test_video.mp4',
                'duration': 20,
                'cost': 3.0,
                'quality_metrics': {
                    'lip_sync_accuracy': 89.5,
                    'video_resolution': '1920x1080',
                    'audio_quality': 'high'
                }
            }
            
            video_response = client.post('/api/video/generate', json=video_request, headers=headers)
        
        assert video_response.status_code == 201
        video_data = video_response.json
        assert video_data['success'] is True
        video_id = video_data['video_id']
        
        # Step 5: Check Video Generation Status
        status_response = client.get(f'/api/video/{video_id}/status', headers=headers)
        assert status_response.status_code == 200
        status_data = status_response.json
        
        # Initially should be processing
        assert status_data['status'] in ['queued', 'processing']
        
        # Step 6: Simulate processing completion and check final status
        # In a real scenario, this would be polled until completion
        with patch('models.video.VideoGeneration.query') as mock_query:
            mock_video = Mock()
            mock_video.id = video_id
            mock_video.status = VideoStatus.COMPLETED
            mock_video.output_file_url = 'https://example.com/test_video.mp4'
            mock_video.duration_seconds = 20
            mock_video.cost = 3.0
            mock_video.quality_metrics = {'lip_sync_accuracy': 89.5}
            mock_query.get.return_value = mock_video
            
            final_status = client.get(f'/api/video/{video_id}/status', headers=headers)
            assert final_status.status_code == 200
            final_data = final_status.json
            assert final_data['status'] == 'completed'
            assert 'output_url' in final_data
        
        # Step 7: Download Video
        with patch('services.file_service.FileService.get_file_content') as mock_get_content:
            mock_get_content.return_value = b'mock_video_data'
            
            download_response = client.get(f'/api/video/{video_id}/download', headers=headers)
            assert download_response.status_code == 200
            assert download_response.data == b'mock_video_data'
        
        # Step 8: Verify Credits Deduction
        user_info_response = client.get('/api/user/profile', headers=headers)
        assert user_info_response.status_code == 200
        updated_user = user_info_response.json
        assert updated_user['credits_remaining'] == 0  # Used the free credit

    def test_premium_user_workflow_with_upgrade(self, client, ai_mocks, test_image_file):
        """Test workflow for user who upgrades to premium during the process"""
        
        # Create user and login
        user_data = {
            'email': 'premium_e2e@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Premium',
            'last_name': 'User',
            'gdpr_consent': True
        }
        
        # Register and login
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'email': user_data['email'],
            'password': user_data['password']
        })
        auth_token = login_response.json['tokens']['access_token']
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Step 1: Check pricing options
        pricing_response = client.get('/api/payment/pricing')
        assert pricing_response.status_code == 200
        pricing_data = pricing_response.json
        
        # Should have all pricing tiers
        assert len(pricing_data['pricing_cards']) == 4
        pro_tier = next(card for card in pricing_data['pricing_cards'] if card['tier_id'] == 'pro')
        assert pro_tier['credits'] == 15
        assert pro_tier['price'] == 249
        
        # Step 2: Purchase Pro Tier Credits
        purchase_request = {
            'tier': 'pro',
            'payment_method': 'pm_mock_card_visa'
        }
        
        # Mock Stripe payment processing
        with patch('stripe.Customer.create') as mock_customer:
            mock_customer.return_value = {'id': 'cus_mock_123', 'email': user_data['email']}
            
            with patch('stripe.PaymentIntent.create') as mock_payment_intent:
                mock_payment_intent.return_value = {
                    'id': 'pi_mock_123',
                    'status': 'succeeded',
                    'amount': 24900,  # 249 rupees in paise
                    'currency': 'inr'
                }
                
                purchase_response = client.post('/api/payment/purchase', json=purchase_request, headers=headers)
        
        assert purchase_response.status_code == 200
        purchase_data = purchase_response.json
        assert purchase_data['success'] is True
        assert purchase_data['credits_added'] == 15
        
        # Step 3: Verify credits updated
        profile_response = client.get('/api/user/profile', headers=headers)
        updated_profile = profile_response.json
        assert updated_profile['credits_remaining'] == 16  # 1 free + 15 purchased
        assert updated_profile['subscription_tier'] == 'pro'
        
        # Step 4: Create multiple videos (testing batch creation)
        video_requests = [
            {
                'script_text': f'This is test video number {i}. Testing our premium video generation capabilities.',
                'ai_provider': 'veo3' if i % 2 == 0 else 'runway',
                'video_quality': 'premium',
                'aspect_ratio': 'landscape'
            }
            for i in range(1, 4)  # Create 3 videos
        ]
        
        # Upload image once for all videos
        with open(test_image_file, 'rb') as f:
            files = {'file': ('premium_portrait.jpg', f, 'image/jpeg')}
            upload_response = client.post('/api/upload', files=files, headers=headers)
        file_id = upload_response.json['file_id']
        
        video_ids = []
        for request in video_requests:
            request['source_file_id'] = file_id
            
            with patch('services.ai_service.AIService') as mock_ai_service:
                mock_ai_service.return_value.generate_video.return_value = {
                    'success': True,
                    'output_file_path': f'videos/premium_video_{len(video_ids)}.mp4',
                    'duration': 25,
                    'cost': 5.0,  # Premium quality costs more
                    'quality_metrics': {'lip_sync_accuracy': 95.0}
                }
                
                video_response = client.post('/api/video/generate', json=request, headers=headers)
                assert video_response.status_code == 201
                video_ids.append(video_response.json['video_id'])
        
        # Step 5: Check that credits were properly deducted
        final_profile = client.get('/api/user/profile', headers=headers)
        final_data = final_profile.json
        assert final_data['credits_remaining'] == 13  # 16 - 3 videos = 13
        
        # Step 6: Get user's video history
        history_response = client.get('/api/user/videos', headers=headers)
        assert history_response.status_code == 200
        history_data = history_response.json
        assert len(history_data['videos']) >= 3  # At least the 3 we just created

    def test_error_handling_during_video_generation(self, client, ai_mocks, test_image_file):
        """Test error handling and recovery during video generation"""
        
        # Create user and login
        user_data = {
            'email': 'error_test@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Error',
            'last_name': 'Test',
            'gdpr_consent': True
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'email': user_data['email'],
            'password': user_data['password']
        })
        headers = {'Authorization': f'Bearer {login_response.json["tokens"]["access_token"]}'}
        
        # Upload image
        with open(test_image_file, 'rb') as f:
            files = {'file': ('error_test.jpg', f, 'image/jpeg')}
            upload_response = client.post('/api/upload', files=files, headers=headers)
        file_id = upload_response.json['file_id']
        
        # Test 1: AI Service Failure
        video_request = {
            'source_file_id': file_id,
            'script_text': 'This video should fail due to AI service error.',
            'ai_provider': 'veo3',
            'video_quality': 'standard',
            'aspect_ratio': 'landscape'
        }
        
        with patch('services.ai_service.AIService') as mock_ai_service:
            # Simulate AI service failure
            mock_ai_service.return_value.generate_video.return_value = {
                'success': False,
                'error': 'AI service temporarily unavailable'
            }
            
            error_response = client.post('/api/video/generate', json=video_request, headers=headers)
            assert error_response.status_code == 500
            error_data = error_response.json
            assert error_data['success'] is False
            assert 'AI service temporarily unavailable' in error_data['error']
        
        # Test 2: Insufficient Credits
        # First, use up the free credit
        with patch('services.ai_service.AIService') as mock_ai_service:
            mock_ai_service.return_value.generate_video.return_value = {
                'success': True,
                'output_file_path': 'videos/success.mp4',
                'cost': 3.0
            }
            
            success_response = client.post('/api/video/generate', json=video_request, headers=headers)
            assert success_response.status_code == 201
        
        # Now try to create another video without credits
        insufficient_response = client.post('/api/video/generate', json=video_request, headers=headers)
        assert insufficient_response.status_code == 402  # Payment required
        insufficient_data = insufficient_response.json
        assert 'insufficient credits' in insufficient_data['error'].lower()
        
        # Test 3: Invalid File Format
        invalid_request = video_request.copy()
        invalid_request['source_file_id'] = 'non_existent_file'
        
        invalid_response = client.post('/api/video/generate', json=invalid_request, headers=headers)
        assert invalid_response.status_code == 400
        invalid_data = invalid_response.json
        assert invalid_data['success'] is False

    def test_concurrent_video_generation(self, client, ai_mocks, test_image_file):
        """Test handling of multiple concurrent video generations"""
        
        # Create premium user with sufficient credits
        user_data = {
            'email': 'concurrent_test@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Concurrent',
            'last_name': 'Test',
            'gdpr_consent': True
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'email': user_data['email'],
            'password': user_data['password']
        })
        headers = {'Authorization': f'Bearer {login_response.json["tokens"]["access_token"]}'}
        
        # Add credits via mock purchase
        with patch('models.user.User.add_credits') as mock_add_credits:
            mock_add_credits.return_value = True
            client.post('/api/user/add-credits', json={'credits': 10}, headers=headers)
        
        # Upload image
        with open(test_image_file, 'rb') as f:
            files = {'file': ('concurrent_test.jpg', f, 'image/jpeg')}
            upload_response = client.post('/api/upload', files=files, headers=headers)
        file_id = upload_response.json['file_id']
        
        # Create multiple concurrent video requests
        concurrent_requests = [
            {
                'source_file_id': file_id,
                'script_text': f'Concurrent video test number {i}. Testing system capacity.',
                'ai_provider': 'veo3',
                'video_quality': 'standard',
                'aspect_ratio': 'landscape'
            }
            for i in range(1, 4)
        ]
        
        # Mock AI service to simulate different processing times
        def mock_video_generation(video_id):
            # Simulate variable processing times
            processing_time = 0.1 if '1' in video_id else 0.05
            time.sleep(processing_time)
            return {
                'success': True,
                'output_file_path': f'videos/concurrent_{video_id}.mp4',
                'duration': 15,
                'cost': 2.5
            }
        
        with patch('services.ai_service.AIService') as mock_ai_service:
            mock_ai_service.return_value.generate_video.side_effect = lambda vid: mock_video_generation(vid)
            
            # Submit all requests
            video_responses = []
            for request in concurrent_requests:
                response = client.post('/api/video/generate', json=request, headers=headers)
                video_responses.append(response)
            
            # All requests should succeed
            for response in video_responses:
                assert response.status_code == 201
                assert response.json['success'] is True
        
        # Verify all videos are tracked
        history_response = client.get('/api/user/videos', headers=headers)
        videos = history_response.json['videos']
        assert len(videos) >= 3

    def test_file_upload_validation(self, client, temp_upload_dir):
        """Test file upload validation and error handling"""
        
        # Create user and login
        user_data = {
            'email': 'upload_test@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Upload',
            'last_name': 'Test',
            'gdpr_consent': True
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'email': user_data['email'],
            'password': user_data['password']
        })
        headers = {'Authorization': f'Bearer {login_response.json["tokens"]["access_token"]}'}
        
        # Test 1: Valid image upload
        img = Image.new('RGB', (1920, 1080), color='green')
        valid_image_path = os.path.join(temp_upload_dir, 'valid_image.jpg')
        img.save(valid_image_path, 'JPEG')
        
        with open(valid_image_path, 'rb') as f:
            files = {'file': ('valid_image.jpg', f, 'image/jpeg')}
            valid_response = client.post('/api/upload', files=files, headers=headers)
        
        assert valid_response.status_code == 200
        assert valid_response.json['success'] is True
        
        # Test 2: Invalid file format
        text_file_path = os.path.join(temp_upload_dir, 'invalid.txt')
        with open(text_file_path, 'w') as f:
            f.write('This is not an image')
        
        with open(text_file_path, 'rb') as f:
            files = {'file': ('invalid.txt', f, 'text/plain')}
            invalid_response = client.post('/api/upload', files=files, headers=headers)
        
        assert invalid_response.status_code == 400
        assert 'Invalid file format' in invalid_response.json['error']
        
        # Test 3: File too large
        # Create a mock large file
        large_file_path = os.path.join(temp_upload_dir, 'large_image.jpg')
        with open(large_file_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')  # JPEG header
            f.write(b'\x00' * (15 * 1024 * 1024))  # 15MB of zeros
        
        with patch('flask.request.content_length', 15 * 1024 * 1024):  # Mock content length
            with open(large_file_path, 'rb') as f:
                files = {'file': ('large_image.jpg', f, 'image/jpeg')}
                large_response = client.post('/api/upload', files=files, headers=headers)
        
        assert large_response.status_code == 413
        assert 'File too large' in large_response.json['error']
        
        # Test 4: No file provided
        no_file_response = client.post('/api/upload', headers=headers)
        assert no_file_response.status_code == 400
        assert 'No file provided' in no_file_response.json['error']

    @pytest.mark.slow
    def test_video_quality_comparison(self, client, ai_mocks, test_image_file):
        """Test different video quality settings and their impact"""
        
        # Create premium user
        user_data = {
            'email': 'quality_test@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Quality',
            'last_name': 'Test',
            'gdpr_consent': True
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'email': user_data['email'],
            'password': user_data['password']
        })
        headers = {'Authorization': f'Bearer {login_response.json["tokens"]["access_token"]}'}
        
        # Add sufficient credits
        with patch('models.user.User.add_credits') as mock_add_credits:
            mock_add_credits.return_value = True
            client.post('/api/user/add-credits', json={'credits': 20}, headers=headers)
        
        # Upload image
        with open(test_image_file, 'rb') as f:
            files = {'file': ('quality_test.jpg', f, 'image/jpeg')}
            upload_response = client.post('/api/upload', files=files, headers=headers)
        file_id = upload_response.json['file_id']
        
        # Test different quality levels
        quality_tests = [
            {'quality': 'standard', 'expected_cost_range': (2.0, 4.0)},
            {'quality': 'premium', 'expected_cost_range': (4.0, 8.0)},
        ]
        
        for test in quality_tests:
            video_request = {
                'source_file_id': file_id,
                'script_text': f'Testing {test["quality"]} quality video generation.',
                'ai_provider': 'veo3',
                'video_quality': test['quality'],
                'aspect_ratio': 'landscape'
            }
            
            # Mock appropriate costs for different qualities
            expected_cost = test['expected_cost_range'][1] if test['quality'] == 'premium' else test['expected_cost_range'][0]
            
            with patch('services.ai_service.AIService') as mock_ai_service:
                mock_ai_service.return_value.generate_video.return_value = {
                    'success': True,
                    'output_file_path': f'videos/{test["quality"]}_video.mp4',
                    'duration': 20,
                    'cost': expected_cost,
                    'quality_metrics': {
                        'lip_sync_accuracy': 95.0 if test['quality'] == 'premium' else 85.0,
                        'video_resolution': '1920x1080' if test['quality'] == 'premium' else '1280x720'
                    }
                }
                
                response = client.post('/api/video/generate', json=video_request, headers=headers)
                assert response.status_code == 201
                
                video_data = response.json
                assert test['expected_cost_range'][0] <= video_data['estimated_cost'] <= test['expected_cost_range'][1]