"""
TalkingPhoto AI MVP - AI Provider Mocks
Mock implementations for external AI services to enable reliable testing
"""

import json
import base64
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock
import numpy as np
from datetime import datetime, timezone


class MockNanoBananaAPI:
    """Mock implementation of Google Nano Banana (Gemini 2.5 Flash) API"""
    
    def __init__(self, api_key: str = "mock_key"):
        self.api_key = api_key
        self.call_count = 0
        self.last_request = None
        self.failure_rate = 0.0  # 0-1, probability of API failure
    
    def set_failure_rate(self, rate: float):
        """Set API failure rate for testing error handling"""
        self.failure_rate = rate
    
    def generate_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock content generation endpoint"""
        self.call_count += 1
        self.last_request = payload
        
        # Simulate failure based on failure rate
        if np.random.random() < self.failure_rate:
            return {
                'status_code': 500,
                'error': 'Service temporarily unavailable'
            }
        
        # Extract prompt and image data
        contents = payload.get('contents', [{}])[0]
        parts = contents.get('parts', [])
        
        prompt = ""
        has_image = False
        
        for part in parts:
            if 'text' in part:
                prompt = part['text']
            elif 'inline_data' in part:
                has_image = True
        
        # Generate mock response based on prompt
        if 'enhance' in prompt.lower():
            response_text = self._generate_enhancement_response(prompt, has_image)
        else:
            response_text = "I've processed your request successfully."
        
        return {
            'status_code': 200,
            'candidates': [{
                'content': {
                    'parts': [{
                        'text': response_text
                    }]
                },
                'finishReason': 'STOP'
            }],
            'usageMetadata': {
                'promptTokenCount': len(prompt.split()),
                'candidatesTokenCount': len(response_text.split()),
                'totalTokenCount': len(prompt.split()) + len(response_text.split())
            }
        }
    
    def _generate_enhancement_response(self, prompt: str, has_image: bool) -> str:
        """Generate mock enhancement response"""
        if not has_image:
            return "No image provided for enhancement."
        
        enhancements = [
            "Improved lighting and contrast for better visibility",
            "Enhanced facial features and expression clarity",
            "Optimized color balance and saturation",
            "Reduced noise and improved overall sharpness",
            "Better composition and framing for video use"
        ]
        
        return f"Image enhancement completed. Applied: {', '.join(enhancements[:3])}. The image is now optimized for professional video generation with improved clarity and natural appearance."


class MockVeo3API:
    """Mock implementation of Google Veo3 video generation API"""
    
    def __init__(self, api_key: str = "mock_veo3_key"):
        self.api_key = api_key
        self.jobs = {}  # job_id -> job_data
        self.job_counter = 0
        self.processing_time = 30  # seconds
        self.failure_rate = 0.0
    
    def set_processing_time(self, seconds: int):
        """Set mock processing time"""
        self.processing_time = seconds
    
    def set_failure_rate(self, rate: float):
        """Set API failure rate"""
        self.failure_rate = rate
    
    def submit_generation_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit video generation job"""
        if np.random.random() < self.failure_rate:
            return {
                'status_code': 400,
                'error': 'Invalid request parameters'
            }
        
        self.job_counter += 1
        job_id = f"veo3_job_{self.job_counter}_{int(time.time())}"
        
        # Store job data
        self.jobs[job_id] = {
            'job_id': job_id,
            'status': 'queued',
            'created_at': datetime.now(timezone.utc),
            'payload': payload,
            'progress': 0
        }
        
        return {
            'status_code': 200,
            'job_id': job_id,
            'status': 'queued',
            'estimated_completion_time': self.processing_time
        }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status and results"""
        if job_id not in self.jobs:
            return {
                'status_code': 404,
                'error': 'Job not found'
            }
        
        job = self.jobs[job_id]
        created_time = job['created_at']
        elapsed = (datetime.now(timezone.utc) - created_time).total_seconds()
        
        # Update job status based on elapsed time
        if elapsed < 5:
            job['status'] = 'processing'
            job['progress'] = min(20, int(elapsed * 4))
        elif elapsed < self.processing_time:
            job['status'] = 'processing'
            job['progress'] = min(95, int((elapsed / self.processing_time) * 100))
        else:
            job['status'] = 'completed'
            job['progress'] = 100
            job['output_url'] = f"https://mock-storage.com/videos/{job_id}.mp4"
            job['video_data'] = self._generate_mock_video_data(job_id)
        
        return {
            'status_code': 200,
            'job_id': job_id,
            'status': job['status'],
            'progress': job['progress'],
            'output_url': job.get('output_url'),
            'metadata': {
                'duration': 15,
                'resolution': '1920x1080',
                'format': 'mp4',
                'file_size': 5000000
            } if job['status'] == 'completed' else {}
        }
    
    def _generate_mock_video_data(self, job_id: str) -> bytes:
        """Generate mock video data"""
        # Create a mock MP4 file header + data
        mp4_header = b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom'
        mock_data = mp4_header + job_id.encode() + b'\x00' * 1000
        return mock_data


class MockRunwayAPI:
    """Mock implementation of Runway ML video generation API"""
    
    def __init__(self, api_key: str = "mock_runway_key"):
        self.api_key = api_key
        self.generations = {}
        self.generation_counter = 0
        self.processing_time = 45  # seconds
        self.failure_rate = 0.0
    
    def set_processing_time(self, seconds: int):
        """Set mock processing time"""
        self.processing_time = seconds
    
    def set_failure_rate(self, rate: float):
        """Set API failure rate"""
        self.failure_rate = rate
    
    def create_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create new video generation"""
        if np.random.random() < self.failure_rate:
            return {
                'status_code': 422,
                'error': 'Unprocessable entity'
            }
        
        self.generation_counter += 1
        gen_id = f"gen_{self.generation_counter}_{int(time.time())}"
        
        self.generations[gen_id] = {
            'id': gen_id,
            'status': 'PENDING',
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'payload': payload,
            'progress': 0
        }
        
        return {
            'status_code': 201,
            'id': gen_id,
            'status': 'PENDING',
            'createdAt': self.generations[gen_id]['createdAt']
        }
    
    def get_generation(self, generation_id: str) -> Dict[str, Any]:
        """Get generation status and results"""
        if generation_id not in self.generations:
            return {
                'status_code': 404,
                'error': 'Generation not found'
            }
        
        gen = self.generations[generation_id]
        created_time = datetime.fromisoformat(gen['createdAt'].replace('Z', '+00:00'))
        elapsed = (datetime.now(timezone.utc) - created_time).total_seconds()
        
        # Update status based on elapsed time
        if elapsed < 10:
            gen['status'] = 'RUNNING'
            gen['progress'] = min(30, int(elapsed * 3))
        elif elapsed < self.processing_time:
            gen['status'] = 'RUNNING'
            gen['progress'] = min(90, int((elapsed / self.processing_time) * 100))
        else:
            gen['status'] = 'SUCCEEDED'
            gen['progress'] = 100
            gen['output'] = [f"https://mock-runway.com/outputs/{generation_id}.mp4"]
            gen['video_data'] = self._generate_mock_video_data(generation_id)
        
        return {
            'status_code': 200,
            'id': generation_id,
            'status': gen['status'],
            'progress': gen['progress'],
            'output': gen.get('output', []),
            'metadata': {
                'duration': 15,
                'width': 1920,
                'height': 1080,
                'format': 'mp4'
            } if gen['status'] == 'SUCCEEDED' else {}
        }
    
    def _generate_mock_video_data(self, generation_id: str) -> bytes:
        """Generate mock video data"""
        mp4_header = b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom'
        mock_data = mp4_header + generation_id.encode() + b'\x00' * 1200
        return mock_data


