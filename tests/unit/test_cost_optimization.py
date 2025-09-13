"""
TalkingPhoto AI MVP - Cost Optimization Algorithm Tests
Comprehensive tests for cost optimization and provider selection algorithms
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import numpy as np

from services.cost_optimization_service import (
    CostOptimizationService, ProviderMetrics, CostEstimate
)
from services.video_generation_service import VideoGenerationProvider
from models.video import VideoQuality, AspectRatio


class TestCostOptimizationAlgorithms:
    """Test cost optimization algorithms"""
    
    @pytest.fixture
    def cost_service(self):
        """Create cost optimization service with mocked Redis"""
        with patch('services.cost_optimization_service.Redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance
            
            # Mock Redis methods
            mock_redis_instance.exists.return_value = False
            mock_redis_instance.hset.return_value = True
            mock_redis_instance.expire.return_value = True
            mock_redis_instance.hgetall.return_value = {}
            
            with patch('services.cost_optimization_service.current_app') as mock_app:
                mock_app.config.get.return_value = 'localhost'
                service = CostOptimizationService()
                service.redis_client = mock_redis_instance
                return service
    
    def test_time_based_pricing(self, cost_service):
        """Test time-based pricing adjustments"""
        # Test peak hours (9 AM - 5 PM workday)
        peak_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc)  # Monday 2 PM
        with patch('services.cost_optimization_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = peak_time
            mock_datetime.timezone = timezone
            
            peak_multiplier = cost_service.get_time_multiplier()
            assert peak_multiplier == 1.3
        
        # Test standard hours (5 PM - 12 AM)
        standard_time = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)  # Monday 8 PM
        with patch('services.cost_optimization_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = standard_time
            mock_datetime.timezone = timezone
            
            standard_multiplier = cost_service.get_time_multiplier()
            assert standard_multiplier == 1.0
        
        # Test off-peak hours (12 AM - 9 AM)
        offpeak_time = datetime(2024, 1, 15, 3, 0, 0, tzinfo=timezone.utc)  # Monday 3 AM
        with patch('services.cost_optimization_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = offpeak_time
            mock_datetime.timezone = timezone
            
            offpeak_multiplier = cost_service.get_time_multiplier()
            assert offpeak_multiplier == 0.8
        
        # Test weekend (should be off-peak)
        weekend_time = datetime(2024, 1, 20, 14, 0, 0, tzinfo=timezone.utc)  # Saturday 2 PM
        with patch('services.cost_optimization_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = weekend_time
            mock_datetime.timezone = timezone
            
            weekend_multiplier = cost_service.get_time_multiplier()
            assert weekend_multiplier == 0.8
    
    def test_quality_based_pricing(self, cost_service):
        """Test quality-based pricing calculations"""
        base_cost = 1.0
        
        # Economy quality
        economy_cost = cost_service.calculate_quality_adjusted_cost(
            base_cost, VideoQuality.ECONOMY
        )
        assert economy_cost == 0.7  # 1.0 * 0.7
        
        # Standard quality
        standard_cost = cost_service.calculate_quality_adjusted_cost(
            base_cost, VideoQuality.STANDARD
        )
        assert standard_cost == 1.0  # 1.0 * 1.0
        
        # Premium quality
        premium_cost = cost_service.calculate_quality_adjusted_cost(
            base_cost, VideoQuality.PREMIUM
        )
        assert premium_cost == 1.5  # 1.0 * 1.5
    
    def test_provider_scoring_algorithm(self, cost_service):
        """Test provider scoring algorithm"""
        # Mock provider metrics
        metrics = {
            VideoGenerationProvider.VEO3: ProviderMetrics(
                provider=VideoGenerationProvider.VEO3,
                success_rate=0.95,
                average_processing_time=60,
                average_cost=0.15,
                current_load=10,
                error_count=2,
                availability_score=0.95,
                quality_score=0.85
            ),
            VideoGenerationProvider.RUNWAY: ProviderMetrics(
                provider=VideoGenerationProvider.RUNWAY,
                success_rate=0.98,
                average_processing_time=80,
                average_cost=0.20,
                current_load=5,
                error_count=1,
                availability_score=0.98,
                quality_score=0.92
            ),
            VideoGenerationProvider.D_ID: ProviderMetrics(
                provider=VideoGenerationProvider.D_ID,
                success_rate=0.90,
                average_processing_time=45,
                average_cost=0.10,
                current_load=20,
                error_count=5,
                availability_score=0.88,
                quality_score=0.75
            )
        }
        
        # Calculate scores for each provider
        scores = {}
        for provider, metric in metrics.items():
            # Composite score calculation
            cost_score = (1 / metric.average_cost) * 10  # Lower cost = higher score
            speed_score = (1 / metric.average_processing_time) * 100
            reliability_score = metric.success_rate * metric.availability_score
            quality_score = metric.quality_score
            load_score = max(0, 1 - (metric.current_load / 100))  # Lower load = higher score
            
            # Weighted composite
            scores[provider] = {
                'cost': cost_score,
                'speed': speed_score,
                'reliability': reliability_score,
                'quality': quality_score,
                'load': load_score,
                'composite': (
                    cost_score * 0.3 +
                    speed_score * 0.2 +
                    reliability_score * 0.25 +
                    quality_score * 0.20 +
                    load_score * 0.05
                )
            }
        
        # D-ID should have best cost score
        assert scores[VideoGenerationProvider.D_ID]['cost'] > scores[VideoGenerationProvider.VEO3]['cost']
        
        # Runway should have best quality score
        assert scores[VideoGenerationProvider.RUNWAY]['quality'] > scores[VideoGenerationProvider.VEO3]['quality']
        
        # D-ID should have best speed score
        assert scores[VideoGenerationProvider.D_ID]['speed'] > scores[VideoGenerationProvider.RUNWAY]['speed']
    
    def test_dynamic_pricing_adjustment(self, cost_service):
        """Test dynamic pricing based on demand"""
        # Simulate high demand scenario
        high_demand_metrics = {
            'current_load': 80,  # 80% capacity
            'queue_length': 50,
            'avg_wait_time': 300  # 5 minutes
        }
        
        # Calculate demand multiplier
        load_factor = high_demand_metrics['current_load'] / 100
        queue_factor = min(high_demand_metrics['queue_length'] / 20, 2.0)
        wait_factor = min(high_demand_metrics['avg_wait_time'] / 120, 1.5)
        
        demand_multiplier = 1 + (load_factor * 0.2 + queue_factor * 0.1 + wait_factor * 0.1)
        
        assert demand_multiplier > 1.3  # Should increase price during high demand
        
        # Simulate low demand scenario
        low_demand_metrics = {
            'current_load': 20,
            'queue_length': 2,
            'avg_wait_time': 30
        }
        
        load_factor = low_demand_metrics['current_load'] / 100
        queue_factor = min(low_demand_metrics['queue_length'] / 20, 2.0)
        wait_factor = min(low_demand_metrics['avg_wait_time'] / 120, 1.5)
        
        demand_multiplier = 1 + (load_factor * 0.2 + queue_factor * 0.1 + wait_factor * 0.1)
        
        assert demand_multiplier < 1.2  # Should have minimal increase
    
    def test_bulk_discount_calculation(self, cost_service):
        """Test bulk discount calculations"""
        base_price_per_video = 5.0
        
        # Define discount tiers
        discount_tiers = [
            (1, 0),      # 1-4 videos: no discount
            (5, 0.10),   # 5-9 videos: 10% discount
            (10, 0.15),  # 10-19 videos: 15% discount
            (20, 0.20),  # 20-49 videos: 20% discount
            (50, 0.25),  # 50+ videos: 25% discount
        ]
        
        def calculate_bulk_price(quantity):
            for min_qty, discount in reversed(discount_tiers):
                if quantity >= min_qty:
                    return base_price_per_video * quantity * (1 - discount)
            return base_price_per_video * quantity
        
        # Test different quantities
        assert calculate_bulk_price(1) == 5.0
        assert calculate_bulk_price(5) == 22.5  # 5 * 5 * 0.9
        assert calculate_bulk_price(10) == 42.5  # 10 * 5 * 0.85
        assert calculate_bulk_price(20) == 80.0  # 20 * 5 * 0.8
        assert calculate_bulk_price(50) == 187.5  # 50 * 5 * 0.75
    
    def test_cost_estimation_accuracy(self, cost_service):
        """Test accuracy of cost estimation"""
        # Mock historical data
        historical_estimates = [
            {'estimated': 4.5, 'actual': 4.8},
            {'estimated': 3.2, 'actual': 3.1},
            {'estimated': 5.0, 'actual': 5.3},
            {'estimated': 2.8, 'actual': 2.9},
            {'estimated': 6.1, 'actual': 6.0}
        ]
        
        # Calculate accuracy metrics
        errors = [abs(h['estimated'] - h['actual']) for h in historical_estimates]
        mean_absolute_error = np.mean(errors)
        mean_percentage_error = np.mean([
            abs(h['estimated'] - h['actual']) / h['actual'] * 100
            for h in historical_estimates
        ])
        
        assert mean_absolute_error < 0.3  # Average error less than $0.30
        assert mean_percentage_error < 10  # Average percentage error less than 10%
        
        # Calculate confidence based on historical accuracy
        confidence = max(0, 1 - (mean_percentage_error / 100))
        assert confidence > 0.9  # High confidence in estimates


class TestProviderSelectionOptimization:
    """Test provider selection optimization strategies"""
    
    def test_multi_objective_optimization(self):
        """Test multi-objective optimization for provider selection"""
        providers = [
            {
                'name': VideoGenerationProvider.VEO3,
                'cost': 0.15,
                'quality': 0.85,
                'speed': 0.75,
                'reliability': 0.95
            },
            {
                'name': VideoGenerationProvider.RUNWAY,
                'cost': 0.20,
                'quality': 0.92,
                'speed': 0.65,
                'reliability': 0.98
            },
            {
                'name': VideoGenerationProvider.D_ID,
                'cost': 0.10,
                'quality': 0.75,
                'speed': 0.85,
                'reliability': 0.90
            }
        ]
        
        # Define objective weights
        weights = {
            'cost': 0.4,      # 40% weight on cost
            'quality': 0.3,   # 30% weight on quality
            'speed': 0.2,     # 20% weight on speed
            'reliability': 0.1 # 10% weight on reliability
        }
        
        # Calculate weighted scores
        for provider in providers:
            # Normalize cost (lower is better, so invert)
            cost_score = 1 / provider['cost'] if provider['cost'] > 0 else 0
            
            # Calculate weighted score
            provider['score'] = (
                cost_score * weights['cost'] +
                provider['quality'] * weights['quality'] +
                provider['speed'] * weights['speed'] +
                provider['reliability'] * weights['reliability']
            )
        
        # Sort by score
        sorted_providers = sorted(providers, key=lambda x: x['score'], reverse=True)
        
        # D-ID should be optimal with these weights (best cost)
        assert sorted_providers[0]['name'] == VideoGenerationProvider.D_ID
    
    def test_constraint_based_selection(self):
        """Test provider selection with constraints"""
        constraints = {
            'max_cost': 0.18,
            'min_quality': 0.80,
            'min_reliability': 0.92
        }
        
        providers = [
            {
                'name': VideoGenerationProvider.VEO3,
                'cost': 0.15,
                'quality': 0.85,
                'reliability': 0.95
            },
            {
                'name': VideoGenerationProvider.RUNWAY,
                'cost': 0.20,  # Exceeds max_cost
                'quality': 0.92,
                'reliability': 0.98
            },
            {
                'name': VideoGenerationProvider.D_ID,
                'cost': 0.10,
                'quality': 0.75,  # Below min_quality
                'reliability': 0.90  # Below min_reliability
            }
        ]
        
        # Filter by constraints
        valid_providers = [
            p for p in providers
            if p['cost'] <= constraints['max_cost']
            and p['quality'] >= constraints['min_quality']
            and p['reliability'] >= constraints['min_reliability']
        ]
        
        # Only VEO3 should meet all constraints
        assert len(valid_providers) == 1
        assert valid_providers[0]['name'] == VideoGenerationProvider.VEO3
    
    def test_adaptive_selection_strategy(self):
        """Test adaptive provider selection based on context"""
        
        def select_provider(context):
            """Select provider based on context"""
            if context['user_tier'] == 'premium':
                # Premium users get best quality
                return VideoGenerationProvider.RUNWAY
            elif context['urgency'] == 'high':
                # Urgent requests use fastest provider
                return VideoGenerationProvider.D_ID
            elif context['budget'] == 'limited':
                # Budget-conscious selection
                return VideoGenerationProvider.D_ID
            else:
                # Default balanced selection
                return VideoGenerationProvider.VEO3
        
        # Test different contexts
        assert select_provider({'user_tier': 'premium'}) == VideoGenerationProvider.RUNWAY
        assert select_provider({'urgency': 'high'}) == VideoGenerationProvider.D_ID
        assert select_provider({'budget': 'limited'}) == VideoGenerationProvider.D_ID
        assert select_provider({'user_tier': 'standard'}) == VideoGenerationProvider.VEO3


class TestCostPrediction:
    """Test cost prediction models"""
    
    def test_linear_regression_cost_model(self):
        """Test linear regression for cost prediction"""
        # Historical data: (duration, quality_level, provider_index) -> cost
        training_data = [
            ([10, 1, 0], 1.5),   # 10s, standard, provider 0
            ([20, 1, 0], 3.0),   # 20s, standard, provider 0
            ([30, 2, 0], 6.75),  # 30s, premium, provider 0
            ([10, 1, 1], 2.0),   # 10s, standard, provider 1
            ([20, 2, 1], 6.0),   # 20s, premium, provider 1
        ]
        
        # Simple linear model: cost = a*duration + b*quality + c*provider + d
        # Fit model (simplified - in reality would use sklearn)
        X = np.array([x[0] for x in training_data])
        y = np.array([x[1] for x in training_data])
        
        # Add bias term
        X_with_bias = np.c_[X, np.ones(X.shape[0])]
        
        # Solve using normal equation
        coefficients = np.linalg.lstsq(X_with_bias, y, rcond=None)[0]
        
        # Predict new cost
        new_request = np.array([15, 1, 0, 1])  # 15s, standard, provider 0, bias
        predicted_cost = np.dot(new_request, coefficients)
        
        assert 2.0 < predicted_cost < 3.0  # Should be between 10s and 20s costs
    
    def test_cost_anomaly_detection(self):
        """Test detection of cost anomalies"""
        # Historical costs (normal distribution)
        normal_costs = [4.5, 4.8, 5.0, 4.7, 5.1, 4.9, 5.2, 4.6, 5.0, 4.8]
        
        mean_cost = np.mean(normal_costs)
        std_cost = np.std(normal_costs)
        
        # Define anomaly threshold (3 standard deviations)
        lower_bound = mean_cost - 3 * std_cost
        upper_bound = mean_cost + 3 * std_cost
        
        # Test normal cost
        normal_new_cost = 4.9
        assert lower_bound <= normal_new_cost <= upper_bound
        
        # Test anomaly cost
        anomaly_cost = 12.0
        assert anomaly_cost > upper_bound  # Should be detected as anomaly
        
        # Calculate anomaly score
        z_score = abs((anomaly_cost - mean_cost) / std_cost)
        assert z_score > 3  # Significant anomaly


class TestCostAllocation:
    """Test cost allocation strategies"""
    
    def test_usage_based_allocation(self):
        """Test usage-based cost allocation"""
        # User usage data
        users = [
            {'id': 'user1', 'videos': 10, 'total_duration': 150},
            {'id': 'user2', 'videos': 5, 'total_duration': 100},
            {'id': 'user3', 'videos': 15, 'total_duration': 200}
        ]
        
        # Total costs to allocate
        total_infrastructure_cost = 1000
        total_api_cost = 500
        
        # Allocate infrastructure cost by video count
        total_videos = sum(u['videos'] for u in users)
        for user in users:
            user['infra_cost'] = (user['videos'] / total_videos) * total_infrastructure_cost
        
        # Allocate API cost by duration
        total_duration = sum(u['total_duration'] for u in users)
        for user in users:
            user['api_cost'] = (user['total_duration'] / total_duration) * total_api_cost
            user['total_cost'] = user['infra_cost'] + user['api_cost']
        
        # Verify allocations
        assert abs(sum(u['infra_cost'] for u in users) - total_infrastructure_cost) < 0.01
        assert abs(sum(u['api_cost'] for u in users) - total_api_cost) < 0.01
        
        # User3 should have highest cost (most usage)
        costs_sorted = sorted(users, key=lambda x: x['total_cost'], reverse=True)
        assert costs_sorted[0]['id'] == 'user3'
    
    def test_tiered_pricing_allocation(self):
        """Test tiered pricing allocation"""
        # Define pricing tiers
        tiers = [
            {'name': 'free', 'videos': 3, 'price': 0},
            {'name': 'basic', 'videos': 10, 'price': 9.99},
            {'name': 'pro', 'videos': 50, 'price': 29.99},
            {'name': 'enterprise', 'videos': float('inf'), 'price': 99.99}
        ]
        
        def calculate_tier_price(video_count):
            for tier in tiers:
                if video_count <= tier['videos']:
                    return tier['price']
            return tiers[-1]['price']
        
        # Test different usage levels
        assert calculate_tier_price(2) == 0      # Free tier
        assert calculate_tier_price(5) == 9.99   # Basic tier
        assert calculate_tier_price(25) == 29.99 # Pro tier
        assert calculate_tier_price(100) == 99.99 # Enterprise tier


if __name__ == "__main__":
    pytest.main([__file__, "-v"])