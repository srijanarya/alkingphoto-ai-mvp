"""
TalkingPhoto AI MVP - Performance and Latency Benchmarks
Comprehensive performance tests for AI/ML components
"""

import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta

from tests.mocks.ai_providers import create_ai_service_mocks


class TestLatencyBenchmarks:
    """Test latency and response times for AI providers"""
    
    def test_provider_response_times(self):
        """Benchmark response times for each provider"""
        mocks = create_ai_service_mocks()
        
        benchmarks = {}
        iterations = 100
        
        # Benchmark Nano Banana
        nano_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            mocks['nano_banana'].generate_content({'contents': [{'parts': [{'text': 'test'}]}]})
            nano_times.append(time.perf_counter() - start)
        
        benchmarks['nano_banana'] = {
            'mean': statistics.mean(nano_times),
            'median': statistics.median(nano_times),
            'stdev': statistics.stdev(nano_times) if len(nano_times) > 1 else 0,
            'p95': np.percentile(nano_times, 95),
            'p99': np.percentile(nano_times, 99)
        }
        
        # Benchmark Veo3
        veo3_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            mocks['veo3'].submit_generation_job({'test': 'data'})
            veo3_times.append(time.perf_counter() - start)
        
        benchmarks['veo3'] = {
            'mean': statistics.mean(veo3_times),
            'median': statistics.median(veo3_times),
            'stdev': statistics.stdev(veo3_times) if len(veo3_times) > 1 else 0,
            'p95': np.percentile(veo3_times, 95),
            'p99': np.percentile(veo3_times, 99)
        }
        
        # All response times should be under 100ms for mocks
        for provider, metrics in benchmarks.items():
            assert metrics['mean'] < 0.1, f"{provider} mean response time too high"
            assert metrics['p99'] < 0.2, f"{provider} p99 response time too high"
    
    def test_concurrent_request_handling(self):
        """Test handling concurrent requests"""
        mocks = create_ai_service_mocks()
        veo3 = mocks['veo3']
        
        concurrent_requests = 50
        
        def submit_job(index):
            start = time.perf_counter()
            response = veo3.submit_generation_job({'request_id': index})
            elapsed = time.perf_counter() - start
            return {
                'index': index,
                'success': response['status_code'] == 200,
                'time': elapsed
            }
        
        # Submit requests concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_job, i) for i in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        success_count = sum(1 for r in results if r['success'])
        response_times = [r['time'] for r in results]
        
        assert success_count == concurrent_requests  # All should succeed
        assert max(response_times) < 1.0  # No request should take more than 1 second
        
        # Check for performance degradation under load
        first_10_avg = statistics.mean(response_times[:10])
        last_10_avg = statistics.mean(response_times[-10:])
        degradation = (last_10_avg - first_10_avg) / first_10_avg if first_10_avg > 0 else 0
        
        assert degradation < 0.5  # Less than 50% degradation
    
    def test_async_performance(self):
        """Test async performance for parallel operations"""
        
        async def process_request(provider_name, request_data):
            """Simulate async processing"""
            start = time.perf_counter()
            await asyncio.sleep(0.01)  # Simulate network delay
            elapsed = time.perf_counter() - start
            return {
                'provider': provider_name,
                'time': elapsed,
                'success': True
            }
        
        async def run_parallel_requests():
            """Run multiple providers in parallel"""
            tasks = [
                process_request('veo3', {'image': 'test1'}),
                process_request('runway', {'image': 'test2'}),
                process_request('d-id', {'image': 'test3'}),
                process_request('synthesia', {'image': 'test4'}),
                process_request('heygen', {'image': 'test5'})
            ]
            
            start = time.perf_counter()
            results = await asyncio.gather(*tasks)
            total_time = time.perf_counter() - start
            
            return results, total_time
        
        # Run async test
        results, total_time = asyncio.run(run_parallel_requests())
        
        # All 5 requests should complete in roughly the time of one request
        assert total_time < 0.05  # Should be close to single request time
        assert len(results) == 5
        assert all(r['success'] for r in results)
    
    def test_caching_performance(self):
        """Test performance improvements with caching"""
        
        class CachedProvider:
            def __init__(self):
                self.cache = {}
                self.call_count = 0
                self.cache_hits = 0
            
            def generate(self, key, compute_fn):
                self.call_count += 1
                if key in self.cache:
                    self.cache_hits += 1
                    return self.cache[key]
                
                # Simulate expensive computation
                time.sleep(0.01)
                result = compute_fn()
                self.cache[key] = result
                return result
        
        provider = CachedProvider()
        
        # First call - should be slow
        start = time.perf_counter()
        result1 = provider.generate('key1', lambda: 'result1')
        first_call_time = time.perf_counter() - start
        
        # Second call with same key - should be fast (cached)
        start = time.perf_counter()
        result2 = provider.generate('key1', lambda: 'result1')
        cached_call_time = time.perf_counter() - start
        
        assert result1 == result2
        assert cached_call_time < first_call_time / 10  # At least 10x faster
        assert provider.cache_hits == 1
        
        # Calculate cache hit rate
        hit_rate = provider.cache_hits / provider.call_count
        assert hit_rate == 0.5  # 1 hit out of 2 calls


