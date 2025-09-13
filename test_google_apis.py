#!/usr/bin/env python3
"""
Test script to verify all Google APIs are working correctly
Run this before deployment to ensure all APIs are configured properly
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# Load environment variables
load_dotenv()

class GoogleAPITester:
    def __init__(self):
        self.results = {}
        self.api_key = os.getenv('GOOGLE_AI_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY') or self.api_key
        
    def test_gemini_api(self):
        """Test Gemini API (Nano Banana) for image generation"""
        print("\n🔍 Testing Gemini API (Nano Banana)...")
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": "Hello, can you respond to confirm the API is working?"
                    }]
                }]
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print("✅ Gemini API is working!")
                self.results['gemini'] = 'SUCCESS'
                
                # Test image-specific model if available
                self.test_gemini_vision()
            else:
                print(f"❌ Gemini API failed: {response.status_code}")
                print(f"Response: {response.text}")
                self.results['gemini'] = f'FAILED: {response.status_code}'
                
        except Exception as e:
            print(f"❌ Gemini API error: {str(e)}")
            self.results['gemini'] = f'ERROR: {str(e)}'
    
    def test_gemini_vision(self):
        """Test Gemini Vision capabilities"""
        print("\n🔍 Testing Gemini Vision (Image Analysis)...")
        
        try:
            # Test with a simple image analysis request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            
            # Create a simple test image (base64 encoded white pixel)
            test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "What is in this image?"},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": test_image
                            }
                        }
                    ]
                }]
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print("✅ Gemini Vision API is working!")
                self.results['gemini_vision'] = 'SUCCESS'
            else:
                print(f"⚠️ Gemini Vision API status: {response.status_code}")
                self.results['gemini_vision'] = f'Status: {response.status_code}'
                
        except Exception as e:
            print(f"⚠️ Gemini Vision test skipped: {str(e)}")
            self.results['gemini_vision'] = 'SKIPPED'
    
    def test_text_to_speech(self):
        """Test Google Cloud Text-to-Speech API"""
        print("\n🔍 Testing Google Text-to-Speech API...")
        
        try:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
            
            payload = {
                "input": {"text": "Hello, this is a test"},
                "voice": {
                    "languageCode": "en-US",
                    "name": "en-US-Wavenet-D"
                },
                "audioConfig": {"audioEncoding": "MP3"}
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print("✅ Text-to-Speech API is working!")
                self.results['tts'] = 'SUCCESS'
            else:
                print(f"❌ Text-to-Speech API failed: {response.status_code}")
                self.results['tts'] = f'FAILED: {response.status_code}'
                
        except Exception as e:
            print(f"⚠️ Text-to-Speech API error: {str(e)}")
            self.results['tts'] = f'ERROR: {str(e)}'
    
    def test_vision_api(self):
        """Test Google Cloud Vision API for face detection"""
        print("\n🔍 Testing Google Cloud Vision API...")
        
        try:
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
            
            # Test image (1x1 white pixel)
            test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            payload = {
                "requests": [{
                    "image": {"content": test_image},
                    "features": [{"type": "FACE_DETECTION", "maxResults": 1}]
                }]
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print("✅ Vision API is working!")
                self.results['vision'] = 'SUCCESS'
            else:
                print(f"❌ Vision API failed: {response.status_code}")
                self.results['vision'] = f'FAILED: {response.status_code}'
                
        except Exception as e:
            print(f"⚠️ Vision API error: {str(e)}")
            self.results['vision'] = f'ERROR: {str(e)}'
    
    def check_veo3_availability(self):
        """Check if Veo3 API is available"""
        print("\n🔍 Checking Veo3 API availability...")
        
        veo3_key = os.getenv('VEO3_API_KEY')
        if not veo3_key:
            print("⚠️ Veo3 API key not set (this is normal if you don't have access yet)")
            self.results['veo3'] = 'NOT_CONFIGURED'
            return
        
        # Veo3 is in limited preview, so we just check if key exists
        print("✅ Veo3 API key is configured (actual access depends on approval)")
        self.results['veo3'] = 'KEY_CONFIGURED'
    
    def print_summary(self):
        """Print summary of all API tests"""
        print("\n" + "="*50)
        print("📊 GOOGLE API TEST SUMMARY")
        print("="*50)
        
        for api, status in self.results.items():
            icon = "✅" if "SUCCESS" in status else "❌" if "FAILED" in status else "⚠️"
            print(f"{icon} {api.upper()}: {status}")
        
        # Check if ready for deployment
        critical_apis = ['gemini']
        all_critical_working = all(
            "SUCCESS" in self.results.get(api, "") 
            for api in critical_apis
        )
        
        print("\n" + "="*50)
        if all_critical_working:
            print("🎉 READY FOR DEPLOYMENT!")
            print("Your critical Google APIs are working correctly.")
            print("\nNext steps:")
            print("1. Update Streamlit Cloud secrets with these API keys")
            print("2. Deploy your app")
            print("3. Test the live features")
        else:
            print("⚠️ Some APIs need configuration")
            print("\nTo fix:")
            print("1. Check your API keys in .env file")
            print("2. Ensure APIs are enabled in Google Cloud Console")
            print("3. Check API quotas and billing")
    
    def save_test_report(self):
        """Save test results to a file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'api_keys_configured': {
                'GOOGLE_AI_API_KEY': bool(os.getenv('GOOGLE_AI_API_KEY')),
                'GEMINI_API_KEY': bool(os.getenv('GEMINI_API_KEY')),
                'VEO3_API_KEY': bool(os.getenv('VEO3_API_KEY')),
            }
        }
        
        with open('api_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Test report saved to: api_test_report.json")

def main():
    print("🚀 TalkingPhoto MVP - Google API Test Suite")
    print("="*50)
    
    tester = GoogleAPITester()
    
    if not tester.api_key:
        print("❌ ERROR: GOOGLE_AI_API_KEY not found in .env file!")
        print("\nPlease add your API key to .env file:")
        print("GOOGLE_AI_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Run all tests
    tester.test_gemini_api()
    tester.test_text_to_speech()
    tester.test_vision_api()
    tester.check_veo3_availability()
    
    # Print summary
    tester.print_summary()
    tester.save_test_report()

if __name__ == "__main__":
    main()