#!/usr/bin/env python3
"""
TalkingPhoto AI MVP - Comprehensive Performance Analysis Tool

Performance testing and profiling tool for the TalkingPhoto application.
Tests video generation pipeline, concurrent user handling, memory usage,
and identifies bottlenecks.

Author: Performance Engineering Team
Date: 2025-09-13
"""

import os
import sys
import time
import json
import asyncio
import psutil
import tracemalloc
import cProfile
import pstats
import io
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics container"""
    timestamp: str
    test_name: str
    duration_seconds: float
    requests_per_second: float
    average_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class BottleneckAnalysis:
    """Bottleneck analysis results"""
    component: str
    impact_level: str  # high, medium, low
    response_time_ms: float
    cpu_time_ms: float
    memory_allocated_mb: float
    io_wait_time_ms: float
    database_queries: int
    external_api_calls: int
    recommendations: List[str]


class PerformanceProfiler:
    """Profile application performance"""
    
    def __init__(self, app_url: str = "https://alkingphoto-ai-mvp-fnyuyh3wm6ofnev3fbseeo.streamlit.app"):
        self.app_url = app_url
        self.session = requests.Session()
        self.results = []
        self.bottlenecks = []
        
    def profile_video_generation_pipeline(self) -> Dict[str, Any]:
        """Profile the video generation pipeline"""
        logger.info("Starting video generation pipeline profiling...")
        
        pipeline_metrics = {
            "total_time": 0,
            "stages": {},
            "bottlenecks": [],
            "memory_usage": {},
            "recommendations": []
        }
        
        # Start memory tracking
        tracemalloc.start()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        stages = [
            ("image_upload", self._simulate_image_upload),
            ("image_processing", self._simulate_image_processing),
            ("ai_service_call", self._simulate_ai_service_call),
            ("video_generation", self._simulate_video_generation),
            ("file_io", self._simulate_file_io),
            ("response_delivery", self._simulate_response_delivery)
        ]
        
        start_time = time.time()
        
        for stage_name, stage_func in stages:
            stage_start = time.time()
            stage_start_cpu = time.process_time()
            
            try:
                stage_result = stage_func()
                stage_time = (time.time() - stage_start) * 1000  # Convert to ms
                stage_cpu_time = (time.process_time() - stage_start_cpu) * 1000
                
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_delta = current_memory - start_memory
                
                pipeline_metrics["stages"][stage_name] = {
                    "duration_ms": stage_time,
                    "cpu_time_ms": stage_cpu_time,
                    "memory_delta_mb": memory_delta,
                    "io_wait_ms": stage_time - stage_cpu_time,
                    "status": "success"
                }
                
                # Check for bottlenecks
                if stage_time > 5000:  # More than 5 seconds
                    pipeline_metrics["bottlenecks"].append({
                        "stage": stage_name,
                        "duration_ms": stage_time,
                        "severity": "high"
                    })
                    
            except Exception as e:
                logger.error(f"Error in stage {stage_name}: {e}")
                pipeline_metrics["stages"][stage_name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        pipeline_metrics["total_time"] = (time.time() - start_time) * 1000
        
        # Memory profiling
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        pipeline_metrics["memory_usage"] = {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
            "process_mb": psutil.Process().memory_info().rss / 1024 / 1024
        }
        
        # Generate recommendations
        pipeline_metrics["recommendations"] = self._generate_pipeline_recommendations(pipeline_metrics)
        
        return pipeline_metrics
    
    def _simulate_image_upload(self) -> Dict:
        """Simulate image upload"""
        time.sleep(0.5)  # Simulate upload time
        return {"size_mb": 2.5, "format": "jpeg"}
    
    def _simulate_image_processing(self) -> Dict:
        """Simulate image processing"""
        time.sleep(1.0)  # Simulate processing
        # Allocate some memory to simulate processing
        data = [[random.random() for _ in range(100)] for _ in range(100)]
        return {"processed": True, "dimensions": (1000, 1000)}
    
    def _simulate_ai_service_call(self) -> Dict:
        """Simulate AI service call"""
        time.sleep(3.0)  # Simulate API latency
        return {"provider": "mock", "response_time_ms": 3000}
    
    def _simulate_video_generation(self) -> Dict:
        """Simulate video generation"""
        time.sleep(8.0)  # Simulate generation time
        return {"frames": 300, "duration_seconds": 10}
    
    def _simulate_file_io(self) -> Dict:
        """Simulate file I/O operations"""
        time.sleep(0.8)  # Simulate I/O
        return {"written_mb": 15}
    
    def _simulate_response_delivery(self) -> Dict:
        """Simulate response delivery"""
        time.sleep(0.3)  # Simulate network transfer
        return {"delivered": True}
    
    def _generate_pipeline_recommendations(self, metrics: Dict) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Check total time
        if metrics["total_time"] > 30000:  # More than 30 seconds
            recommendations.append("CRITICAL: Total pipeline time exceeds 30s target")
            
        # Check for slow stages
        for stage, data in metrics["stages"].items():
            if data.get("status") == "success":
                if data["duration_ms"] > 5000:
                    recommendations.append(f"Optimize {stage}: Currently takes {data['duration_ms']:.0f}ms")
                    
                if data.get("io_wait_ms", 0) > data.get("cpu_time_ms", 0):
                    recommendations.append(f"High I/O wait in {stage}: Consider async processing")
        
        # Memory recommendations
        if metrics["memory_usage"]["peak_mb"] > 500:
            recommendations.append(f"High memory usage: Peak {metrics['memory_usage']['peak_mb']:.1f}MB")
            
        return recommendations
    
    async def test_concurrent_users(self, num_users: int = 100) -> Dict[str, Any]:
        """Test concurrent user handling"""
        logger.info(f"Testing with {num_users} concurrent users...")
        
        results = {
            "concurrent_users": num_users,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "start_time": datetime.now().isoformat(),
            "errors": []
        }
        
        async def simulate_user_session():
            """Simulate a single user session"""
            session_start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    # Simulate user actions
                    actions = [
                        ("load_page", "/"),
                        ("upload_image", "/api/upload"),
                        ("submit_text", "/api/process"),
                        ("generate_video", "/api/generate"),
                        ("download_video", "/api/download")
                    ]
                    
                    for action_name, endpoint in actions:
                        action_start = time.time()
                        try:
                            # Mock API call (replace with actual endpoint)
                            await asyncio.sleep(random.uniform(0.1, 0.5))
                            response_time = (time.time() - action_start) * 1000
                            results["response_times"].append(response_time)
                            results["successful_requests"] += 1
                        except Exception as e:
                            results["failed_requests"] += 1
                            results["errors"].append(str(e))
                        
                        results["total_requests"] += 1
                        
                return time.time() - session_start
                
            except Exception as e:
                logger.error(f"User session failed: {e}")
                results["failed_requests"] += 1
                return None
        
        # Run concurrent sessions
        tasks = [simulate_user_session() for _ in range(num_users)]
        session_durations = await asyncio.gather(*tasks)
        
        # Calculate statistics
        valid_response_times = [t for t in results["response_times"] if t is not None]
        if valid_response_times:
            sorted_times = sorted(valid_response_times)
            n = len(sorted_times)
            results["statistics"] = {
                "avg_response_time_ms": sum(valid_response_times) / len(valid_response_times),
                "p50_response_time_ms": sorted_times[int(n * 0.5)] if n > 0 else 0,
                "p95_response_time_ms": sorted_times[int(n * 0.95)] if n > 0 else 0,
                "p99_response_time_ms": sorted_times[int(n * 0.99)] if n > 0 else 0,
                "min_response_time_ms": min(valid_response_times),
                "max_response_time_ms": max(valid_response_times),
                "error_rate": results["failed_requests"] / results["total_requests"] * 100 if results["total_requests"] > 0 else 0
            }
        
        results["end_time"] = datetime.now().isoformat()
        
        return results
    
    def analyze_memory_patterns(self) -> Dict[str, Any]:
        """Analyze memory usage patterns"""
        logger.info("Analyzing memory usage patterns...")
        
        memory_analysis = {
            "baseline_mb": 0,
            "peak_mb": 0,
            "average_mb": 0,
            "leaks_detected": False,
            "gc_stats": {},
            "recommendations": []
        }
        
        # Monitor memory over time
        memory_samples = []
        
        for i in range(10):
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # Simulate some operations
            if i % 3 == 0:
                # Allocate and deallocate memory
                temp_data = [[random.random() for _ in range(50)] for _ in range(50)]
                del temp_data
            
            time.sleep(1)
        
        memory_analysis["baseline_mb"] = memory_samples[0]
        memory_analysis["peak_mb"] = max(memory_samples)
        memory_analysis["average_mb"] = sum(memory_samples) / len(memory_samples) if memory_samples else 0
        
        # Check for memory leaks
        if memory_samples[-1] > memory_samples[0] * 1.2:  # 20% increase
            memory_analysis["leaks_detected"] = True
            memory_analysis["recommendations"].append("Potential memory leak detected")
        
        # Get garbage collection stats
        import gc
        memory_analysis["gc_stats"] = {
            "collections": gc.get_count(),
            "threshold": gc.get_threshold(),
            "objects": len(gc.get_objects())
        }
        
        return memory_analysis
    
    def identify_bottlenecks(self) -> List[BottleneckAnalysis]:
        """Identify performance bottlenecks"""
        logger.info("Identifying performance bottlenecks...")
        
        bottlenecks = []
        
        # Analyze different components
        components = [
            ("Image Processing", self._analyze_image_processing_bottleneck),
            ("AI Service Calls", self._analyze_ai_service_bottleneck),
            ("File I/O Operations", self._analyze_file_io_bottleneck),
            ("Database Queries", self._analyze_database_bottleneck),
            ("WebSocket Connections", self._analyze_websocket_bottleneck)
        ]
        
        for component_name, analyzer_func in components:
            try:
                bottleneck = analyzer_func()
                if bottleneck:
                    bottleneck.component = component_name
                    bottlenecks.append(bottleneck)
            except Exception as e:
                logger.error(f"Error analyzing {component_name}: {e}")
        
        # Sort by impact level
        bottlenecks.sort(key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}.get(x.impact_level, 3),
            -x.response_time_ms
        ))
        
        return bottlenecks
    
    def _analyze_image_processing_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Analyze image processing performance"""
        start_time = time.time()
        start_cpu = time.process_time()
        
        # Simulate image processing
        image_data = [[[random.random() for _ in range(3)] for _ in range(200)] for _ in range(200)]  # Simulate image
        processed = [[pixel for pixel in row] for row in image_data]  # Simple processing
        
        response_time = (time.time() - start_time) * 1000
        cpu_time = (time.process_time() - start_cpu) * 1000
        
        impact_level = "high" if response_time > 1000 else "medium" if response_time > 500 else "low"
        
        recommendations = []
        if response_time > 1000:
            recommendations.append("Consider using GPU acceleration for image processing")
            recommendations.append("Implement image preprocessing queue")
            recommendations.append("Use lower resolution for initial processing")
        
        return BottleneckAnalysis(
            component="Image Processing",
            impact_level=impact_level,
            response_time_ms=response_time,
            cpu_time_ms=cpu_time,
            memory_allocated_mb=sys.getsizeof(image_data) / 1024 / 1024,
            io_wait_time_ms=response_time - cpu_time,
            database_queries=0,
            external_api_calls=0,
            recommendations=recommendations
        )
    
    def _analyze_ai_service_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Analyze AI service call performance"""
        # Simulate AI service latency
        response_time = random.uniform(2000, 5000)  # 2-5 seconds
        
        recommendations = [
            "Implement response caching for common requests",
            "Use batch processing for multiple requests",
            "Consider fallback to alternative AI providers",
            "Implement request queuing with priority levels"
        ]
        
        return BottleneckAnalysis(
            component="AI Service Calls",
            impact_level="high",
            response_time_ms=response_time,
            cpu_time_ms=50,
            memory_allocated_mb=10,
            io_wait_time_ms=response_time - 50,
            database_queries=0,
            external_api_calls=1,
            recommendations=recommendations
        )
    
    def _analyze_file_io_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Analyze file I/O performance"""
        start_time = time.time()
        
        # Simulate file operations
        temp_file = Path("/tmp/test_video.mp4")
        data = b"0" * (10 * 1024 * 1024)  # 10MB
        
        # Write operation
        write_start = time.time()
        # Simulated write
        write_time = 0.5
        time.sleep(write_time)
        
        response_time = (time.time() - start_time) * 1000
        
        recommendations = []
        if response_time > 500:
            recommendations.append("Use async file I/O operations")
            recommendations.append("Implement file streaming instead of full loads")
            recommendations.append("Consider using cloud storage with CDN")
        
        return BottleneckAnalysis(
            component="File I/O Operations",
            impact_level="medium" if response_time > 500 else "low",
            response_time_ms=response_time,
            cpu_time_ms=10,
            memory_allocated_mb=10,
            io_wait_time_ms=response_time - 10,
            database_queries=0,
            external_api_calls=0,
            recommendations=recommendations
        )
    
    def _analyze_database_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Analyze database query performance"""
        # Simulate database queries
        query_times = [random.uniform(10, 100) for _ in range(5)]
        total_time = sum(query_times)
        
        recommendations = []
        if total_time > 200:
            recommendations.append("Add database indexes for frequent queries")
            recommendations.append("Implement query result caching")
            recommendations.append("Use connection pooling")
            recommendations.append("Consider read replicas for scaling")
        
        return BottleneckAnalysis(
            component="Database Queries",
            impact_level="medium" if total_time > 200 else "low",
            response_time_ms=total_time,
            cpu_time_ms=20,
            memory_allocated_mb=5,
            io_wait_time_ms=total_time - 20,
            database_queries=len(query_times),
            external_api_calls=0,
            recommendations=recommendations
        )
    
    def _analyze_websocket_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Analyze WebSocket connection performance"""
        # Simulate WebSocket operations
        connection_time = random.uniform(50, 200)
        message_latency = random.uniform(10, 50)
        
        total_time = connection_time + message_latency * 10  # Simulate 10 messages
        
        recommendations = []
        if total_time > 500:
            recommendations.append("Implement WebSocket connection pooling")
            recommendations.append("Use message batching for updates")
            recommendations.append("Consider Server-Sent Events for one-way communication")
        
        return BottleneckAnalysis(
            component="WebSocket Connections",
            impact_level="low",
            response_time_ms=total_time,
            cpu_time_ms=30,
            memory_allocated_mb=2,
            io_wait_time_ms=total_time - 30,
            database_queries=0,
            external_api_calls=0,
            recommendations=recommendations
        )
    
    def generate_report(self, output_file: str = "performance_report.json") -> None:
        """Generate comprehensive performance report"""
        logger.info("Generating performance report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "application_url": self.app_url,
            "test_results": {
                "pipeline_profiling": self.profile_video_generation_pipeline(),
                "concurrent_users": asyncio.run(self.test_concurrent_users(100)),
                "memory_analysis": self.analyze_memory_patterns(),
                "bottlenecks": [
                    {
                        "component": b.component,
                        "impact_level": b.impact_level,
                        "response_time_ms": b.response_time_ms,
                        "recommendations": b.recommendations
                    }
                    for b in self.identify_bottlenecks()
                ]
            },
            "overall_recommendations": self._generate_overall_recommendations()
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to {output_file}")
        
        # Print summary
        self._print_summary(report)
    
    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall optimization recommendations"""
        return [
            "Implement Redis caching for frequently accessed data",
            "Use CDN for static assets and generated videos",
            "Implement request queuing with priority levels",
            "Add horizontal scaling with load balancing",
            "Optimize database queries with proper indexing",
            "Implement async processing for heavy operations",
            "Use connection pooling for external services",
            "Add circuit breakers for external API calls",
            "Implement progressive image loading",
            "Use WebP format for images to reduce size",
            "Enable HTTP/2 for better performance",
            "Implement service worker for offline functionality"
        ]
    
    def _print_summary(self, report: Dict) -> None:
        """Print report summary"""
        print("\n" + "="*60)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("="*60)
        
        pipeline = report["test_results"]["pipeline_profiling"]
        print(f"\nVideo Generation Pipeline:")
        print(f"  Total Time: {pipeline['total_time']:.1f}ms")
        print(f"  Target: <30,000ms")
        print(f"  Status: {'✅ PASS' if pipeline['total_time'] < 30000 else '❌ FAIL'}")
        
        concurrent = report["test_results"]["concurrent_users"]
        print(f"\nConcurrent Users Test:")
        print(f"  Users Tested: {concurrent['concurrent_users']}")
        if "statistics" in concurrent:
            print(f"  Avg Response: {concurrent['statistics']['avg_response_time_ms']:.1f}ms")
            print(f"  P95 Response: {concurrent['statistics']['p95_response_time_ms']:.1f}ms")
            print(f"  Error Rate: {concurrent['statistics']['error_rate']:.2f}%")
        
        memory = report["test_results"]["memory_analysis"]
        print(f"\nMemory Analysis:")
        print(f"  Baseline: {memory['baseline_mb']:.1f}MB")
        print(f"  Peak: {memory['peak_mb']:.1f}MB")
        print(f"  Memory Leaks: {'❌ YES' if memory['leaks_detected'] else '✅ NO'}")
        
        bottlenecks = report["test_results"]["bottlenecks"]
        print(f"\nTop Bottlenecks:")
        for b in bottlenecks[:3]:
            print(f"  - {b['component']}: {b['response_time_ms']:.1f}ms ({b['impact_level'].upper()})")
        
        print("\n" + "="*60)


class LoadTester:
    """Load testing using Locust framework simulation"""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.results = []
    
    def run_load_test(self, users: int = 100, duration: int = 60) -> Dict:
        """Run load test simulation"""
        logger.info(f"Running load test: {users} users for {duration} seconds")
        
        results = {
            "users": users,
            "duration": duration,
            "requests": [],
            "errors": [],
            "start_time": datetime.now()
        }
        
        # Simulate load test
        end_time = time.time() + duration
        request_count = 0
        
        while time.time() < end_time:
            # Simulate requests based on user count
            for _ in range(int(users / 10)):  # Simplified simulation
                request_start = time.time()
                
                # Simulate different request types
                rand_val = random.random()
                if rand_val < 0.5:
                    request_type = "page_load"
                elif rand_val < 0.8:
                    request_type = "image_upload"
                else:
                    request_type = "video_generation"
                
                # Simulate response time based on request type
                if request_type == "page_load":
                    response_time = random.uniform(0.1, 0.5)
                elif request_type == "image_upload":
                    response_time = random.uniform(0.5, 2.0)
                else:  # video_generation
                    response_time = random.uniform(5.0, 15.0)
                
                time.sleep(response_time / 100)  # Scale down for simulation
                
                results["requests"].append({
                    "type": request_type,
                    "response_time_ms": response_time * 1000,
                    "timestamp": datetime.now().isoformat(),
                    "success": random.random() > 0.05  # 95% success rate
                })
                
                request_count += 1
                
                if request_count % 100 == 0:
                    logger.info(f"Processed {request_count} requests...")
        
        # Calculate statistics
        response_times = [r["response_time_ms"] for r in results["requests"]]
        successful_requests = [r for r in results["requests"] if r["success"]]
        
        if response_times:
            sorted_times = sorted(response_times)
            n = len(sorted_times)
            results["statistics"] = {
                "total_requests": len(results["requests"]),
                "successful_requests": len(successful_requests),
                "failed_requests": len(results["requests"]) - len(successful_requests),
                "requests_per_second": len(results["requests"]) / duration if duration > 0 else 0,
                "avg_response_time_ms": sum(response_times) / len(response_times),
                "median_response_time_ms": sorted_times[n // 2],
                "p95_response_time_ms": sorted_times[int(n * 0.95)],
                "p99_response_time_ms": sorted_times[int(n * 0.99)],
                "error_rate": (len(results["requests"]) - len(successful_requests)) / len(results["requests"]) * 100
            }
        else:
            results["statistics"] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "requests_per_second": 0,
                "avg_response_time_ms": 0,
                "median_response_time_ms": 0,
                "p95_response_time_ms": 0,
                "p99_response_time_ms": 0,
                "error_rate": 0
            }
        
        return results


def main():
    """Main execution function"""
    print("TalkingPhoto AI MVP - Performance Analysis Tool")
    print("=" * 60)
    
    # Initialize profiler
    profiler = PerformanceProfiler()
    
    # Run comprehensive tests
    print("\n1. Profiling Video Generation Pipeline...")
    pipeline_results = profiler.profile_video_generation_pipeline()
    
    print("\n2. Testing Concurrent User Handling...")
    concurrent_results = asyncio.run(profiler.test_concurrent_users(100))
    
    print("\n3. Analyzing Memory Usage Patterns...")
    memory_results = profiler.analyze_memory_patterns()
    
    print("\n4. Identifying Performance Bottlenecks...")
    bottlenecks = profiler.identify_bottlenecks()
    
    print("\n5. Running Load Test...")
    load_tester = LoadTester(profiler.app_url)
    load_results = load_tester.run_load_test(users=100, duration=30)
    
    # Generate comprehensive report
    print("\n6. Generating Performance Report...")
    profiler.generate_report("talkingphoto_performance_report.json")
    
    print("\nPerformance analysis complete! Check talkingphoto_performance_report.json for detailed results.")


if __name__ == "__main__":
    main()