class TestScalabilityBenchmarks:
    """Test system scalability"""
    
    def test_linear_scaling(self):
        """Test if system scales linearly with load"""
        
        def process_batch(size):
            """Process a batch of requests"""
            start = time.perf_counter()
            results = []
            for i in range(size):
                # Simulate processing
                time.sleep(0.001)
                results.append(i * 2)
            return time.perf_counter() - start
        
        # Test different batch sizes
        sizes = [10, 20, 40, 80]
        times = []
        
        for size in sizes:
            elapsed = process_batch(size)
            times.append(elapsed)
        
        # Check for linear scaling
        for i in range(1, len(sizes)):
            expected_ratio = sizes[i] / sizes[0]
            actual_ratio = times[i] / times[0]
            deviation = abs(actual_ratio - expected_ratio) / expected_ratio
            
            # Allow 20% deviation from perfect linear scaling
            assert deviation < 0.2, f"Non-linear scaling detected at size {sizes[i]}"
    
    def test_memory_efficiency(self):
        """Test memory efficiency under load"""
        import sys
        
        # Create large number of mock objects
        mocks = []
        initial_size = sys.getsizeof(mocks)
        
        for i in range(1000):
            mock = {
                'id': f'mock_{i}',
                'data': b'x' * 1000,  # 1KB per mock
                'metadata': {'created': time.time()}
            }
            mocks.append(mock)
        
        final_size = sys.getsizeof(mocks) + sum(sys.getsizeof(m) for m in mocks)
        
        # Check memory usage is reasonable
        expected_size = 1000 * 1000  # Roughly 1MB for 1000 x 1KB objects
        assert final_size < expected_size * 2  # Allow 2x overhead
        
        # Test cleanup
        mocks.clear()
        assert len(mocks) == 0
    
    def test_queue_throughput(self):
        """Test request queue throughput"""
        from collections import deque
        import threading
        
        class ThroughputTest:
            def __init__(self):
                self.queue = deque()
                self.processed = 0
                self.lock = threading.Lock()
                self.running = True
            
            def producer(self, count):
                """Add items to queue"""
                for i in range(count):
                    self.queue.append(f'item_{i}')
                    time.sleep(0.0001)  # Simulate production rate
            
            def consumer(self):
                """Process items from queue"""
                while self.running or self.queue:
                    if self.queue:
                        with self.lock:
                            if self.queue:
                                item = self.queue.popleft()
                                self.processed += 1
                                time.sleep(0.0005)  # Simulate processing
                    else:
                        time.sleep(0.001)
        
        test = ThroughputTest()
        
        # Start producer and consumer threads
        producer_thread = threading.Thread(target=test.producer, args=(100,))
        consumer_thread = threading.Thread(target=test.consumer)
        
        start = time.perf_counter()
        producer_thread.start()
        consumer_thread.start()
        
        producer_thread.join()
        test.running = False
        consumer_thread.join()
        
        elapsed = time.perf_counter() - start
        
        # Calculate throughput
        throughput = test.processed / elapsed if elapsed > 0 else 0
        
        assert test.processed == 100  # All items processed
        assert throughput > 50  # At least 50 items per second


