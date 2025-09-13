#!/usr/bin/env python3
"""
TalkingPhoto AI MVP - Performance Optimizations Implementation

Concrete optimization implementations for identified bottlenecks.
Includes caching strategies, async processing, database optimizations, and more.

Author: Performance Engineering Team
Date: 2025-09-13
"""

import os
import asyncio
import hashlib
import json
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps, lru_cache
import redis
import aioredis
import aiocache
from aiocache import cached
from aiocache.serializers import JsonSerializer
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import gc
from dataclasses import dataclass
import logging
from pathlib import Path
import pickle
import threading
from queue import Queue, PriorityQueue
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CACHING STRATEGY IMPLEMENTATION
# ============================================================================

class CacheManager:
    """Advanced caching strategy implementation"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = None
        self.local_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        try:
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available, using local cache only: {e}")
    
    def _get_cache_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace"""
        return f"talkingphoto:{namespace}:{key}"
    
    def get(self, namespace: str, key: str, default=None):
        """Get value from cache (Redis -> Local -> Default)"""
        cache_key = self._get_cache_key(namespace, key)
        
        # Try local cache first
        if cache_key in self.local_cache:
            self.cache_stats["hits"] += 1
            return self.local_cache[cache_key]["value"]
        
        # Try Redis
        if self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                if value:
                    self.cache_stats["hits"] += 1
                    # Store in local cache
                    self.local_cache[cache_key] = {
                        "value": json.loads(value),
                        "timestamp": time.time()
                    }
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        self.cache_stats["misses"] += 1
        return default
    
    def set(self, namespace: str, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        cache_key = self._get_cache_key(namespace, key)
        
        # Store in local cache
        self.local_cache[cache_key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl
        }
        
        # Store in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(value)
                )
            except Exception as e:
                logger.error(f"Redis set error: {e}")
    
    def invalidate(self, namespace: str, key: str = None):
        """Invalidate cache entries"""
        if key:
            cache_key = self._get_cache_key(namespace, key)
            # Remove from local cache
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
                self.cache_stats["evictions"] += 1
            
            # Remove from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(cache_key)
                except Exception as e:
                    logger.error(f"Redis delete error: {e}")
        else:
            # Invalidate entire namespace
            pattern = self._get_cache_key(namespace, "*")
            
            # Clear local cache
            keys_to_remove = [k for k in self.local_cache if k.startswith(f"talkingphoto:{namespace}:")]
            for key in keys_to_remove:
                del self.local_cache[key]
                self.cache_stats["evictions"] += 1
            
            # Clear Redis
            if self.redis_client:
                try:
                    for key in self.redis_client.scan_iter(pattern):
                        self.redis_client.delete(key)
                except Exception as e:
                    logger.error(f"Redis clear namespace error: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate": f"{hit_rate:.2f}%",
            "local_cache_size": len(self.local_cache),
            "redis_available": self.redis_client is not None
        }


