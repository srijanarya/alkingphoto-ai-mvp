"""
TalkingPhoto AI MVP - Credits System Unit Tests
Comprehensive tests for credit management, pricing, and transaction logic
"""

import pytest
import time
from unittest.mock import Mock, patch
from enum import Enum

from core.credits import CreditTier, CreditManager, TransactionManager


class TestCreditTier:
    """Test credit tier enumeration and values"""
    
    def test_credit_tier_values(self):
        """Test that credit tiers have correct values"""
        assert CreditTier.FREE.value == ("free", 1, 0, "Free Trial")
        assert CreditTier.BASIC.value == ("basic", 5, 99, "Basic Pack")
        assert CreditTier.PRO.value == ("pro", 15, 249, "Pro Pack")
        assert CreditTier.PREMIUM.value == ("premium", 30, 449, "Premium Pack")
    
    def test_credit_tier_accessibility(self):
        """Test that all credit tiers are accessible"""
        tiers = list(CreditTier)
        assert len(tiers) == 4
        
        tier_names = [tier.value[0] for tier in tiers]
        assert 'free' in tier_names
        assert 'basic' in tier_names
        assert 'pro' in tier_names
        assert 'premium' in tier_names


class TestCreditManager:
    """Test credit management logic and pricing calculations"""
    
    def test_pricing_config_consistency(self):
        """Test that pricing configuration is consistent with enum values"""
        for tier in CreditTier:
            config = CreditManager.PRICING_CONFIG[tier]
            
            # Check that config has required keys
            assert 'credits' in config
            assert 'price' in config
            assert 'description' in config
            
            # Check that values match enum
            assert config['credits'] == tier.value[1]
            assert config['price'] == tier.value[2]
    
    def test_get_pricing_info_structure(self):
        """Test that pricing info returns correct structure"""
        pricing = CreditManager.get_pricing_info()
        
        # Should have all tiers
        assert len(pricing) == 4
        assert 'free' in pricing
        assert 'basic' in pricing
        assert 'pro' in pricing
        assert 'premium' in pricing
        
        # Check structure of each tier
        for tier_id, tier_info in pricing.items():
            assert 'tier_name' in tier_info
            assert 'credits' in tier_info
            assert 'price_rupees' in tier_info
            assert 'price_per_video' in tier_info
            assert 'description' in tier_info
            assert 'savings' in tier_info
    
    def test_price_per_video_calculation(self):
        """Test price per video calculation accuracy"""
        pricing = CreditManager.get_pricing_info()
        
        # Free tier should have 0 price per video
        assert pricing['free']['price_per_video'] == 0
        
        # Basic tier: 99 / 5 = 19.8
        assert pricing['basic']['price_per_video'] == 19.8
        
        # Pro tier: 249 / 15 = 16.6
        assert pricing['pro']['price_per_video'] == 16.6
        
        # Premium tier: 449 / 30 = 14.97 (rounded to 14.97)
        assert abs(pricing['premium']['price_per_video'] - 14.97) < 0.01
    
    def test_savings_calculation_basic_tier(self):
        """Test that basic tier has no savings displayed"""
        savings = CreditManager._calculate_savings(CreditTier.BASIC)
        assert savings == ""
    
    def test_savings_calculation_free_tier(self):
        """Test that free tier has no savings displayed"""
        savings = CreditManager._calculate_savings(CreditTier.FREE)
        assert savings == ""
    
    def test_savings_calculation_pro_tier(self):
        """Test savings calculation for pro tier"""
        savings = CreditManager._calculate_savings(CreditTier.PRO)
        
        # Basic: 19.8 per video, Pro: 16.6 per video
        # Savings per video: 3.2, Total for 15 videos: 48
        # Percentage: (3.2/19.8) * 100 = 16.16%
        assert "Save ₹48" in savings
        assert "16% off" in savings
    
    def test_savings_calculation_premium_tier(self):
        """Test savings calculation for premium tier"""
        savings = CreditManager._calculate_savings(CreditTier.PREMIUM)
        
        # Basic: 19.8 per video, Premium: 14.97 per video
        # Savings per video: 4.83, Total for 30 videos: 144.9
        # Percentage: (4.83/19.8) * 100 = 24.39%
        assert "Save ₹145" in savings or "Save ₹144" in savings
        assert "24% off" in savings
    
    def test_get_recommended_tier_logic(self):
        """Test tier recommendation logic based on usage"""
        # Low usage - free tier
        assert CreditManager.get_recommended_tier(1) == CreditTier.FREE
        assert CreditManager.get_recommended_tier(0) == CreditTier.FREE
        
        # Basic usage - basic tier
        assert CreditManager.get_recommended_tier(3) == CreditTier.BASIC
        assert CreditManager.get_recommended_tier(5) == CreditTier.BASIC
        
        # Pro usage - pro tier
        assert CreditManager.get_recommended_tier(10) == CreditTier.PRO
        assert CreditManager.get_recommended_tier(15) == CreditTier.PRO
        
        # Heavy usage - premium tier
        assert CreditManager.get_recommended_tier(20) == CreditTier.PREMIUM
        assert CreditManager.get_recommended_tier(50) == CreditTier.PREMIUM
    
    def test_calculate_cost_savings_pro_vs_basic(self):
        """Test cost savings calculation between pro and basic tiers"""
        savings = CreditManager.calculate_cost_savings(CreditTier.PRO, CreditTier.BASIC)
        
        # Basic: 19.8, Pro: 16.6, Difference: 3.2 per video
        assert abs(savings['savings_per_video'] - 3.2) < 0.1
        assert abs(savings['total_savings'] - 48.0) < 1.0
        assert abs(savings['percentage_savings'] - 16.2) < 0.5
    
    def test_calculate_cost_savings_premium_vs_basic(self):
        """Test cost savings calculation between premium and basic tiers"""
        savings = CreditManager.calculate_cost_savings(CreditTier.PREMIUM, CreditTier.BASIC)
        
        # Should show significant savings for premium
        assert savings['savings_per_video'] > 4.0
        assert savings['total_savings'] > 140.0
        assert savings['percentage_savings'] > 20.0
    
    def test_calculate_cost_savings_same_tier(self):
        """Test cost savings calculation for same tier (should be zero)"""
        savings = CreditManager.calculate_cost_savings(CreditTier.BASIC, CreditTier.BASIC)
        
        assert savings['savings_per_video'] == 0.0
        assert savings['total_savings'] == 0.0
        assert savings['percentage_savings'] == 0.0
    
    def test_calculate_cost_savings_free_vs_basic(self):
        """Test cost savings when comparing free to basic (should handle edge case)"""
        savings = CreditManager.calculate_cost_savings(CreditTier.FREE, CreditTier.BASIC)
        
        # Free tier should show negative savings (more expensive per video conceptually)
        assert savings['savings_per_video'] < 0
        assert savings['percentage_savings'] < 0