class TestOptimizationBenchmarks:
    """Test optimization algorithm performance"""
    
    def test_provider_selection_speed(self):
        """Test speed of provider selection algorithm"""
        providers = [
            {'name': 'veo3', 'cost': 0.15, 'quality': 8.5, 'speed': 2.1},
            {'name': 'runway', 'cost': 0.20, 'quality': 8.8, 'speed': 3.4},
            {'name': 'd-id', 'cost': 0.10, 'quality': 7.5, 'speed': 1.8},
            {'name': 'synthesia', 'cost': 0.25, 'quality': 9.0, 'speed': 4.0},
            {'name': 'heygen', 'cost': 0.18, 'quality': 8.2, 'speed': 2.5}
        ]
        
        def select_optimal(providers, criteria):
            """Select optimal provider based on criteria"""
            if criteria == 'cost':
                return min(providers, key=lambda x: x['cost'])
            elif criteria == 'quality':
                return max(providers, key=lambda x: x['quality'])
            elif criteria == 'speed':
                return min(providers, key=lambda x: x['speed'])
            else:  # balanced
                scores = []
                for p in providers:
                    score = (1/p['cost']) * 0.4 + p['quality'] * 0.4 + (1/p['speed']) * 0.2
                    scores.append((p, score))
                return max(scores, key=lambda x: x[1])[0]
        
        # Benchmark selection speed
        iterations = 10000
        start = time.perf_counter()
        
        for _ in range(iterations):
            select_optimal(providers, 'cost')
            select_optimal(providers, 'quality')
            select_optimal(providers, 'balanced')
        
        elapsed = time.perf_counter() - start
        operations_per_second = (iterations * 3) / elapsed
        
        # Should handle at least 100k selections per second
        assert operations_per_second > 100000
    
    def test_cost_calculation_performance(self):
        """Test performance of cost calculation"""
        
        def calculate_cost(duration, quality, provider, bulk_count=1):
            """Calculate video generation cost"""
            base_rates = {
                'veo3': 0.15,
                'runway': 0.20,
                'd-id': 0.10
            }
            
            quality_multipliers = {
                'economy': 0.7,
                'standard': 1.0,
                'premium': 1.5
            }
            
            bulk_discounts = [
                (50, 0.25),
                (20, 0.20),
                (10, 0.15),
                (5, 0.10),
                (1, 0)
            ]
            
            base_cost = base_rates.get(provider, 0.15) * duration
            quality_cost = base_cost * quality_multipliers.get(quality, 1.0)
            
            # Apply bulk discount
            discount = 0
            for min_qty, disc in bulk_discounts:
                if bulk_count >= min_qty:
                    discount = disc
                    break
            
            final_cost = quality_cost * (1 - discount) * bulk_count
            return final_cost
        
        # Benchmark calculations
        iterations = 100000
        start = time.perf_counter()
        
        for _ in range(iterations):
            calculate_cost(30, 'standard', 'veo3', 1)
            calculate_cost(60, 'premium', 'runway', 10)
            calculate_cost(15, 'economy', 'd-id', 50)
        
        elapsed = time.perf_counter() - start
        calculations_per_second = (iterations * 3) / elapsed
        
        # Should handle at least 500k calculations per second
        assert calculations_per_second > 500000


class TestRateLimitCompliance:
    """Test rate limiting compliance"""
    
    def test_rate_limiter(self):
        """Test rate limiter implementation"""
        
        class RateLimiter:
            def __init__(self, max_requests, time_window):
                self.max_requests = max_requests
                self.time_window = time_window  # seconds
                self.requests = []
            
            def is_allowed(self):
                now = time.time()
                # Remove old requests outside window
                self.requests = [r for r in self.requests if now - r < self.time_window]
                
                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return True
                return False
        
        # Test rate limiter (10 requests per second)
        limiter = RateLimiter(10, 1.0)
        
        # Should allow first 10 requests
        for _ in range(10):
            assert limiter.is_allowed()
        
        # 11th request should be blocked
        assert not limiter.is_allowed()
        
        # Wait for window to pass
        time.sleep(1.1)
        
        # Should allow again
        assert limiter.is_allowed()
    
    def test_provider_rate_limits(self):
        """Test compliance with provider-specific rate limits"""
        
        provider_limits = {
            'veo3': {'requests_per_second': 10, 'requests_per_minute': 300},
            'runway': {'requests_per_second': 5, 'requests_per_minute': 200},
            'elevenlabs': {'requests_per_second': 20, 'requests_per_minute': 500}
        }
        
        def test_rate_compliance(provider, requests_count, duration):
            """Test if request rate complies with limits"""
            limits = provider_limits[provider]
            
            # Calculate actual rates
            requests_per_second = requests_count / duration
            requests_per_minute = requests_per_second * 60
            
            # Check compliance
            compliant = (
                requests_per_second <= limits['requests_per_second'] and
                requests_per_minute <= limits['requests_per_minute']
            )
            
            return compliant, requests_per_second
        
        # Test different scenarios
        assert test_rate_compliance('veo3', 9, 1)[0]  # Within limits
        assert not test_rate_compliance('veo3', 15, 1)[0]  # Exceeds per-second limit
        assert test_rate_compliance('runway', 4, 1)[0]  # Within limits
        assert not test_rate_compliance('runway', 250, 60)[0]  # Exceeds per-minute limit
    
    def test_backoff_strategy(self):
        """Test exponential backoff implementation"""
        
        def exponential_backoff(attempt, base_delay=1, max_delay=60):
            """Calculate backoff delay"""
            delay = min(base_delay * (2 ** attempt), max_delay)
            # Add jitter to prevent thundering herd
            jitter = np.random.uniform(0, delay * 0.1)
            return delay + jitter
        
        # Test backoff progression
        delays = []
        for attempt in range(6):
            delay = exponential_backoff(attempt)
            delays.append(delay)
        
        # Verify exponential growth
        assert delays[0] < delays[1] < delays[2]
        assert delays[-1] <= 60  # Max delay cap
        
        # Test with different base delays
        fast_backoff = exponential_backoff(3, base_delay=0.1)
        slow_backoff = exponential_backoff(3, base_delay=2)
        
        assert fast_backoff < slow_backoff


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])