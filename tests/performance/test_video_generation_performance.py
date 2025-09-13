"""
TalkingPhoto AI MVP - Video Generation Performance Tests
Performance benchmarks and load testing for video generation pipeline
"""

import pytest
import time
import asyncio
import concurrent.futures
from unittest.mock import Mock, patch
import psutil
import memory_profiler
from datetime import datetime, timedelta

from services.video_generation_service import VideoGenerationPipeline, VideoGenerationRequest
from services.ai_service import AIService
from models.video import VideoQuality, AspectRatio, AIProvider
from tests.mocks.ai_providers import create_ai_service_mocks


@pytest.mark.performance
class TestVideoGenerationPerformance:
    """Performance tests for video generation pipeline"""
    
    @pytest.fixture
    def performance_pipeline(self):
        """Create video generation pipeline for performance testing"""
        with patch('services.video_generation_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_value'
            with patch('services.video_generation_service.Redis'):
                return VideoGenerationPipeline()
    
    @pytest.fixture
    def sample_requests(self, temp_upload_dir):
        """Create sample video generation requests"""
        # Create test image file
        import os
        from PIL import Image
        
        img = Image.new('RGB', (1920, 1080), color='blue')
        image_path = os.path.join(temp_upload_dir, 'perf_test.jpg')
        img.save(image_path, 'JPEG')
        
        # Create different types of requests
        requests = [
            VideoGenerationRequest(
                source_image=image_path,
                script_text="Short test video for performance testing.",
                quality=VideoQuality.STANDARD,
                aspect_ratio=AspectRatio.LANDSCAPE,
                duration=10.0
            ),
            VideoGenerationRequest(
                source_image=image_path,
                script_text="Medium length test video for performance testing. This script is longer to test how the system handles different content lengths.",
                quality=VideoQuality.PREMIUM,
                aspect_ratio=AspectRatio.PORTRAIT,
                duration=30.0
            ),
            VideoGenerationRequest(
                source_image=image_path,
                script_text="Long test video for performance testing. This script is much longer to test how the system handles extended content generation. We want to ensure that longer videos don't cause memory issues or timeout problems.",
                quality=VideoQuality.STANDARD,
                aspect_ratio=AspectRatio.SQUARE,
                duration=60.0
            )
        ]
        
        return requests

    @pytest.mark.benchmark
    def test_single_video_generation_speed(self, performance_pipeline, sample_requests, benchmark):
        """Benchmark single video generation speed"""
        
        async def generate_video():
            # Mock all external dependencies for speed
            with patch.multiple(performance_pipeline,
                _generate_audio=Mock(return_value={'success': True, 'duration': 10}),
                _analyze_facial_landmarks=Mock(return_value={'success': True}),
                _generate_lipsync_animation=Mock(return_value={'success': True, 'frames': []}),
                _select_optimal_provider=Mock(return_value=AIProvider.VEO3),
                _generate_with_provider=Mock(return_value={'success': True, 'video_data': b'test'}),
                _post_process_video=Mock(return_value={'success': True, 'video_data': b'final'})
            ):
                
                result = await performance_pipeline.generate_video_async(
                    sample_requests[0], 
                    'benchmark_video_001'
                )
                return result
        
        # Benchmark the video generation
        def run_generation():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(generate_video())
            finally:
                loop.close()
        
        result = benchmark(run_generation)
        
        # Verify successful generation
        assert result['success'] is True
        
        # Performance assertions
        stats = benchmark.stats
        assert stats.mean < 2.0  # Should complete in under 2 seconds (mocked)
        assert stats.stddev < 0.5  # Low variance

    @pytest.mark.slow
    def test_concurrent_video_generation_throughput(self, performance_pipeline, sample_requests):
        """Test system throughput with concurrent video generations"""
        
        async def mock_generate_video(request, video_id):
            # Simulate realistic processing time
            await asyncio.sleep(0.1)  # 100ms processing time
            return {
                'success': True,
                'video_id': video_id,
                'video_data': b'mock_video_data',
                'processing_time': 0.1
            }
        
        async def run_concurrent_test():
            # Test with different concurrency levels
            concurrency_levels = [1, 5, 10, 20]
            results = {}
            
            for concurrency in concurrency_levels:
                start_time = time.time()
                
                # Create tasks
                tasks = []
                for i in range(concurrency):
                    video_id = f'concurrent_{concurrency}_{i}'
                    request = sample_requests[i % len(sample_requests)]
                    
                    # Mock the generation method
                    with patch.object(performance_pipeline, 'generate_video_async', mock_generate_video):
                        task = performance_pipeline.generate_video_async(request, video_id)
                        tasks.append(task)
                
                # Execute all tasks concurrently
                completed_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Calculate metrics
                successful_generations = sum(1 for r in completed_results if not isinstance(r, Exception) and r.get('success'))
                throughput = successful_generations / total_time if total_time > 0 else 0
                
                results[concurrency] = {
                    'total_time': total_time,
                    'successful_generations': successful_generations,
                    'throughput': throughput,
                    'errors': sum(1 for r in completed_results if isinstance(r, Exception))
                }
            
            return results
        
        # Run the concurrent test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_concurrent_test())
        finally:
            loop.close()
        
        # Performance assertions
        assert results[1]['throughput'] > 5.0  # Should handle at least 5 videos/second for single
        assert results[5]['throughput'] > 15.0  # Should scale with concurrency
        assert results[10]['successful_generations'] == 10  # All should succeed
        
        # Verify scaling efficiency
        efficiency_5 = results[5]['throughput'] / results[1]['throughput']
        assert efficiency_5 > 2.0  # Should scale reasonably well
        
        # Ensure no errors at reasonable concurrency levels
        assert results[5]['errors'] == 0
        assert results[10]['errors'] == 0

    def test_memory_usage_during_video_generation(self, performance_pipeline, sample_requests):
        """Test memory usage patterns during video generation"""
        
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        @memory_profiler.profile
        async def memory_test_generation():
            memory_measurements = []
            
            # Generate multiple videos and track memory
            for i in range(5):
                start_memory = process.memory_info().rss / 1024 / 1024
                
                # Mock video generation with realistic data sizes
                with patch.multiple(performance_pipeline,
                    _generate_audio=Mock(return_value={
                        'success': True, 
                        'audio_data': b'0' * 1000000,  # 1MB audio data
                        'duration': 30
                    }),
                    _generate_lipsync_animation=Mock(return_value={
                        'success': True, 
                        'frames': [{'data': b'0' * 100000} for _ in range(900)]  # 90MB frame data
                    }),
                    _generate_with_provider=Mock(return_value={
                        'success': True, 
                        'video_data': b'0' * 5000000  # 5MB video data
                    }),
                    _post_process_video=Mock(return_value={
                        'success': True, 
                        'video_data': b'0' * 3500000  # 3.5MB optimized video
                    })
                ):
                    
                    result = await performance_pipeline.generate_video_async(
                        sample_requests[i % len(sample_requests)],
                        f'memory_test_{i}'
                    )
                    
                    end_memory = process.memory_info().rss / 1024 / 1024
                    memory_measurements.append({
                        'iteration': i,
                        'start_memory': start_memory,
                        'end_memory': end_memory,
                        'memory_increase': end_memory - start_memory,
                        'success': result['success']
                    })
                    
                    # Force garbage collection
                    import gc
                    gc.collect()
            
            return memory_measurements
        
        # Run memory test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            measurements = loop.run_until_complete(memory_test_generation())
        finally:
            loop.close()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        # Memory usage assertions
        max_memory_increase = max(m['memory_increase'] for m in measurements)
        total_memory_increase = final_memory - initial_memory
        
        # Should not have excessive memory growth
        assert max_memory_increase < 500  # Less than 500MB per video
        assert total_memory_increase < 200  # Total increase should be reasonable
        
        # All generations should succeed
        assert all(m['success'] for m in measurements)

    def test_ai_provider_response_times(self, performance_pipeline):
        """Test and benchmark AI provider response times"""
        
        # Mock different AI providers with realistic response times
        provider_mocks = {
            AIProvider.VEO3: {
                'response_time': 0.5,  # 500ms
                'success_rate': 0.95,
                'cost': 0.15
            },
            AIProvider.RUNWAY: {
                'response_time': 0.8,  # 800ms
                'success_rate': 0.98,
                'cost': 0.20
            },
            AIProvider.NANO_BANANA: {
                'response_time': 0.2,  # 200ms
                'success_rate': 0.92,
                'cost': 0.08
            }
        }
        
        async def test_provider_performance(provider, config):
            start_time = time.time()
            
            # Simulate provider call
            await asyncio.sleep(config['response_time'])
            
            # Simulate occasional failures
            import random
            success = random.random() < config['success_rate']
            
            end_time = time.time()
            
            return {
                'provider': provider,
                'response_time': end_time - start_time,
                'success': success,
                'cost': config['cost']
            }
        
        async def run_provider_benchmarks():
            results = {}
            
            for provider, config in provider_mocks.items():
                # Test each provider multiple times
                provider_results = []
                
                for i in range(10):
                    result = await test_provider_performance(provider, config)
                    provider_results.append(result)
                
                # Calculate statistics
                response_times = [r['response_time'] for r in provider_results]
                success_count = sum(1 for r in provider_results if r['success'])
                
                results[provider] = {
                    'avg_response_time': sum(response_times) / len(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'success_rate': success_count / len(provider_results),
                    'cost': config['cost']
                }
            
            return results
        
        # Run provider benchmarks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_provider_benchmarks())
        finally:
            loop.close()
        
        # Performance assertions
        assert results[AIProvider.NANO_BANANA]['avg_response_time'] < 0.3  # Fastest provider
        assert results[AIProvider.VEO3]['avg_response_time'] < 0.7  # Mid-range
        assert results[AIProvider.RUNWAY]['avg_response_time'] < 1.0  # Slower but high quality
        
        # All providers should have reasonable success rates
        for provider, stats in results.items():
            assert stats['success_rate'] > 0.85  # At least 85% success rate

    @pytest.mark.slow
    def test_load_testing_video_generation(self, performance_pipeline, sample_requests):
        """Load test the video generation system"""
        
        async def load_test_scenario():
            # Simulate realistic load patterns
            load_scenarios = [
                {'concurrent_users': 5, 'videos_per_user': 2, 'duration': 30},
                {'concurrent_users': 10, 'videos_per_user': 1, 'duration': 60},
                {'concurrent_users': 20, 'videos_per_user': 1, 'duration': 45}
            ]
            
            results = {}
            
            for scenario in load_scenarios:
                scenario_start = time.time()
                all_tasks = []
                
                # Create users and their video generation tasks
                for user_id in range(scenario['concurrent_users']):
                    user_tasks = []
                    
                    for video_num in range(scenario['videos_per_user']):
                        video_id = f"load_test_u{user_id}_v{video_num}"
                        request = sample_requests[video_num % len(sample_requests)]
                        
                        # Mock video generation with variable processing time
                        async def mock_generate(vid_id):
                            # Simulate realistic processing time with some variance
                            import random
                            processing_time = random.uniform(0.1, 0.3)
                            await asyncio.sleep(processing_time)
                            
                            return {
                                'success': True,
                                'video_id': vid_id,
                                'processing_time': processing_time
                            }
                        
                        task = mock_generate(video_id)
                        user_tasks.append(task)
                    
                    all_tasks.extend(user_tasks)
                
                # Execute all tasks concurrently
                start_execution = time.time()
                task_results = await asyncio.gather(*all_tasks, return_exceptions=True)
                end_execution = time.time()
                
                # Calculate metrics
                successful_videos = sum(1 for r in task_results if not isinstance(r, Exception) and r.get('success'))
                failed_videos = len(task_results) - successful_videos
                total_videos = len(task_results)
                execution_time = end_execution - start_execution
                
                results[f"{scenario['concurrent_users']}_users"] = {
                    'scenario': scenario,
                    'total_videos': total_videos,
                    'successful_videos': successful_videos,
                    'failed_videos': failed_videos,
                    'success_rate': successful_videos / total_videos if total_videos > 0 else 0,
                    'execution_time': execution_time,
                    'videos_per_second': successful_videos / execution_time if execution_time > 0 else 0
                }
            
            return results
        
        # Run load test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(load_test_scenario())
        finally:
            loop.close()
        
        # Load test assertions
        for scenario_name, metrics in results.items():
            # High success rate under load
            assert metrics['success_rate'] > 0.95, f"Low success rate for {scenario_name}: {metrics['success_rate']}"
            
            # Reasonable throughput
            assert metrics['videos_per_second'] > 5.0, f"Low throughput for {scenario_name}: {metrics['videos_per_second']}"
            
            # Execution time should be reasonable
            assert metrics['execution_time'] < 10.0, f"Long execution time for {scenario_name}: {metrics['execution_time']}"

    def test_database_performance_under_load(self, db_session):
        """Test database performance during high-load scenarios"""
        
        from models.user import User
        from models.video import VideoGeneration
        from models.file import UploadedFile
        import uuid
        
        start_time = time.time()
        
        # Create test data
        users = []
        videos = []
        files = []
        
        # Create users
        for i in range(100):
            user = User(
                id=str(uuid.uuid4()),
                email=f'perf_user_{i}@test.com',
                password='test_password',
                first_name=f'User{i}',
                last_name='Test',
                credits_remaining=10
            )
            users.append(user)
            db_session.add(user)
        
        db_session.commit()
        user_creation_time = time.time() - start_time
        
        # Create files and videos
        file_start = time.time()
        for i, user in enumerate(users[:50]):  # Create files for first 50 users
            file = UploadedFile(
                id=str(uuid.uuid4()),
                user_id=user.id,
                original_filename=f'test_file_{i}.jpg',
                filename=f'test_file_{i}_unique.jpg',
                file_type='image',
                mime_type='image/jpeg',
                file_size=1024000,
                file_hash=f'hash_{i}'
            )
            files.append(file)
            db_session.add(file)
            
            # Create multiple videos per user
            for j in range(3):
                video = VideoGeneration(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    source_file_id=file.id,
                    script_text=f'Test video {j} for user {i}',
                    ai_provider=AIProvider.VEO3,
                    video_quality='standard',
                    aspect_ratio='landscape',
                    duration_seconds=30
                )
                videos.append(video)
                db_session.add(video)
        
        db_session.commit()
        creation_time = time.time() - file_start
        
        # Test query performance
        query_start = time.time()
        
        # Complex queries that might be used in the application
        user_count = db_session.query(User).count()
        video_count = db_session.query(VideoGeneration).count()
        
        # Join query
        user_videos = db_session.query(User, VideoGeneration).join(VideoGeneration).limit(50).all()
        
        # Aggregation query
        from sqlalchemy import func
        user_video_counts = db_session.query(
            User.id, 
            func.count(VideoGeneration.id).label('video_count')
        ).join(VideoGeneration).group_by(User.id).all()
        
        query_time = time.time() - query_start
        
        # Performance assertions
        assert user_creation_time < 2.0, f"User creation took too long: {user_creation_time}s"
        assert creation_time < 5.0, f"File/video creation took too long: {creation_time}s"
        assert query_time < 1.0, f"Queries took too long: {query_time}s"
        
        # Data integrity checks
        assert user_count == 100
        assert video_count == 150  # 50 users * 3 videos each
        assert len(user_videos) == 50
        assert len(user_video_counts) == 50

    def test_api_response_time_benchmarks(self, client, test_user, auth_headers):
        """Benchmark API endpoint response times"""
        
        response_times = {}
        
        # Test various endpoints
        endpoints = [
            ('GET', '/api/user/profile', None),
            ('GET', '/api/payment/pricing', None),
            ('GET', '/api/user/videos', None),
        ]
        
        for method, endpoint, data in endpoints:
            times = []
            
            # Test each endpoint multiple times
            for _ in range(10):
                start = time.time()
                
                if method == 'GET':
                    response = client.get(endpoint, headers=auth_headers)
                elif method == 'POST':
                    response = client.post(endpoint, json=data, headers=auth_headers)
                
                end = time.time()
                times.append(end - start)
                
                # Ensure the endpoint works
                assert response.status_code in [200, 201]
            
            response_times[endpoint] = {
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        # Performance assertions for API response times
        for endpoint, metrics in response_times.items():
            assert metrics['avg_time'] < 0.2, f"Slow average response for {endpoint}: {metrics['avg_time']}s"
            assert metrics['max_time'] < 0.5, f"Slow max response for {endpoint}: {metrics['max_time']}s"