class TestTransactionManager:
    """Test transaction management and purchase logic"""
    
    def test_create_purchase_intent_structure(self):
        """Test purchase intent creation structure"""
        intent = TransactionManager.create_purchase_intent(CreditTier.PRO, 'test_user_123')
        
        # Check required fields
        assert 'transaction_id' in intent
        assert 'user_id' in intent
        assert 'tier' in intent
        assert 'credits' in intent
        assert 'amount' in intent
        assert 'currency' in intent
        assert 'description' in intent
        assert 'created_at' in intent
        assert 'status' in intent
        
        # Check values
        assert intent['user_id'] == 'test_user_123'
        assert intent['tier'] == 'pro'
        assert intent['credits'] == 15
        assert intent['amount'] == 249
        assert intent['currency'] == 'INR'
        assert intent['status'] == 'pending'
    
    def test_create_purchase_intent_transaction_id_uniqueness(self):
        """Test that transaction IDs are unique"""
        intent1 = TransactionManager.create_purchase_intent(CreditTier.BASIC, 'user1')
        time.sleep(0.01)  # Small delay to ensure different timestamp
        intent2 = TransactionManager.create_purchase_intent(CreditTier.BASIC, 'user2')
        
        assert intent1['transaction_id'] != intent2['transaction_id']
        assert 'user1' in intent1['transaction_id']
        assert 'user2' in intent2['transaction_id']
    
    def test_create_purchase_intent_different_tiers(self):
        """Test purchase intent creation for different tiers"""
        # Free tier
        free_intent = TransactionManager.create_purchase_intent(CreditTier.FREE, 'user')
        assert free_intent['credits'] == 1
        assert free_intent['amount'] == 0
        
        # Basic tier
        basic_intent = TransactionManager.create_purchase_intent(CreditTier.BASIC, 'user')
        assert basic_intent['credits'] == 5
        assert basic_intent['amount'] == 99
        
        # Premium tier
        premium_intent = TransactionManager.create_purchase_intent(CreditTier.PREMIUM, 'user')
        assert premium_intent['credits'] == 30
        assert premium_intent['amount'] == 449
    
    def test_get_pricing_display_structure(self):
        """Test pricing display format for UI"""
        pricing_cards = TransactionManager.get_pricing_display()
        
        # Should have all 4 tiers
        assert len(pricing_cards) == 4
        
        # Check structure of each card
        for card in pricing_cards:
            assert 'tier_id' in card
            assert 'title' in card
            assert 'credits' in card
            assert 'price' in card
            assert 'description' in card
            assert 'per_video_cost' in card
            assert 'is_free' in card
            assert 'is_popular' in card
            assert 'is_best_value' in card
            assert 'features' in card
    
    def test_get_pricing_display_flags(self):
        """Test pricing display flags are set correctly"""
        pricing_cards = TransactionManager.get_pricing_display()
        
        # Find specific cards
        free_card = next(card for card in pricing_cards if card['tier_id'] == 'free')
        basic_card = next(card for card in pricing_cards if card['tier_id'] == 'basic')
        pro_card = next(card for card in pricing_cards if card['tier_id'] == 'pro')
        premium_card = next(card for card in pricing_cards if card['tier_id'] == 'premium')
        
        # Check flags
        assert free_card['is_free'] is True
        assert basic_card['is_free'] is False
        assert pro_card['is_popular'] is True
        assert premium_card['is_best_value'] is True
        
        # Only one card should be popular/best_value
        popular_count = sum(1 for card in pricing_cards if card['is_popular'])
        best_value_count = sum(1 for card in pricing_cards if card['is_best_value'])
        assert popular_count == 1
        assert best_value_count == 1
    
    def test_get_pricing_display_savings_info(self):
        """Test that savings information is included for higher tiers"""
        pricing_cards = TransactionManager.get_pricing_display()
        
        # Find cards
        free_card = next(card for card in pricing_cards if card['tier_id'] == 'free')
        basic_card = next(card for card in pricing_cards if card['tier_id'] == 'basic')
        pro_card = next(card for card in pricing_cards if card['tier_id'] == 'pro')
        premium_card = next(card for card in pricing_cards if card['tier_id'] == 'premium')
        
        # Free and basic shouldn't have savings
        assert 'savings' not in free_card
        assert 'savings' not in basic_card
        
        # Pro and premium should have savings
        assert 'savings' in pro_card
        assert 'savings_percentage' in pro_card
        assert 'savings' in premium_card
        assert 'savings_percentage' in premium_card
        
        # Check savings format
        assert pro_card['savings'].startswith('Save ₹')
        assert pro_card['savings_percentage'].endswith('% off')
    
    def test_get_tier_features_content(self):
        """Test tier features content"""
        # Free tier features
        free_features = TransactionManager._get_tier_features(CreditTier.FREE)
        assert '1 free video' in free_features
        assert 'Watermarked output' in free_features
        assert len(free_features) >= 2
        
        # Basic tier features
        basic_features = TransactionManager._get_tier_features(CreditTier.BASIC)
        assert '5 videos' in basic_features
        assert 'No watermark' in basic_features
        assert 'High-quality video generation' in basic_features
        
        # Pro tier features
        pro_features = TransactionManager._get_tier_features(CreditTier.PRO)
        assert '15 videos' in pro_features
        assert 'Priority processing' in pro_features
        assert 'No watermark' in pro_features
        
        # Premium tier features
        premium_features = TransactionManager._get_tier_features(CreditTier.PREMIUM)
        assert '30 videos' in premium_features
        assert 'Advanced customization' in premium_features
        assert 'Priority processing' in premium_features
    
    def test_get_tier_features_progressive_enhancement(self):
        """Test that higher tiers include more features"""
        free_features = TransactionManager._get_tier_features(CreditTier.FREE)
        basic_features = TransactionManager._get_tier_features(CreditTier.BASIC)
        pro_features = TransactionManager._get_tier_features(CreditTier.PRO)
        premium_features = TransactionManager._get_tier_features(CreditTier.PREMIUM)
        
        # Higher tiers should have more features
        assert len(free_features) < len(basic_features)
        assert len(basic_features) <= len(pro_features)
        assert len(pro_features) <= len(premium_features)
        
        # Check that premium has the most comprehensive features
        assert len(premium_features) >= 6