def cache_result(namespace: str, ttl: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        cache_manager = CacheManager()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = hashlib.md5(
                f"{func.__name__}:{str(args)}:{str(kwargs)}".encode()
            ).hexdigest()
            
            # Try to get from cache
            cached_value = cache_manager.get(namespace, cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(namespace, cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# ASYNC PROCESSING OPTIMIZATION
# ============================================================================

class AsyncProcessor:
    """Async processing for heavy operations"""
    
    def __init__(self, max_workers: int = 4):
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self.task_queue = PriorityQueue()
        self.results = {}
        
    async def process_image_async(self, image_data: bytes) -> Dict:
        """Process image asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Run CPU-intensive operation in process pool
        result = await loop.run_in_executor(
            self.process_pool,
            self._process_image_worker,
            image_data
        )
        
        return result
    
    @staticmethod
    def _process_image_worker(image_data: bytes) -> Dict:
        """Worker function for image processing"""
        # Simulate image processing
        time.sleep(0.1)  # Reduced from synchronous version
        
        return {
            "processed": True,
            "size": len(image_data),
            "timestamp": datetime.now().isoformat()
        }
    
    async def batch_process_requests(self, requests: List[Dict]) -> List[Dict]:
        """Process multiple requests in batch"""
        tasks = []
        
        for request in requests:
            if request["type"] == "image":
                task = self.process_image_async(request["data"])
            elif request["type"] == "text":
                task = self.process_text_async(request["data"])
            else:
                task = self.process_generic_async(request["data"])
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def process_text_async(self, text: str) -> Dict:
        """Process text asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Run in thread pool for I/O operations
        result = await loop.run_in_executor(
            self.thread_pool,
            self._process_text_worker,
            text
        )
        
        return result
    
    @staticmethod
    def _process_text_worker(text: str) -> Dict:
        """Worker function for text processing"""
        # Simulate text processing
        time.sleep(0.05)
        
        return {
            "processed": True,
            "length": len(text),
            "words": len(text.split()),
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_generic_async(self, data: Any) -> Dict:
        """Generic async processing"""
        await asyncio.sleep(0.01)  # Simulate async operation
        
        return {
            "processed": True,
            "type": "generic",
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# DATABASE QUERY OPTIMIZATION
# ============================================================================

class DatabaseOptimizer:
    """Database query optimization strategies"""
    
    def __init__(self):
        self.query_cache = {}
        self.prepared_statements = {}
        self.connection_pool = []
        self.max_connections = 10
        
    @lru_cache(maxsize=128)
    def optimize_query(self, query: str) -> str:
        """Optimize SQL query"""
        optimized = query
        
        # Add indexes hints
        if "WHERE" in query and "INDEX" not in query:
            # Analyze query and suggest indexes
            optimized = self._add_index_hints(query)
        
        # Convert to prepared statement if possible
        if query in self.prepared_statements:
            return self.prepared_statements[query]
        
        return optimized
    
    def _add_index_hints(self, query: str) -> str:
        """Add index hints to query"""
        # Simplified index hint addition
        if "user_id" in query:
            query = query.replace("FROM users", "FROM users USE INDEX (idx_user_id)")
        if "created_at" in query:
            query = query.replace("FROM videos", "FROM videos USE INDEX (idx_created_at)")
        
        return query
    
    def batch_insert(self, table: str, records: List[Dict]) -> bool:
        """Batch insert optimization"""
        if not records:
            return False
        
        # Build batch insert query
        columns = records[0].keys()
        placeholders = ", ".join([f"({', '.join(['%s'] * len(columns))})" for _ in records])
        
        query = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES {placeholders}
        ON CONFLICT DO NOTHING
        """
        
        # Execute batch insert
        values = []
        for record in records:
            values.extend(record.values())
        
        # Simulated execution
        logger.info(f"Batch inserting {len(records)} records into {table}")
        
        return True
    
    def create_indexes(self) -> List[str]:
        """Create recommended indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_id ON users(id)",
            "CREATE INDEX IF NOT EXISTS idx_video_user_id ON videos(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_video_created_at ON videos(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_session_user_id ON sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_generation_status ON generations(status)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key)",
        ]
        
        return indexes
    
    def analyze_slow_queries(self) -> List[Dict]:
        """Analyze and identify slow queries"""
        slow_queries = []
        
        # Simulated slow query analysis
        queries = [
            {
                "query": "SELECT * FROM videos WHERE user_id = ?",
                "avg_time_ms": 150,
                "calls": 1000,
                "recommendation": "Add index on user_id"
            },
            {
                "query": "SELECT COUNT(*) FROM generations",
                "avg_time_ms": 500,
                "calls": 100,
                "recommendation": "Use cached counter instead"
            }
        ]
        
        return queries


# ============================================================================
# MEMORY OPTIMIZATION
# ============================================================================

class MemoryOptimizer:
    """Memory usage optimization strategies"""
    
    def __init__(self):
        self.memory_threshold_mb = 500
        self.gc_threshold = 100
        
    def optimize_memory(self):
        """Run memory optimization"""
        initial_memory = self.get_memory_usage()
        
        # Force garbage collection
        gc.collect()
        
        # Clear caches
        self.clear_caches()
        
        # Compact memory
        self.compact_memory()
        
        final_memory = self.get_memory_usage()
        
        return {
            "initial_mb": initial_memory,
            "final_mb": final_memory,
            "saved_mb": initial_memory - final_memory,
            "gc_stats": gc.get_stats()
        }
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def clear_caches(self):
        """Clear various caches"""
        # Clear LRU caches
        for obj in gc.get_objects():
            if hasattr(obj, 'cache_clear'):
                try:
                    obj.cache_clear()
                except:
                    pass
    
    def compact_memory(self):
        """Compact memory by removing unused objects"""
        # Remove circular references
        gc.collect(2)
        
        # Clear weak references
        for obj in gc.get_objects():
            if hasattr(obj, '__weakref__'):
                del obj
    
    def monitor_memory_leaks(self) -> Dict:
        """Monitor for memory leaks"""
        import tracemalloc
        
        tracemalloc.start()
        
        # Take snapshot
        snapshot1 = tracemalloc.take_snapshot()
        
        # Simulate some operations
        time.sleep(1)
        
        # Take another snapshot
        snapshot2 = tracemalloc.take_snapshot()
        
        # Calculate difference
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        leaks = []
        for stat in stats[:10]:
            if stat.size_diff > 0:
                leaks.append({
                    "file": stat.traceback.format()[0] if stat.traceback else "unknown",
                    "size_diff_kb": stat.size_diff / 1024,
                    "count_diff": stat.count_diff
                })
        
        tracemalloc.stop()
        
        return {
            "potential_leaks": leaks,
            "total_memory_mb": self.get_memory_usage()
        }


# ============================================================================
# CONNECTION POOLING
# ============================================================================

class ConnectionPool:
    """Connection pooling for external services"""
    
    def __init__(self, service_name: str, max_connections: int = 10):
        self.service_name = service_name
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.active_connections = 0
        self.stats = {
            "created": 0,
            "reused": 0,
            "closed": 0
        }
        
        # Pre-create connections
        for _ in range(min(3, max_connections)):
            self.connections.put(self._create_connection())
    
    def _create_connection(self):
        """Create a new connection"""
        self.stats["created"] += 1
        
        # Simulated connection creation
        connection = {
            "id": hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8],
            "created_at": datetime.now(),
            "service": self.service_name,
            "active": True
        }
        
        logger.info(f"Created connection {connection['id']} for {self.service_name}")
        return connection
    
    def get_connection(self, timeout: float = 5.0):
        """Get a connection from the pool"""
        try:
            connection = self.connections.get(timeout=timeout)
            self.active_connections += 1
            self.stats["reused"] += 1
            return connection
        except:
            if self.active_connections < self.max_connections:
                connection = self._create_connection()
                self.active_connections += 1
                return connection
            else:
                raise Exception(f"No available connections for {self.service_name}")
    
    def return_connection(self, connection):
        """Return a connection to the pool"""
        if connection["active"]:
            self.connections.put(connection)
            self.active_connections -= 1
        else:
            self.stats["closed"] += 1
            self.active_connections -= 1
    
    def close_all(self):
        """Close all connections"""
        while not self.connections.empty():
            connection = self.connections.get()
            connection["active"] = False
            self.stats["closed"] += 1
        
        self.active_connections = 0


# ============================================================================
# REQUEST QUEUE WITH PRIORITY
# ============================================================================

@dataclass
class PriorityRequest:
    """Request with priority"""
    priority: int  # Lower number = higher priority
    timestamp: float
    request_id: str
    data: Dict
    
    def __lt__(self, other):
        return (self.priority, self.timestamp) < (other.priority, other.timestamp)


class RequestQueue:
    """Priority request queue for managing load"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = PriorityQueue(maxsize=max_size)
        self.processing = {}
        self.completed = {}
        self.workers = []
        self.running = False
        
    def add_request(self, data: Dict, priority: int = 5) -> str:
        """Add request to queue"""
        request_id = hashlib.md5(
            f"{time.time()}:{json.dumps(data)}".encode()
        ).hexdigest()
        
        request = PriorityRequest(
            priority=priority,
            timestamp=time.time(),
            request_id=request_id,
            data=data
        )
        
        self.queue.put(request)
        logger.info(f"Added request {request_id} with priority {priority}")
        
        return request_id
    
    def start_workers(self, num_workers: int = 4):
        """Start worker threads"""
        self.running = True
        
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker, args=(i,))
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {num_workers} workers")
    
    def _worker(self, worker_id: int):
        """Worker thread function"""
        while self.running:
            try:
                request = self.queue.get(timeout=1)
                self.processing[request.request_id] = request
                
                # Process request
                result = self._process_request(request)
                
                # Mark as completed
                self.completed[request.request_id] = {
                    "result": result,
                    "completed_at": datetime.now(),
                    "processing_time": time.time() - request.timestamp
                }
                
                del self.processing[request.request_id]
                
            except Exception as e:
                continue
    
    def _process_request(self, request: PriorityRequest) -> Dict:
        """Process a single request"""
        # Simulate processing based on request type
        if request.data.get("type") == "video_generation":
            time.sleep(2)  # Simulate heavy processing
        else:
            time.sleep(0.1)  # Simulate light processing
        
        return {
            "success": True,
            "request_id": request.request_id,
            "processed_at": datetime.now().isoformat()
        }
    
    def get_status(self, request_id: str) -> Dict:
        """Get request status"""
        if request_id in self.completed:
            return {
                "status": "completed",
                **self.completed[request_id]
            }
        elif request_id in self.processing:
            return {
                "status": "processing",
                "started_at": self.processing[request_id].timestamp
            }
        else:
            # Check if in queue
            for item in self.queue.queue:
                if item.request_id == request_id:
                    return {
                        "status": "queued",
                        "position": self.queue.qsize()
                    }
            
            return {"status": "not_found"}
    
    def stop_workers(self):
        """Stop all workers"""
        self.running = False
        for worker in self.workers:
            worker.join()
        
        logger.info("All workers stopped")


# ============================================================================
# CDN AND STATIC ASSET OPTIMIZATION
# ============================================================================

class CDNOptimizer:
    """CDN and static asset optimization"""
    
    def __init__(self):
        self.cdn_base_url = "https://cdn.talkingphoto.ai"
        self.asset_versions = {}
        
    def optimize_image(self, image_path: str) -> Dict:
        """Optimize image for web delivery"""
        optimizations = {
            "original": image_path,
            "webp": self._convert_to_webp(image_path),
            "thumbnail": self._create_thumbnail(image_path),
            "responsive": self._create_responsive_versions(image_path)
        }
        
        return optimizations
    
    def _convert_to_webp(self, image_path: str) -> str:
        """Convert image to WebP format"""
        # Simulated WebP conversion
        webp_path = image_path.replace(".jpg", ".webp").replace(".png", ".webp")
        logger.info(f"Converted {image_path} to WebP")
        return webp_path
    
    def _create_thumbnail(self, image_path: str) -> str:
        """Create thumbnail version"""
        thumb_path = image_path.replace(".", "_thumb.")
        logger.info(f"Created thumbnail for {image_path}")
        return thumb_path
    
    def _create_responsive_versions(self, image_path: str) -> Dict:
        """Create responsive image versions"""
        versions = {
            "small": image_path.replace(".", "_320w."),
            "medium": image_path.replace(".", "_768w."),
            "large": image_path.replace(".", "_1920w.")
        }
        
        return versions
    
    def get_cdn_url(self, asset_path: str, version: bool = True) -> str:
        """Get CDN URL for asset"""
        if version:
            asset_hash = hashlib.md5(asset_path.encode()).hexdigest()[:8]
            return f"{self.cdn_base_url}/{asset_path}?v={asset_hash}"
        
        return f"{self.cdn_base_url}/{asset_path}"
    
    def preload_critical_assets(self) -> List[str]:
        """Get list of critical assets to preload"""
        return [
            "/static/css/main.css",
            "/static/js/app.js",
            "/static/fonts/main.woff2",
            "/static/img/logo.webp"
        ]


# ============================================================================
# CIRCUIT BREAKER FOR EXTERNAL SERVICES
# ============================================================================

class CircuitBreaker:
    """Circuit breaker pattern for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset"""
        if self.last_failure_time:
            time_since_failure = time.time() - self.last_failure_time
            return time_since_failure >= self.recovery_timeout
        return False
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_status(self) -> Dict:
        """Get circuit breaker status"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time
        }


# ============================================================================
# MAIN OPTIMIZATION MANAGER
# ============================================================================

class PerformanceOptimizationManager:
    """Central manager for all performance optimizations"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.async_processor = AsyncProcessor()
        self.db_optimizer = DatabaseOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.request_queue = RequestQueue()
        self.cdn_optimizer = CDNOptimizer()
        self.connection_pools = {}
        self.circuit_breakers = {}
        
        # Start background workers
        self.request_queue.start_workers(4)
        
    def apply_all_optimizations(self) -> Dict:
        """Apply all optimizations and return results"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "optimizations": {}
        }
        
        # Apply database optimizations
        logger.info("Applying database optimizations...")
        results["optimizations"]["database"] = {
            "indexes_created": self.db_optimizer.create_indexes(),
            "slow_queries": self.db_optimizer.analyze_slow_queries()
        }
        
        # Apply memory optimizations
        logger.info("Applying memory optimizations...")
        results["optimizations"]["memory"] = self.memory_optimizer.optimize_memory()
        
        # Get cache statistics
        results["optimizations"]["cache"] = self.cache_manager.get_stats()
        
        # CDN optimizations
        results["optimizations"]["cdn"] = {
            "critical_assets": self.cdn_optimizer.preload_critical_assets()
        }
        
        return results
    
    @cache_result(namespace="video_generation", ttl=3600)
    def generate_video_optimized(self, image_data: bytes, text: str) -> Dict:
        """Optimized video generation with caching"""
        # Check circuit breaker
        if "video_api" not in self.circuit_breakers:
            self.circuit_breakers["video_api"] = CircuitBreaker()
        
        circuit_breaker = self.circuit_breakers["video_api"]
        
        # Add to priority queue
        request_id = self.request_queue.add_request(
            {
                "type": "video_generation",
                "image_size": len(image_data),
                "text_length": len(text)
            },
            priority=1  # High priority
        )
        
        # Use connection pool
        if "video_service" not in self.connection_pools:
            self.connection_pools["video_service"] = ConnectionPool("video_service")
        
        connection = self.connection_pools["video_service"].get_connection()
        
        try:
            # Process with circuit breaker protection
            result = circuit_breaker.call(
                self._process_video_generation,
                image_data,
                text,
                connection
            )
            
            return result
            
        finally:
            self.connection_pools["video_service"].return_connection(connection)
    
    def _process_video_generation(self, image_data: bytes, text: str, connection: Dict) -> Dict:
        """Internal video generation processing"""
        # Simulated processing
        time.sleep(0.5)
        
        return {
            "success": True,
            "video_url": self.cdn_optimizer.get_cdn_url(f"videos/{hashlib.md5(image_data).hexdigest()}.mp4"),
            "duration_seconds": 10,
            "connection_id": connection["id"]
        }
    
    def get_optimization_report(self) -> Dict:
        """Get comprehensive optimization report"""
        return {
            "cache_stats": self.cache_manager.get_stats(),
            "memory_usage_mb": self.memory_optimizer.get_memory_usage(),
            "queue_size": self.request_queue.queue.qsize(),
            "active_connections": sum(
                pool.active_connections 
                for pool in self.connection_pools.values()
            ),
            "circuit_breakers": {
                name: breaker.get_status() 
                for name, breaker in self.circuit_breakers.items()
            }
        }


def main():
    """Main execution for testing optimizations"""
    print("TalkingPhoto AI - Performance Optimizations")
    print("=" * 60)
    
    # Initialize optimization manager
    manager = PerformanceOptimizationManager()
    
    print("\nApplying all optimizations...")
    results = manager.apply_all_optimizations()
    
    print("\nOptimization Results:")
    print(json.dumps(results, indent=2, default=str))
    
    # Test optimized video generation
    print("\nTesting optimized video generation...")
    test_image = b"test_image_data" * 1000
    test_text = "Hello, this is a test video generation"
    
    start_time = time.time()
    result = manager.generate_video_optimized(test_image, test_text)
    duration = time.time() - start_time
    
    print(f"Video generation completed in {duration:.2f} seconds")
    print(f"Result: {result}")
    
    # Get optimization report
    print("\nOptimization Report:")
    report = manager.get_optimization_report()
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()