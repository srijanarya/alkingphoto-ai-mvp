#!/usr/bin/env python3
"""
Verify which TalkingPhoto features are enabled based on API configuration
"""

import os
from dotenv import load_dotenv
from config import Config

# Load environment variables
load_dotenv()

def main():
    print("🎬 TalkingPhoto MVP - Feature Status")
    print("="*50)
    
    # Check API Keys
    print("\n📌 API Keys Status:")
    api_keys = {
        'Google AI': Config.GOOGLE_AI_API_KEY,
        'Gemini/Nano Banana': Config.GEMINI_API_KEY,
        'Veo3': Config.VEO3_API_KEY,
        'Runway': Config.RUNWAY_API_KEY,
        'OpenAI': Config.OPENAI_API_KEY,
        'Stripe': Config.STRIPE_SECRET_KEY,
    }
    
    for name, key in api_keys.items():
        status = "✅ Configured" if key else "❌ Not Set"
        print(f"  {name}: {status}")
    
    # Check Google Cloud APIs
    print("\n🌐 Google Cloud APIs:")
    google_apis = {
        'Vision API (Face Detection)': Config.GOOGLE_VISION_ENABLED,
        'Text-to-Speech': Config.GOOGLE_TTS_ENABLED,
        'Veo3 (Video Generation)': Config.VEO3_ENABLED,
    }
    
    for name, enabled in google_apis.items():
        status = "✅ Enabled" if enabled else "⚠️ Disabled"
        print(f"  {name}: {status}")
    
    # Check Features
    print("\n🚀 Available Features:")
    for feature, enabled in Config.FEATURES_ENABLED.items():
        status = "✅ Active" if enabled else "❌ Inactive"
        feature_name = feature.replace('_', ' ').title()
        print(f"  {feature_name}: {status}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not Config.GOOGLE_AI_API_KEY:
        print("  1. Add GOOGLE_AI_API_KEY to enable AI features")
    
    if not Config.VEO3_API_KEY:
        print("  2. Veo3 API key not set (normal if you don't have access yet)")
        print("     - Your app will use export instructions instead")
    
    if not Config.STRIPE_SECRET_KEY:
        print("  3. Add Stripe keys to enable payment processing")
    
    if all([Config.GOOGLE_AI_API_KEY, Config.STRIPE_SECRET_KEY]):
        print("  🎉 Your core features are ready to use!")
        print("  Deploy to Streamlit Cloud and start generating videos!")
    
    # Show active workflow
    print("\n📱 Current Workflow:")
    if Config.FEATURES_ENABLED['photo_enhancement']:
        print("  1. ✅ User uploads photo → AI enhancement")
    else:
        print("  1. ⚠️ User uploads photo → Basic processing")
    
    if Config.FEATURES_ENABLED['text_to_speech']:
        print("  2. ✅ User enters script → AI voice generation")
    else:
        print("  2. ⚠️ User enters script → Text only")
    
    if Config.FEATURES_ENABLED['video_generation']:
        print("  3. ✅ Generate talking video with Veo3")
    elif Config.FEATURES_ENABLED['ai_export_guidance']:
        print("  3. ⚠️ Provide AI-powered export instructions")
    else:
        print("  3. ⚠️ Provide basic export instructions")

if __name__ == "__main__":
    main()