@pytest.mark.integration
class TestCreditsIntegration:
    """Integration tests for credits system components"""
    
    def test_end_to_end_pricing_workflow(self):
        """Test complete pricing workflow from recommendation to purchase intent"""
        # Scenario: User wants 12 videos per month
        expected_usage = 12
        
        # Get recommendation
        recommended_tier = CreditManager.get_recommended_tier(expected_usage)
        assert recommended_tier == CreditTier.PRO  # 15 videos for 12 needed
        
        # Get pricing info
        pricing = CreditManager.get_pricing_info()
        tier_info = pricing[recommended_tier.value[0]]
        
        # Verify recommendation makes sense
        assert tier_info['credits'] >= expected_usage
        assert tier_info['price_per_video'] < pricing['basic']['price_per_video']
        
        # Create purchase intent
        intent = TransactionManager.create_purchase_intent(recommended_tier, 'test_user')
        
        # Verify intent matches recommendation
        assert intent['tier'] == recommended_tier.value[0]
        assert intent['credits'] == tier_info['credits']
        assert intent['amount'] == tier_info['price_rupees']
    
    def test_cost_optimization_analysis(self):
        """Test cost optimization across all tiers"""
        pricing = CreditManager.get_pricing_info()
        
        # Calculate cost efficiency (credits per rupee)
        efficiency = {}
        for tier_id, info in pricing.items():
            if info['price_rupees'] > 0:
                efficiency[tier_id] = info['credits'] / info['price_rupees']
        
        # Premium should be most cost-efficient
        assert efficiency['premium'] > efficiency['pro']
        assert efficiency['pro'] > efficiency['basic']
        
        # Verify the cost optimization message
        pro_savings = CreditManager.calculate_cost_savings(CreditTier.PRO)
        premium_savings = CreditManager.calculate_cost_savings(CreditTier.PREMIUM)
        
        assert premium_savings['percentage_savings'] > pro_savings['percentage_savings']
    
    def test_ui_display_completeness(self):
        """Test that UI display has all necessary information"""
        display_data = TransactionManager.get_pricing_display()
        
        # Verify we can build a complete UI from this data
        for card in display_data:
            # Each card should have display title
            assert len(card['title']) > 0
            
            # Should have pricing information
            if not card['is_free']:
                assert card['price'] > 0
                assert card['per_video_cost'] > 0
            
            # Should have feature list
            assert len(card['features']) > 0
            
            # Should have clear description
            assert len(card['description']) > 0
            
            # Savings info should be present for non-free, non-basic tiers
            if card['tier_id'] not in ['free', 'basic']:
                assert 'savings' in card
                assert 'savings_percentage' in card
    
    def test_transaction_id_format_and_parsing(self):
        """Test transaction ID format for external payment integration"""
        intent = TransactionManager.create_purchase_intent(CreditTier.PRO, 'user_abc123')
        txn_id = intent['transaction_id']
        
        # Should start with 'txn_'
        assert txn_id.startswith('txn_')
        
        # Should contain timestamp and user ID
        parts = txn_id.split('_')
        assert len(parts) >= 3
        assert parts[0] == 'txn'
        assert parts[2] == 'user'
        assert parts[3] == 'abc123'
        
        # Timestamp should be reasonable (within last minute)
        timestamp = int(parts[1])
        current_time = int(time.time())
        assert abs(current_time - timestamp) < 60  # Within 1 minute