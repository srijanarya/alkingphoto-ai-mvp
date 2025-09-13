"""
TalkingPhoto AI MVP - Cost Optimization Service
Smart API routing and cost optimization for video generation
"""

import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from redis import Redis
import structlog
from flask import current_app

from models.video import VideoQuality, AspectRatio, AIProvider
from services.video_generation_service import VideoGenerationProvider, ProviderCapabilities

logger = structlog.get_logger()


@dataclass
class ProviderMetrics:
    """Real-time provider performance metrics"""
    provider: VideoGenerationProvider
    success_rate: float  # Last 24 hours
    average_processing_time: float  # Seconds
    average_cost: float  # Per second
    current_load: int  # Active jobs
    error_count: int  # Last hour
    availability_score: float  # 0-1 score
    quality_score: float  # Average user rating


@dataclass
class CostEstimate:
    """Cost estimate for video generation"""
    provider: VideoGenerationProvider
    estimated_cost: float
    confidence: float  # 0-1 confidence in estimate
    processing_time: float  # Estimated seconds
    quality_score: float  # Expected quality


class CostOptimizationService:
    """
    Intelligent cost optimization and API routing service
    """
    
    def __init__(self):
        self.redis_client = Redis(
            host=current_app.config.get('REDIS_HOST', 'localhost'),
            port=current_app.config.get('REDIS_PORT', 6379),
            decode_responses=True
        )
        
        # Provider cost matrix (per second of video)
        self.base_costs = {
            VideoGenerationProvider.VEO3: 0.15,
            VideoGenerationProvider.RUNWAY: 0.20,
            VideoGenerationProvider.SYNTHESIA: 0.25,
            VideoGenerationProvider.D_ID: 0.10,
            VideoGenerationProvider.HEYGEN: 0.18
        }
        
        # Quality multipliers
        self.quality_multipliers = {
            VideoQuality.ECONOMY: 0.7,
            VideoQuality.STANDARD: 1.0,
            VideoQuality.PREMIUM: 1.5
        }
        
        # Time-based pricing adjustments (peak hours cost more)
        self.time_multipliers = {
            'peak': 1.3,      # 9 AM - 5 PM workdays
            'standard': 1.0,   # 5 PM - 12 AM
            'off_peak': 0.8    # 12 AM - 9 AM and weekends
        }
        
        # Initialize provider metrics cache
        self._init_metrics_cache()
    
    def _init_metrics_cache(self):
        """Initialize provider metrics in Redis"""
        for provider in VideoGenerationProvider:
            metrics_key = f"provider_metrics:{provider.value}"
            if not self.redis_client.exists(metrics_key):
                default_metrics = {
                    'success_rate': 0.95,
                    'average_processing_time': 60,
                    'average_cost': self.base_costs.get(provider, 0.15),
                    'current_load': 0,
                    'error_count': 0,
                    'availability_score': 0.95,
                    'quality_score': 0.85
                }
                self.redis_client.hset(metrics_key, mapping=default_metrics)
                self.redis_client.expire(metrics_key, 86400)  # 24 hour TTL
    
    def select_optimal_provider(self, duration: float, quality: VideoQuality,
                               aspect_ratio: AspectRatio, user_preferences: Dict[str, Any] = None) -> Tuple[VideoGenerationProvider, CostEstimate]:
        """
        Select optimal provider based on multiple factors
        
        Args:
            duration: Video duration in seconds
            quality: Desired video quality
            aspect_ratio: Video aspect ratio
            user_preferences: User preferences (budget, speed, quality priority)
        
        Returns:
            Tuple of selected provider and cost estimate
        """
        user_preferences = user_preferences or {}
        
        # Get current metrics for all providers
        provider_scores = []
        
        for provider in VideoGenerationProvider:
            # Check if provider supports requirements
            if not self._provider_supports_requirements(provider, duration, quality, aspect_ratio):
                continue
            
            # Get provider metrics
            metrics = self._get_provider_metrics(provider)
            
            # Calculate cost estimate
            cost_estimate = self._calculate_cost_estimate(provider, duration, quality, metrics)
            
            # Calculate optimization score
            score = self._calculate_optimization_score(
                provider, metrics, cost_estimate, user_preferences
            )
            
            provider_scores.append((provider, score, cost_estimate))
        
        if not provider_scores:
            # Fallback to default provider
            default_provider = VideoGenerationProvider.VEO3
            default_estimate = self._calculate_cost_estimate(
                default_provider, duration, quality,
                self._get_provider_metrics(default_provider)
            )
            return default_provider, default_estimate
        
        # Sort by score and select best
        provider_scores.sort(key=lambda x: x[1], reverse=True)
        selected_provider, _, cost_estimate = provider_scores[0]
        
        # Log selection
        logger.info("Provider selected",
                   provider=selected_provider.value,
                   cost=cost_estimate.estimated_cost,
                   score=provider_scores[0][1])
        
        return selected_provider, cost_estimate
    
    def _provider_supports_requirements(self, provider: VideoGenerationProvider,
                                       duration: float, quality: VideoQuality,
                                       aspect_ratio: AspectRatio) -> bool:
        """Check if provider supports the requirements"""
        # Import capabilities from video generation service
        from services.video_generation_service import VideoGenerationPipeline
        
        capabilities = VideoGenerationPipeline.PROVIDER_CAPABILITIES.get(provider)
        if not capabilities:
            return False
        
        return (duration <= capabilities.max_duration and
                quality in capabilities.supported_qualities and
                aspect_ratio in capabilities.supported_aspects)
    
    def _get_provider_metrics(self, provider: VideoGenerationProvider) -> ProviderMetrics:
        """Get current metrics for provider"""
        metrics_key = f"provider_metrics:{provider.value}"
        metrics_data = self.redis_client.hgetall(metrics_key)
        
        return ProviderMetrics(
            provider=provider,
            success_rate=float(metrics_data.get('success_rate', 0.95)),
            average_processing_time=float(metrics_data.get('average_processing_time', 60)),
            average_cost=float(metrics_data.get('average_cost', self.base_costs.get(provider, 0.15))),
            current_load=int(metrics_data.get('current_load', 0)),
            error_count=int(metrics_data.get('error_count', 0)),
            availability_score=float(metrics_data.get('availability_score', 0.95)),
            quality_score=float(metrics_data.get('quality_score', 0.85))
        )
    
    def _calculate_cost_estimate(self, provider: VideoGenerationProvider,
                                duration: float, quality: VideoQuality,
                                metrics: ProviderMetrics) -> CostEstimate:
        """Calculate cost estimate for provider"""
        # Base cost
        base_cost = metrics.average_cost * duration
        
        # Apply quality multiplier
        quality_mult = self.quality_multipliers.get(quality, 1.0)
        
        # Apply time-based pricing
        time_mult = self._get_time_multiplier()
        
        # Apply load-based pricing (surge pricing)
        load_mult = self._get_load_multiplier(metrics.current_load)
        
        # Final cost
        estimated_cost = base_cost * quality_mult * time_mult * load_mult
        
        # Calculate confidence based on recent performance
        confidence = min(metrics.success_rate * metrics.availability_score, 0.99)
        
        # Estimate processing time
        processing_time = metrics.average_processing_time * (1 + (metrics.current_load * 0.1))
        
        return CostEstimate(
            provider=provider,
            estimated_cost=round(estimated_cost, 2),
            confidence=confidence,
            processing_time=processing_time,
            quality_score=metrics.quality_score
        )
    
    def _calculate_optimization_score(self, provider: VideoGenerationProvider,
                                     metrics: ProviderMetrics,
                                     cost_estimate: CostEstimate,
                                     user_preferences: Dict[str, Any]) -> float:
        """
        Calculate optimization score for provider selection
        
        Factors:
        - Cost efficiency (40%)
        - Processing speed (20%)
        - Quality (25%)
        - Reliability (15%)
        """
        # Get user preference weights (default balanced)
        cost_weight = user_preferences.get('cost_priority', 0.4)
        speed_weight = user_preferences.get('speed_priority', 0.2)
        quality_weight = user_preferences.get('quality_priority', 0.25)
        reliability_weight = user_preferences.get('reliability_priority', 0.15)
        
        # Normalize weights
        total_weight = cost_weight + speed_weight + quality_weight + reliability_weight
        if total_weight > 0:
            cost_weight /= total_weight
            speed_weight /= total_weight
            quality_weight /= total_weight
            reliability_weight /= total_weight
        
        # Calculate component scores (0-1 scale)
        
        # Cost score (inverse - lower cost = higher score)
        max_cost = 0.30  # Maximum expected cost per second
        cost_score = max(0, 1 - (cost_estimate.estimated_cost / (max_cost * 60)))
        
        # Speed score (inverse - faster = higher score)
        max_time = 300  # Maximum expected processing time
        speed_score = max(0, 1 - (cost_estimate.processing_time / max_time))
        
        # Quality score (direct)
        quality_score = metrics.quality_score
        
        # Reliability score (combination of success rate and availability)
        reliability_score = (metrics.success_rate * 0.7 + metrics.availability_score * 0.3)
        
        # Apply error penalty
        if metrics.error_count > 5:
            reliability_score *= 0.5
        elif metrics.error_count > 2:
            reliability_score *= 0.8
        
        # Calculate weighted score
        total_score = (
            cost_score * cost_weight +
            speed_score * speed_weight +
            quality_score * quality_weight +
            reliability_score * reliability_weight
        )
        
        # Apply load balancing bonus (prefer less loaded providers)
        if metrics.current_load < 5:
            total_score *= 1.1
        elif metrics.current_load > 20:
            total_score *= 0.9
        
        return min(total_score, 1.0)
    
    def _get_time_multiplier(self) -> float:
        """Get time-based pricing multiplier"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        weekday = now.weekday()
        
        # Weekend off-peak
        if weekday >= 5:  # Saturday or Sunday
            return self.time_multipliers['off_peak']
        
        # Weekday peak hours (9 AM - 5 PM UTC)
        if 9 <= hour < 17:
            return self.time_multipliers['peak']
        
        # Weekday standard hours (5 PM - 12 AM UTC)
        if 17 <= hour < 24:
            return self.time_multipliers['standard']
        
        # Weekday off-peak (12 AM - 9 AM UTC)
        return self.time_multipliers['off_peak']
    
    def _get_load_multiplier(self, current_load: int) -> float:
        """Get load-based pricing multiplier (surge pricing)"""
        if current_load < 10:
            return 1.0
        elif current_load < 20:
            return 1.1
        elif current_load < 30:
            return 1.2
        else:
            return 1.3
    
    def update_provider_metrics(self, provider: VideoGenerationProvider,
                               success: bool, processing_time: float,
                               actual_cost: float, quality_rating: float = None):
        """
        Update provider metrics after job completion
        
        Args:
            provider: Provider used
            success: Whether job succeeded
            processing_time: Actual processing time in seconds
            actual_cost: Actual cost incurred
            quality_rating: Optional user quality rating (0-5)
        """
        try:
            metrics_key = f"provider_metrics:{provider.value}"
            current_metrics = self.redis_client.hgetall(metrics_key)
            
            # Update success rate (exponential moving average)
            alpha = 0.1  # Smoothing factor
            current_success_rate = float(current_metrics.get('success_rate', 0.95))
            new_success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * current_success_rate
            
            # Update average processing time
            current_avg_time = float(current_metrics.get('average_processing_time', 60))
            new_avg_time = alpha * processing_time + (1 - alpha) * current_avg_time
            
            # Update average cost
            current_avg_cost = float(current_metrics.get('average_cost', self.base_costs.get(provider, 0.15)))
            new_avg_cost = alpha * (actual_cost / max(processing_time / 60, 1)) + (1 - alpha) * current_avg_cost
            
            # Update error count
            error_count = int(current_metrics.get('error_count', 0))
            if not success:
                error_count += 1
            else:
                error_count = max(0, error_count - 1)  # Decay error count on success
            
            # Update quality score if rating provided
            if quality_rating is not None:
                current_quality = float(current_metrics.get('quality_score', 0.85))
                normalized_rating = quality_rating / 5.0
                new_quality = alpha * normalized_rating + (1 - alpha) * current_quality
            else:
                new_quality = float(current_metrics.get('quality_score', 0.85))
            
            # Update availability score
            availability = new_success_rate * (1 - min(error_count / 10, 0.5))
            
            # Update current load
            current_load = int(current_metrics.get('current_load', 0))
            if success:
                current_load = max(0, current_load - 1)
            
            # Save updated metrics
            updated_metrics = {
                'success_rate': new_success_rate,
                'average_processing_time': new_avg_time,
                'average_cost': new_avg_cost,
                'current_load': current_load,
                'error_count': error_count,
                'availability_score': availability,
                'quality_score': new_quality
            }
            
            self.redis_client.hset(metrics_key, mapping=updated_metrics)
            self.redis_client.expire(metrics_key, 86400)  # Refresh TTL
            
            # Log metrics update
            logger.info("Provider metrics updated",
                       provider=provider.value,
                       success_rate=new_success_rate,
                       avg_time=new_avg_time)
            
        except Exception as e:
            logger.error("Failed to update provider metrics", error=str(e))
    
    def increment_provider_load(self, provider: VideoGenerationProvider):
        """Increment current load for provider when job starts"""
        try:
            metrics_key = f"provider_metrics:{provider.value}"
            self.redis_client.hincrby(metrics_key, 'current_load', 1)
        except Exception as e:
            logger.error("Failed to increment provider load", error=str(e))
    
    def get_cost_breakdown(self, duration: float, quality: VideoQuality,
                          provider: VideoGenerationProvider = None) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for video generation
        
        Returns:
            Detailed cost breakdown including all factors
        """
        breakdown = {
            'duration_seconds': duration,
            'quality': quality.value,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if provider:
            # Breakdown for specific provider
            metrics = self._get_provider_metrics(provider)
            cost_estimate = self._calculate_cost_estimate(provider, duration, quality, metrics)
            
            base_cost = self.base_costs.get(provider, 0.15) * duration
            quality_mult = self.quality_multipliers.get(quality, 1.0)
            time_mult = self._get_time_multiplier()
            load_mult = self._get_load_multiplier(metrics.current_load)
            
            breakdown['provider'] = provider.value
            breakdown['base_cost'] = round(base_cost, 2)
            breakdown['quality_multiplier'] = quality_mult
            breakdown['time_multiplier'] = time_mult
            breakdown['load_multiplier'] = load_mult
            breakdown['estimated_total'] = cost_estimate.estimated_cost
            breakdown['confidence'] = cost_estimate.confidence
            breakdown['processing_time_estimate'] = cost_estimate.processing_time
            
        else:
            # Breakdown for all providers
            providers_breakdown = {}
            
            for provider in VideoGenerationProvider:
                if self._provider_supports_requirements(provider, duration, quality, AspectRatio.LANDSCAPE):
                    metrics = self._get_provider_metrics(provider)
                    cost_estimate = self._calculate_cost_estimate(provider, duration, quality, metrics)
                    
                    providers_breakdown[provider.value] = {
                        'estimated_cost': cost_estimate.estimated_cost,
                        'processing_time': cost_estimate.processing_time,
                        'quality_score': cost_estimate.quality_score,
                        'confidence': cost_estimate.confidence
                    }
            
            breakdown['providers'] = providers_breakdown
            
            # Add comparison metrics
            if providers_breakdown:
                costs = [p['estimated_cost'] for p in providers_breakdown.values()]
                breakdown['cheapest'] = min(costs)
                breakdown['most_expensive'] = max(costs)
                breakdown['average'] = round(sum(costs) / len(costs), 2)
                breakdown['savings_potential'] = round(max(costs) - min(costs), 2)
        
        return breakdown
    
    def get_usage_analytics(self, user_id: str, period_days: int = 30) -> Dict[str, Any]:
        """
        Get usage analytics and cost optimization recommendations
        
        Args:
            user_id: User ID
            period_days: Analysis period in days
        
        Returns:
            Usage analytics and recommendations
        """
        try:
            # Get usage history from Redis
            usage_key = f"user_usage:{user_id}"
            usage_data = self.redis_client.hgetall(usage_key)
            
            # Calculate statistics
            total_videos = int(usage_data.get('total_videos', 0))
            total_cost = float(usage_data.get('total_cost', 0))
            total_duration = float(usage_data.get('total_duration', 0))
            
            # Provider usage distribution
            provider_usage = json.loads(usage_data.get('provider_usage', '{}'))
            
            # Quality distribution
            quality_usage = json.loads(usage_data.get('quality_usage', '{}'))
            
            # Time pattern analysis
            time_pattern = json.loads(usage_data.get('time_pattern', '{}'))
            
            # Calculate averages
            avg_cost_per_video = total_cost / max(total_videos, 1)
            avg_duration = total_duration / max(total_videos, 1)
            
            # Generate recommendations
            recommendations = self._generate_cost_recommendations(
                provider_usage, quality_usage, time_pattern, avg_cost_per_video
            )
            
            return {
                'period_days': period_days,
                'total_videos': total_videos,
                'total_cost': round(total_cost, 2),
                'total_duration_seconds': total_duration,
                'average_cost_per_video': round(avg_cost_per_video, 2),
                'average_duration': round(avg_duration, 1),
                'provider_usage': provider_usage,
                'quality_distribution': quality_usage,
                'time_pattern': time_pattern,
                'recommendations': recommendations,
                'potential_savings': self._calculate_potential_savings(
                    provider_usage, quality_usage, total_cost
                )
            }
            
        except Exception as e:
            logger.error("Failed to get usage analytics", error=str(e))
            return {
                'error': 'Failed to retrieve analytics',
                'period_days': period_days
            }
    
    def _generate_cost_recommendations(self, provider_usage: Dict, quality_usage: Dict,
                                      time_pattern: Dict, avg_cost: float) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Check if using expensive providers frequently
        if provider_usage.get('runway', 0) > 30:
            recommendations.append(
                "Consider using Veo3 for standard quality videos to reduce costs by ~25%"
            )
        
        # Check quality usage
        premium_usage = quality_usage.get('premium', 0)
        if premium_usage > 50:
            recommendations.append(
                "Review if all videos need premium quality - standard quality can save 33% on costs"
            )
        
        # Check time patterns
        peak_usage = sum(time_pattern.get(str(h), 0) for h in range(9, 17))
        total_usage = sum(time_pattern.values()) if time_pattern else 1
        peak_percentage = (peak_usage / total_usage) * 100 if total_usage > 0 else 0
        
        if peak_percentage > 60:
            recommendations.append(
                "Schedule non-urgent videos during off-peak hours (12 AM - 9 AM) for 20% savings"
            )
        
        # Check average cost
        if avg_cost > 15:
            recommendations.append(
                "Your average cost per video is high - consider batch processing for better rates"
            )
        
        # Add bulk discount recommendation
        recommendations.append(
            "Contact sales for volume discounts if generating >100 videos per month"
        )
        
        return recommendations
    
    def _calculate_potential_savings(self, provider_usage: Dict, quality_usage: Dict,
                                    current_total_cost: float) -> float:
        """Calculate potential savings with optimization"""
        potential_cost = current_total_cost
        
        # Savings from provider optimization
        if provider_usage.get('runway', 0) > 0:
            runway_portion = provider_usage['runway'] / 100
            potential_cost *= (1 - runway_portion * 0.25)  # 25% savings switching to Veo3
        
        # Savings from quality optimization
        premium_portion = quality_usage.get('premium', 0) / 100
        if premium_portion > 0.3:
            potential_cost *= (1 - (premium_portion - 0.3) * 0.33)  # 33% savings on excess premium
        
        # Savings from time optimization
        potential_cost *= 0.9  # 10% average savings from off-peak usage
        
        savings = current_total_cost - potential_cost
        return round(max(savings, 0), 2)
    
    def track_usage(self, user_id: str, provider: VideoGenerationProvider,
                   duration: float, quality: VideoQuality, cost: float):
        """
        Track user usage for analytics
        
        Args:
            user_id: User ID
            provider: Provider used
            duration: Video duration in seconds
            quality: Video quality
            cost: Actual cost incurred
        """
        try:
            usage_key = f"user_usage:{user_id}"
            
            # Increment counters
            self.redis_client.hincrby(usage_key, 'total_videos', 1)
            self.redis_client.hincrbyfloat(usage_key, 'total_cost', cost)
            self.redis_client.hincrbyfloat(usage_key, 'total_duration', duration)
            
            # Update provider usage
            provider_usage = json.loads(self.redis_client.hget(usage_key, 'provider_usage') or '{}')
            provider_usage[provider.value] = provider_usage.get(provider.value, 0) + 1
            self.redis_client.hset(usage_key, 'provider_usage', json.dumps(provider_usage))
            
            # Update quality usage
            quality_usage = json.loads(self.redis_client.hget(usage_key, 'quality_usage') or '{}')
            quality_usage[quality.value] = quality_usage.get(quality.value, 0) + 1
            self.redis_client.hset(usage_key, 'quality_usage', json.dumps(quality_usage))
            
            # Update time pattern
            hour = datetime.now(timezone.utc).hour
            time_pattern = json.loads(self.redis_client.hget(usage_key, 'time_pattern') or '{}')
            time_pattern[str(hour)] = time_pattern.get(str(hour), 0) + 1
            self.redis_client.hset(usage_key, 'time_pattern', json.dumps(time_pattern))
            
            # Set expiry
            self.redis_client.expire(usage_key, 2592000)  # 30 days
            
        except Exception as e:
            logger.error("Failed to track usage", error=str(e))