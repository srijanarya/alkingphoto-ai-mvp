"""
TalkingPhoto AI MVP - Credits System

Manages user credits, pricing, and payment logic.
Pure Python implementation for the freemium model.
"""

from typing import Dict, List, Optional
from enum import Enum
import time


class CreditTier(Enum):
    """Available credit tiers and pricing"""
    FREE = ("free", 1, 0, "Free Trial")
    BASIC = ("basic", 5, 99, "Basic Pack")
    PRO = ("pro", 15, 249, "Pro Pack")  
    PREMIUM = ("premium", 30, 449, "Premium Pack")


class CreditManager:
    """Manages credit operations and pricing logic"""
    
    # Pricing configuration (in paise for Indian market)
    PRICING_CONFIG = {
        CreditTier.FREE: {"credits": 1, "price": 0, "description": "1 free video"},
        CreditTier.BASIC: {"credits": 5, "price": 99, "description": "5 videos for ₹99"},
        CreditTier.PRO: {"credits": 15, "price": 249, "description": "15 videos for ₹249 (Best Value!)"},
        CreditTier.PREMIUM: {"credits": 30, "price": 449, "description": "30 videos for ₹449 (Most Popular!)"}
    }
    
    @staticmethod
    def get_pricing_info() -> Dict[str, Dict]:
        """Get all pricing tier information"""
        pricing = {}
        
        for tier in CreditTier:
            config = CreditManager.PRICING_CONFIG[tier]
            price_per_video = config["price"] / config["credits"] if config["credits"] > 0 else 0
            
            pricing[tier.value[0]] = {
                "tier_name": tier.value[3],
                "credits": config["credits"],
                "price_rupees": config["price"],
                "price_per_video": round(price_per_video, 2),
                "description": config["description"],
                "savings": CreditManager._calculate_savings(tier)
            }
        
        return pricing
    
    @staticmethod
    def _calculate_savings(tier: CreditTier) -> str:
        """Calculate savings compared to basic tier"""
        if tier == CreditTier.FREE or tier == CreditTier.BASIC:
            return ""
        
        basic_config = CreditManager.PRICING_CONFIG[CreditTier.BASIC]
        tier_config = CreditManager.PRICING_CONFIG[tier]
        
        basic_per_video = basic_config["price"] / basic_config["credits"]
        tier_per_video = tier_config["price"] / tier_config["credits"]
        
        savings_percent = ((basic_per_video - tier_per_video) / basic_per_video) * 100
        savings_amount = (basic_per_video - tier_per_video) * tier_config["credits"]
        
        return f"Save ₹{savings_amount:.0f} ({savings_percent:.0f}% off)"
    
    @staticmethod
    def get_recommended_tier(expected_usage: int) -> CreditTier:
        """
        Recommend best tier based on expected usage
        
        Args:
            expected_usage: Expected number of videos per month
            
        Returns:
            CreditTier: Recommended tier
        """
        if expected_usage <= 1:
            return CreditTier.FREE
        elif expected_usage <= 5:
            return CreditTier.BASIC
        elif expected_usage <= 15:
            return CreditTier.PRO
        else:
            return CreditTier.PREMIUM
    
    @staticmethod
    def calculate_cost_savings(tier: CreditTier, compared_to: CreditTier = CreditTier.BASIC) -> Dict[str, float]:
        """
        Calculate cost savings between tiers
        
        Args:
            tier: Target tier
            compared_to: Comparison tier
            
        Returns:
            Dict: Savings information
        """
        tier_config = CreditManager.PRICING_CONFIG[tier]
        comparison_config = CreditManager.PRICING_CONFIG[compared_to]
        
        tier_per_video = tier_config["price"] / tier_config["credits"]
        comparison_per_video = comparison_config["price"] / comparison_config["credits"]
        
        savings_per_video = comparison_per_video - tier_per_video
        total_savings = savings_per_video * tier_config["credits"]
        percentage_savings = (savings_per_video / comparison_per_video) * 100 if comparison_per_video > 0 else 0
        
        return {
            "savings_per_video": round(savings_per_video, 2),
            "total_savings": round(total_savings, 2),
            "percentage_savings": round(percentage_savings, 1)
        }


class TransactionManager:
    """Manages credit transactions and history"""
    
    @staticmethod
    def create_purchase_intent(tier: CreditTier, user_id: str) -> Dict[str, any]:
        """
        Create a purchase intent for credit purchase
        
        Args:
            tier: Selected credit tier
            user_id: User identifier
            
        Returns:
            Dict: Purchase intent data
        """
        config = CreditManager.PRICING_CONFIG[tier]
        
        return {
            "transaction_id": f"txn_{int(time.time())}_{user_id}",
            "user_id": user_id,
            "tier": tier.value[0],
            "credits": config["credits"],
            "amount": config["price"],
            "currency": "INR",
            "description": config["description"],
            "created_at": time.time(),
            "status": "pending"
        }
    
    @staticmethod
    def get_pricing_display() -> List[Dict[str, any]]:
        """
        Get pricing information formatted for UI display
        
        Returns:
            List[Dict]: Pricing cards data
        """
        pricing_cards = []
        
        for tier in [CreditTier.FREE, CreditTier.BASIC, CreditTier.PRO, CreditTier.PREMIUM]:
            config = CreditManager.PRICING_CONFIG[tier]
            
            card = {
                "tier_id": tier.value[0],
                "title": tier.value[3],
                "credits": config["credits"],
                "price": config["price"],
                "description": config["description"],
                "per_video_cost": round(config["price"] / config["credits"], 2) if config["credits"] > 0 else 0,
                "is_free": tier == CreditTier.FREE,
                "is_popular": tier == CreditTier.PRO,
                "is_best_value": tier == CreditTier.PREMIUM,
                "features": TransactionManager._get_tier_features(tier)
            }
            
            # Add savings information
            if tier != CreditTier.FREE and tier != CreditTier.BASIC:
                savings = CreditManager.calculate_cost_savings(tier)
                card["savings"] = f"Save ₹{savings['total_savings']:.0f}"
                card["savings_percentage"] = f"{savings['percentage_savings']:.0f}% off"
            
            pricing_cards.append(card)
        
        return pricing_cards
    
    @staticmethod
    def _get_tier_features(tier: CreditTier) -> List[str]:
        """Get features for each tier"""
        base_features = ["High-quality video generation", "Multiple languages", "Email support"]
        
        if tier == CreditTier.FREE:
            return ["1 free video", "Watermarked output"] + base_features[:1]
        elif tier == CreditTier.BASIC:
            return [f"{CreditManager.PRICING_CONFIG[tier]['credits']} videos", "No watermark"] + base_features
        elif tier == CreditTier.PRO:
            return [f"{CreditManager.PRICING_CONFIG[tier]['credits']} videos", "No watermark", "Priority processing"] + base_features
        else:  # PREMIUM
            return [f"{CreditManager.PRICING_CONFIG[tier]['credits']} videos", "No watermark", "Priority processing", "Advanced customization"] + base_features