class MockElevenLabsAPI:
    """Mock implementation of ElevenLabs TTS API"""
    
    def __init__(self, api_key: str = "mock_elevenlabs_key"):
        self.api_key = api_key
        self.call_count = 0
        self.failure_rate = 0.0
        
        # Mock voice catalog
        self.voices = {
            'EXAVITQu4vr4xnSDxMaL': {'name': 'Bella', 'gender': 'female'},
            'TxGEqnHWrfWFTfGW9XjX': {'name': 'Josh', 'gender': 'male'},
            'VR6AewLTigWG4xSOukaG': {'name': 'Arnold', 'gender': 'male'},
            'pNInz6obpgDQGcFmaJgB': {'name': 'Adam', 'gender': 'male'}
        }
    
    def set_failure_rate(self, rate: float):
        """Set API failure rate"""
        self.failure_rate = rate
    
    def get_voices(self) -> Dict[str, Any]:
        """Get available voices"""
        return {
            'status_code': 200,
            'voices': [
                {
                    'voice_id': voice_id,
                    'name': data['name'],
                    'category': 'premade',
                    'labels': {'gender': data['gender']},
                    'settings': {'stability': 0.5, 'similarity_boost': 0.5}
                }
                for voice_id, data in self.voices.items()
            ]
        }
    
    def text_to_speech(self, voice_id: str, text: str, settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert text to speech"""
        self.call_count += 1
        
        if np.random.random() < self.failure_rate:
            return {
                'status_code': 400,
                'error': 'Voice not found or invalid parameters'
            }
        
        if voice_id not in self.voices:
            return {
                'status_code': 404,
                'error': 'Voice not found'
            }
        
        # Generate mock MP3 audio data
        audio_duration = max(2, len(text.split()) * 0.6)  # Rough estimate
        mock_mp3_data = self._generate_mock_audio_data(text, audio_duration)
        
        return {
            'status_code': 200,
            'audio_data': mock_mp3_data,
            'content_type': 'audio/mpeg',
            'duration': audio_duration,
            'voice_used': self.voices[voice_id]['name']
        }
    
    def _generate_mock_audio_data(self, text: str, duration: float) -> bytes:
        """Generate mock audio data"""
        # Mock MP3 header + data
        mp3_header = b'\xff\xfb\x90\x00'  # MP3 frame header
        text_bytes = text.encode('utf-8')[:100]  # Truncate for mock
        padding = b'\x00' * int(duration * 1000)  # Rough size approximation
        return mp3_header + text_bytes + padding


class MockAzureSpeechAPI:
    """Mock implementation of Azure Speech Services"""
    
    def __init__(self, subscription_key: str = "mock_azure_key", region: str = "eastus"):
        self.subscription_key = subscription_key
        self.region = region
        self.call_count = 0
        self.failure_rate = 0.0
        
        # Mock voice catalog
        self.voices = {
            'en-US-JennyNeural': {'name': 'Jenny', 'gender': 'Female', 'locale': 'en-US'},
            'en-US-GuyNeural': {'name': 'Guy', 'gender': 'Male', 'locale': 'en-US'},
            'en-GB-SoniaNeural': {'name': 'Sonia', 'gender': 'Female', 'locale': 'en-GB'},
            'hi-IN-SwaraNeural': {'name': 'Swara', 'gender': 'Female', 'locale': 'hi-IN'}
        }
    
    def set_failure_rate(self, rate: float):
        """Set API failure rate"""
        self.failure_rate = rate
    
    def get_voices_list(self) -> Dict[str, Any]:
        """Get available voices"""
        return {
            'status_code': 200,
            'voices': [
                {
                    'Name': voice_id,
                    'DisplayName': data['name'],
                    'LocalName': data['name'],
                    'ShortName': voice_id,
                    'Gender': data['gender'],
                    'Locale': data['locale'],
                    'SampleRateHertz': '24000',
                    'VoiceType': 'Neural'
                }
                for voice_id, data in self.voices.items()
            ]
        }
    
    def synthesize_speech(self, ssml: str, voice_name: str = None) -> Dict[str, Any]:
        """Synthesize speech from SSML"""
        self.call_count += 1
        
        if np.random.random() < self.failure_rate:
            return {
                'status_code': 400,
                'error': 'Speech synthesis failed'
            }
        
        # Extract text from SSML
        import re
        text_match = re.search(r'<speak[^>]*>(.*?)</speak>', ssml, re.DOTALL)
        text = text_match.group(1) if text_match else ssml
        
        # Remove XML tags
        text = re.sub(r'<[^>]+>', '', text).strip()
        
        # Generate mock WAV audio data
        audio_duration = max(1, len(text.split()) * 0.5)
        mock_wav_data = self._generate_mock_wav_data(text, audio_duration)
        
        return {
            'status_code': 200,
            'audio_data': mock_wav_data,
            'content_type': 'audio/wav',
            'duration': audio_duration,
            'voice_used': voice_name or 'en-US-JennyNeural'
        }
    
    def _generate_mock_wav_data(self, text: str, duration: float) -> bytes:
        """Generate mock WAV audio data"""
        # WAV header for 16-bit PCM, 16kHz mono
        sample_rate = 16000
        num_samples = int(duration * sample_rate)
        
        wav_header = b'RIFF'
        wav_header += (36 + num_samples * 2).to_bytes(4, 'little')  # File size
        wav_header += b'WAVE'
        wav_header += b'fmt '
        wav_header += (16).to_bytes(4, 'little')  # Subchunk1 size
        wav_header += (1).to_bytes(2, 'little')   # Audio format (PCM)
        wav_header += (1).to_bytes(2, 'little')   # Num channels
        wav_header += sample_rate.to_bytes(4, 'little')  # Sample rate
        wav_header += (sample_rate * 2).to_bytes(4, 'little')  # Byte rate
        wav_header += (2).to_bytes(2, 'little')   # Block align
        wav_header += (16).to_bytes(2, 'little')  # Bits per sample
        wav_header += b'data'
        wav_header += (num_samples * 2).to_bytes(4, 'little')  # Data size
        
        # Generate mock audio samples (simple sine wave based on text)
        import struct
        audio_data = b''
        frequency = 440 + (hash(text) % 200)  # Vary frequency based on text
        
        for i in range(num_samples):
            sample = int(16000 * np.sin(2 * np.pi * frequency * i / sample_rate))
            audio_data += struct.pack('<h', sample)
        
        return wav_header + audio_data


class MockStripeAPI:
    """Mock implementation of Stripe payment processing"""
    
    def __init__(self, api_key: str = "mock_stripe_key"):
        self.api_key = api_key
        self.customers = {}
        self.payment_intents = {}
        self.subscriptions = {}
        self.failure_rate = 0.0
    
    def set_failure_rate(self, rate: float):
        """Set payment failure rate"""
        self.failure_rate = rate
    
    def create_customer(self, email: str, name: str = None) -> Dict[str, Any]:
        """Create Stripe customer"""
        if np.random.random() < self.failure_rate:
            return {
                'status_code': 400,
                'error': 'Invalid email address'
            }
        
        customer_id = f"cus_mock_{int(time.time())}"
        self.customers[customer_id] = {
            'id': customer_id,
            'email': email,
            'name': name,
            'created': int(time.time())
        }
        
        return {
            'status_code': 200,
            'customer': self.customers[customer_id]
        }
    
    def create_payment_intent(self, amount: int, currency: str, customer_id: str = None) -> Dict[str, Any]:
        """Create payment intent"""
        if np.random.random() < self.failure_rate:
            return {
                'status_code': 400,
                'error': 'Invalid amount'
            }
        
        intent_id = f"pi_mock_{int(time.time())}"
        self.payment_intents[intent_id] = {
            'id': intent_id,
            'amount': amount,
            'currency': currency,
            'customer': customer_id,
            'status': 'requires_payment_method',
            'client_secret': f"{intent_id}_secret_mock"
        }
        
        return {
            'status_code': 200,
            'payment_intent': self.payment_intents[intent_id]
        }
    
    def confirm_payment_intent(self, intent_id: str, payment_method: str = "pm_mock_card") -> Dict[str, Any]:
        """Confirm payment intent"""
        if intent_id not in self.payment_intents:
            return {
                'status_code': 404,
                'error': 'Payment intent not found'
            }
        
        if np.random.random() < self.failure_rate:
            self.payment_intents[intent_id]['status'] = 'requires_payment_method'
            return {
                'status_code': 402,
                'error': 'Your card was declined'
            }
        
        self.payment_intents[intent_id]['status'] = 'succeeded'
        self.payment_intents[intent_id]['payment_method'] = payment_method
        
        return {
            'status_code': 200,
            'payment_intent': self.payment_intents[intent_id]
        }


# Factory function to create mock services
def create_ai_service_mocks(failure_rates: Dict[str, float] = None) -> Dict[str, Any]:
    """Create a complete set of AI service mocks"""
    if failure_rates is None:
        failure_rates = {}
    
    mocks = {
        'nano_banana': MockNanoBananaAPI(),
        'veo3': MockVeo3API(),
        'runway': MockRunwayAPI(),
        'elevenlabs': MockElevenLabsAPI(),
        'azure_speech': MockAzureSpeechAPI(),
        'stripe': MockStripeAPI()
    }
    
    # Set failure rates
    for service_name, rate in failure_rates.items():
        if service_name in mocks:
            mocks[service_name].set_failure_rate(rate)
    
    return mocks