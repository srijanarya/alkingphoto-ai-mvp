"""
TalkingPhoto AI MVP - Simple Caching System

In-memory caching for development mode.
No external dependencies required.
"""

import time
import hashlib
import json
from typing import Any, Dict, Optional
from functools import wraps

class SimpleCache:
    """Simple in-memory cache for AI responses and processed data"""
    
    def __init__(self, max_size: int = 100):
        """Initialize simple cache
        
        Args:
            max_size: Maximum number of items to store
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            item = self.cache[key]
            # Check if expired
            if item['expires_at'] > time.time():
                self.hits += 1
                return item['value']
            else:
                # Remove expired item
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 5 minutes)
        """
        # Implement simple LRU by removing oldest if at max size
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['created_at'])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl
        }
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self.cache),
            'max_size': self.max_size
        }


# Global cache instance
_cache = SimpleCache()


def cached_result(ttl: int = 300):
    """Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{_cache._make_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Example usage for AI responses
@cached_result(ttl=600)  # Cache for 10 minutes
def get_ai_response(prompt: str, model: str = "mock") -> str:
    """Get AI response with caching"""
    # This would be replaced with actual AI call
    return f"AI response for: {prompt}"