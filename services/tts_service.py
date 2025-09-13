"""
TalkingPhoto AI MVP - Text-to-Speech (TTS) Service
Multi-provider TTS integration with voice options and emotion control
"""

import requests
import base64
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import io
import wave
import struct
from flask import current_app
import azure.cognitiveservices.speech as speechsdk
import structlog
from enum import Enum

logger = structlog.get_logger()


class TTSProvider(Enum):
    """TTS service providers"""
    AZURE = 'azure'
    ELEVENLABS = 'elevenlabs'
    GOOGLE = 'google'
    AWS_POLLY = 'aws_polly'
    OPENAI = 'openai'


class VoiceGender(Enum):
    """Voice gender options"""
    MALE = 'male'
    FEMALE = 'female'
    NEUTRAL = 'neutral'


class VoiceEmotion(Enum):
    """Voice emotion styles"""
    NEUTRAL = 'neutral'
    CHEERFUL = 'cheerful'
    SAD = 'sad'
    ANGRY = 'angry'
    EXCITED = 'excited'
    CALM = 'calm'
    PROFESSIONAL = 'professional'
    FRIENDLY = 'friendly'


class TTSVoice:
    """TTS Voice configuration"""
    
    def __init__(self, provider: TTSProvider, voice_id: str, name: str, 
                 gender: VoiceGender, language: str, accent: str = None,
                 emotions_supported: List[VoiceEmotion] = None):
        self.provider = provider
        self.voice_id = voice_id
        self.name = name
        self.gender = gender
        self.language = language
        self.accent = accent
        self.emotions_supported = emotions_supported or [VoiceEmotion.NEUTRAL]
    
    def to_dict(self):
        return {
            'provider': self.provider.value,
            'voice_id': self.voice_id,
            'name': self.name,
            'gender': self.gender.value,
            'language': self.language,
            'accent': self.accent,
            'emotions_supported': [e.value for e in self.emotions_supported]
        }


class TTSService:
    """
    Comprehensive Text-to-Speech service with multiple provider support
    """
    
    # Available voices across providers
    AVAILABLE_VOICES = [
        # Azure Speech voices
        TTSVoice(TTSProvider.AZURE, 'en-US-JennyNeural', 'Jenny (US)', VoiceGender.FEMALE, 'en-US', 'American',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.CHEERFUL, VoiceEmotion.SAD, VoiceEmotion.ANGRY]),
        TTSVoice(TTSProvider.AZURE, 'en-US-GuyNeural', 'Guy (US)', VoiceGender.MALE, 'en-US', 'American',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.CHEERFUL, VoiceEmotion.ANGRY]),
        TTSVoice(TTSProvider.AZURE, 'en-GB-SoniaNeural', 'Sonia (UK)', VoiceGender.FEMALE, 'en-GB', 'British',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.CHEERFUL, VoiceEmotion.SAD]),
        TTSVoice(TTSProvider.AZURE, 'en-GB-RyanNeural', 'Ryan (UK)', VoiceGender.MALE, 'en-GB', 'British',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.CHEERFUL]),
        TTSVoice(TTSProvider.AZURE, 'hi-IN-SwaraNeural', 'Swara (Hindi)', VoiceGender.FEMALE, 'hi-IN', 'Indian',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.CHEERFUL]),
        TTSVoice(TTSProvider.AZURE, 'hi-IN-MadhurNeural', 'Madhur (Hindi)', VoiceGender.MALE, 'hi-IN', 'Indian',
                [VoiceEmotion.NEUTRAL]),
        TTSVoice(TTSProvider.AZURE, 'es-ES-ElviraNeural', 'Elvira (Spanish)', VoiceGender.FEMALE, 'es-ES', 'Spanish',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.CHEERFUL]),
        TTSVoice(TTSProvider.AZURE, 'es-ES-AlvaroNeural', 'Alvaro (Spanish)', VoiceGender.MALE, 'es-ES', 'Spanish',
                [VoiceEmotion.NEUTRAL]),
        
        # ElevenLabs voices
        TTSVoice(TTSProvider.ELEVENLABS, 'EXAVITQu4vr4xnSDxMaL', 'Bella', VoiceGender.FEMALE, 'en-US', 'American',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.FRIENDLY, VoiceEmotion.PROFESSIONAL]),
        TTSVoice(TTSProvider.ELEVENLABS, 'pNInz6obpgDQGcFmaJgB', 'Adam', VoiceGender.MALE, 'en-US', 'American',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.PROFESSIONAL, VoiceEmotion.CALM]),
        TTSVoice(TTSProvider.ELEVENLABS, 'MF3mGyEYCl7XYWbV9V6O', 'Emily', VoiceGender.FEMALE, 'en-GB', 'British',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.FRIENDLY]),
        TTSVoice(TTSProvider.ELEVENLABS, 'TxGEqnHWrfWFTfGW9XjX', 'Josh', VoiceGender.MALE, 'en-US', 'American',
                [VoiceEmotion.NEUTRAL, VoiceEmotion.EXCITED, VoiceEmotion.CALM]),
        
        # Google Cloud TTS voices
        TTSVoice(TTSProvider.GOOGLE, 'en-US-Wavenet-D', 'Google US Male', VoiceGender.MALE, 'en-US', 'American'),
        TTSVoice(TTSProvider.GOOGLE, 'en-US-Wavenet-F', 'Google US Female', VoiceGender.FEMALE, 'en-US', 'American'),
        TTSVoice(TTSProvider.GOOGLE, 'en-GB-Wavenet-A', 'Google UK Female', VoiceGender.FEMALE, 'en-GB', 'British'),
        TTSVoice(TTSProvider.GOOGLE, 'hi-IN-Wavenet-A', 'Google Hindi Female', VoiceGender.FEMALE, 'hi-IN', 'Indian'),
        TTSVoice(TTSProvider.GOOGLE, 'es-ES-Wavenet-B', 'Google Spanish Male', VoiceGender.MALE, 'es-ES', 'Spanish'),
    ]
    
    def __init__(self):
        self.api_keys = {
            'azure': {
                'key': current_app.config.get('AZURE_SPEECH_KEY'),
                'region': current_app.config.get('AZURE_SPEECH_REGION', 'eastus')
            },
            'elevenlabs': current_app.config.get('ELEVENLABS_API_KEY'),
            'google': current_app.config.get('GOOGLE_CLOUD_API_KEY'),
            'aws': {
                'access_key': current_app.config.get('AWS_ACCESS_KEY_ID'),
                'secret_key': current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                'region': current_app.config.get('AWS_REGION', 'us-east-1')
            },
            'openai': current_app.config.get('OPENAI_API_KEY')
        }
    
    def get_available_voices(self, language: str = None, gender: VoiceGender = None,
                           provider: TTSProvider = None) -> List[Dict[str, Any]]:
        """
        Get available voices filtered by criteria
        """
        voices = self.AVAILABLE_VOICES
        
        if language:
            voices = [v for v in voices if v.language.startswith(language)]
        
        if gender:
            voices = [v for v in voices if v.gender == gender]
        
        if provider:
            voices = [v for v in voices if v.provider == provider]
        
        return [v.to_dict() for v in voices]
    
    def synthesize_speech(self, text: str, voice_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synthesize speech from text using specified voice
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID from available voices
            options: Additional options (speed, pitch, emotion, volume, etc.)
        
        Returns:
            Dictionary with audio data and metadata
        """
        try:
            # Find voice configuration
            voice = self._find_voice_by_id(voice_id)
            if not voice:
                return {'success': False, 'error': f'Voice {voice_id} not found'}
            
            options = options or {}
            
            # Route to appropriate provider
            if voice.provider == TTSProvider.AZURE:
                return self._synthesize_with_azure(text, voice, options)
            elif voice.provider == TTSProvider.ELEVENLABS:
                return self._synthesize_with_elevenlabs(text, voice, options)
            elif voice.provider == TTSProvider.GOOGLE:
                return self._synthesize_with_google(text, voice, options)
            elif voice.provider == TTSProvider.AWS_POLLY:
                return self._synthesize_with_polly(text, voice, options)
            elif voice.provider == TTSProvider.OPENAI:
                return self._synthesize_with_openai(text, voice, options)
            else:
                return {'success': False, 'error': f'Provider {voice.provider.value} not implemented'}
                
        except Exception as e:
            logger.error("TTS synthesis failed", error=str(e), voice_id=voice_id)
            return {'success': False, 'error': str(e)}
    
    def generate_ssml(self, text: str, options: Dict[str, Any] = None) -> str:
        """
        Generate SSML markup for advanced speech control
        
        Args:
            text: Plain text to convert
            options: SSML options (rate, pitch, volume, breaks, emphasis)
        
        Returns:
            SSML formatted string
        """
        options = options or {}
        
        # Base SSML structure
        ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"'
        
        # Add language if specified
        language = options.get('language', 'en-US')
        ssml += f' xml:lang="{language}">'
        
        # Add voice if specified
        if options.get('voice_name'):
            ssml += f'<voice name="{options["voice_name"]}">'
        
        # Add prosody for speech characteristics
        prosody_attrs = []
        if options.get('rate'):  # Speed: x-slow, slow, medium, fast, x-fast, or percentage
            prosody_attrs.append(f'rate="{options["rate"]}"')
        if options.get('pitch'):  # Pitch: x-low, low, medium, high, x-high, or Hz/percentage
            prosody_attrs.append(f'pitch="{options["pitch"]}"')
        if options.get('volume'):  # Volume: silent, x-soft, soft, medium, loud, x-loud, or dB
            prosody_attrs.append(f'volume="{options["volume"]}"')
        
        if prosody_attrs:
            ssml += f'<prosody {" ".join(prosody_attrs)}>'
        
        # Add emotion/style if supported (Azure specific)
        if options.get('style'):
            ssml += f'<mstts:express-as style="{options["style"]}"'
            if options.get('style_degree'):
                ssml += f' styledegree="{options["style_degree"]}"'
            ssml += '>'
        
        # Process text with breaks and emphasis
        processed_text = self._process_text_for_ssml(text, options)
        ssml += processed_text
        
        # Close tags
        if options.get('style'):
            ssml += '</mstts:express-as>'
        if prosody_attrs:
            ssml += '</prosody>'
        if options.get('voice_name'):
            ssml += '</voice>'
        ssml += '</speak>'
        
        return ssml
    
    def _process_text_for_ssml(self, text: str, options: Dict[str, Any]) -> str:
        """
        Process text with SSML markup for pauses, emphasis, etc.
        """
        # Add sentence breaks
        if options.get('auto_breaks', True):
            text = text.replace('. ', '. <break time="500ms"/> ')
            text = text.replace('! ', '! <break time="500ms"/> ')
            text = text.replace('? ', '? <break time="500ms"/> ')
            text = text.replace(', ', ', <break time="200ms"/> ')
        
        # Add emphasis to specific words
        if options.get('emphasis_words'):
            for word in options['emphasis_words']:
                text = text.replace(word, f'<emphasis level="strong">{word}</emphasis>')
        
        # Add custom breaks
        if options.get('breaks'):
            for position, duration in options['breaks'].items():
                text = text[:position] + f'<break time="{duration}ms"/>' + text[position:]
        
        return text
    
    def _find_voice_by_id(self, voice_id: str) -> Optional[TTSVoice]:
        """Find voice configuration by ID"""
        for voice in self.AVAILABLE_VOICES:
            if voice.voice_id == voice_id:
                return voice
        return None
    
    def _synthesize_with_azure(self, text: str, voice: TTSVoice, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize speech using Azure Cognitive Services
        """
        try:
            azure_config = self.api_keys['azure']
            if not azure_config['key']:
                return {'success': False, 'error': 'Azure Speech API key not configured'}
            
            # Configure Azure Speech SDK
            speech_config = speechsdk.SpeechConfig(
                subscription=azure_config['key'],
                region=azure_config['region']
            )
            
            # Set voice
            speech_config.speech_synthesis_voice_name = voice.voice_id
            
            # Set audio format (16kHz, 16-bit, mono for optimal quality/size)
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
            )
            
            # Generate SSML if emotion is specified
            if options.get('emotion') and options['emotion'] != VoiceEmotion.NEUTRAL.value:
                ssml_options = {
                    'voice_name': voice.voice_id,
                    'style': options['emotion'],
                    'style_degree': options.get('emotion_intensity', 1.0),
                    'rate': options.get('speed', 'medium'),
                    'pitch': options.get('pitch', 'medium'),
                    'volume': options.get('volume', 'medium')
                }
                ssml_text = self.generate_ssml(text, ssml_options)
                
                # Use SSML synthesis
                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=speech_config,
                    audio_config=None  # Output to memory
                )
                result = synthesizer.speak_ssml_async(ssml_text).get()
            else:
                # Use plain text synthesis
                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=speech_config,
                    audio_config=None
                )
                result = synthesizer.speak_text_async(text).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data
                
                # Calculate audio metrics
                audio_metrics = self._analyze_audio(audio_data)
                
                return {
                    'success': True,
                    'audio_data': base64.b64encode(audio_data).decode('utf-8'),
                    'audio_format': 'wav',
                    'sample_rate': 16000,
                    'duration_seconds': audio_metrics['duration'],
                    'file_size': len(audio_data),
                    'voice_id': voice.voice_id,
                    'provider': TTSProvider.AZURE.value,
                    'cost': self._calculate_tts_cost(len(text), TTSProvider.AZURE),
                    'metrics': audio_metrics
                }
            else:
                error_details = result.cancellation_details
                return {
                    'success': False,
                    'error': f'Azure TTS failed: {error_details.reason}',
                    'error_details': error_details.error_details
                }
                
        except Exception as e:
            logger.error("Azure TTS synthesis failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _synthesize_with_elevenlabs(self, text: str, voice: TTSVoice, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize speech using ElevenLabs API
        """
        try:
            api_key = self.api_keys['elevenlabs']
            if not api_key:
                return {'success': False, 'error': 'ElevenLabs API key not configured'}
            
            # ElevenLabs API endpoint
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice.voice_id}"
            
            headers = {
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': api_key
            }
            
            # Voice settings
            voice_settings = {
                'stability': options.get('stability', 0.5),
                'similarity_boost': options.get('similarity_boost', 0.75),
                'style': options.get('style', 0.0),
                'use_speaker_boost': options.get('speaker_boost', True)
            }
            
            payload = {
                'text': text,
                'model_id': options.get('model_id', 'eleven_monolingual_v1'),
                'voice_settings': voice_settings
            }
            
            # Make API request
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                audio_data = response.content
                
                # Convert MP3 to WAV for consistency
                wav_data = self._convert_mp3_to_wav(audio_data)
                audio_metrics = self._analyze_audio(wav_data)
                
                return {
                    'success': True,
                    'audio_data': base64.b64encode(wav_data).decode('utf-8'),
                    'audio_format': 'wav',
                    'sample_rate': 22050,
                    'duration_seconds': audio_metrics['duration'],
                    'file_size': len(wav_data),
                    'voice_id': voice.voice_id,
                    'provider': TTSProvider.ELEVENLABS.value,
                    'cost': self._calculate_tts_cost(len(text), TTSProvider.ELEVENLABS),
                    'metrics': audio_metrics
                }
            else:
                return {
                    'success': False,
                    'error': f'ElevenLabs API error: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error("ElevenLabs TTS synthesis failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _synthesize_with_google(self, text: str, voice: TTSVoice, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize speech using Google Cloud Text-to-Speech
        """
        try:
            api_key = self.api_keys['google']
            if not api_key:
                return {'success': False, 'error': 'Google Cloud API key not configured'}
            
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
            
            # Build request
            synthesis_input = {'text': text}
            
            voice_config = {
                'languageCode': voice.language,
                'name': voice.voice_id
            }
            
            audio_config = {
                'audioEncoding': 'LINEAR16',
                'speakingRate': options.get('speed', 1.0),
                'pitch': options.get('pitch', 0.0),
                'volumeGainDb': options.get('volume', 0.0),
                'sampleRateHertz': 16000
            }
            
            payload = {
                'input': synthesis_input,
                'voice': voice_config,
                'audioConfig': audio_config
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                audio_content = response.json()['audioContent']
                audio_data = base64.b64decode(audio_content)
                
                # Create WAV header for raw PCM data
                wav_data = self._create_wav_from_pcm(audio_data, 16000)
                audio_metrics = self._analyze_audio(wav_data)
                
                return {
                    'success': True,
                    'audio_data': base64.b64encode(wav_data).decode('utf-8'),
                    'audio_format': 'wav',
                    'sample_rate': 16000,
                    'duration_seconds': audio_metrics['duration'],
                    'file_size': len(wav_data),
                    'voice_id': voice.voice_id,
                    'provider': TTSProvider.GOOGLE.value,
                    'cost': self._calculate_tts_cost(len(text), TTSProvider.GOOGLE),
                    'metrics': audio_metrics
                }
            else:
                return {
                    'success': False,
                    'error': f'Google TTS API error: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error("Google TTS synthesis failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _synthesize_with_polly(self, text: str, voice: TTSVoice, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize speech using AWS Polly
        """
        # Implementation would require boto3
        return {'success': False, 'error': 'AWS Polly not yet implemented'}
    
    def _synthesize_with_openai(self, text: str, voice: TTSVoice, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize speech using OpenAI TTS
        """
        try:
            api_key = self.api_keys['openai']
            if not api_key:
                return {'success': False, 'error': 'OpenAI API key not configured'}
            
            url = "https://api.openai.com/v1/audio/speech"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'tts-1-hd',  # High quality model
                'input': text,
                'voice': options.get('openai_voice', 'alloy'),  # alloy, echo, fable, onyx, nova, shimmer
                'response_format': 'wav',
                'speed': options.get('speed', 1.0)
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                audio_data = response.content
                audio_metrics = self._analyze_audio(audio_data)
                
                return {
                    'success': True,
                    'audio_data': base64.b64encode(audio_data).decode('utf-8'),
                    'audio_format': 'wav',
                    'sample_rate': 24000,
                    'duration_seconds': audio_metrics['duration'],
                    'file_size': len(audio_data),
                    'voice_id': 'openai_' + payload['voice'],
                    'provider': TTSProvider.OPENAI.value,
                    'cost': self._calculate_tts_cost(len(text), TTSProvider.OPENAI),
                    'metrics': audio_metrics
                }
            else:
                return {
                    'success': False,
                    'error': f'OpenAI TTS API error: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error("OpenAI TTS synthesis failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _analyze_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Analyze audio data to extract metrics
        """
        try:
            # Read WAV file
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)
                    channels = wav_file.getnchannels()
                    sampwidth = wav_file.getsampwidth()
                    
                    # Calculate RMS (volume level)
                    audio_io.seek(44)  # Skip WAV header
                    raw_data = audio_io.read()
                    
                    # Convert bytes to samples
                    fmt = f'{len(raw_data) // sampwidth}h' if sampwidth == 2 else f'{len(raw_data)}b'
                    samples = struct.unpack(fmt, raw_data)
                    
                    # Calculate RMS
                    sum_squares = sum(s**2 for s in samples)
                    rms = (sum_squares / len(samples)) ** 0.5
                    
                    # Normalize RMS to 0-100 scale
                    max_value = 2**(sampwidth * 8 - 1)
                    normalized_rms = (rms / max_value) * 100
                    
                    return {
                        'duration': duration,
                        'sample_rate': rate,
                        'channels': channels,
                        'bit_depth': sampwidth * 8,
                        'average_volume': normalized_rms,
                        'total_samples': frames
                    }
        except Exception as e:
            logger.error("Audio analysis failed", error=str(e))
            return {
                'duration': 0,
                'sample_rate': 0,
                'channels': 0,
                'bit_depth': 0,
                'average_volume': 0,
                'total_samples': 0
            }
    
    def _convert_mp3_to_wav(self, mp3_data: bytes) -> bytes:
        """
        Convert MP3 audio to WAV format
        Note: This is a placeholder - actual implementation would use pydub or ffmpeg
        """
        # In production, use:
        # from pydub import AudioSegment
        # audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        # wav_io = io.BytesIO()
        # audio.export(wav_io, format='wav')
        # return wav_io.getvalue()
        
        # For now, return mock WAV data
        return self._create_wav_from_pcm(b'\x00' * 16000, 16000)
    
    def _create_wav_from_pcm(self, pcm_data: bytes, sample_rate: int) -> bytes:
        """
        Create WAV file from raw PCM data
        """
        # WAV file parameters
        channels = 1
        sampwidth = 2
        
        # Create WAV file in memory
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sampwidth)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        return wav_io.getvalue()
    
    def _calculate_tts_cost(self, text_length: int, provider: TTSProvider) -> float:
        """
        Calculate TTS cost based on text length and provider
        """
        # Cost per 1000 characters
        costs = {
            TTSProvider.AZURE: 0.016,  # $16 per 1M characters
            TTSProvider.ELEVENLABS: 0.30,  # $300 per 1M characters
            TTSProvider.GOOGLE: 0.016,  # $16 per 1M characters
            TTSProvider.AWS_POLLY: 0.004,  # $4 per 1M characters
            TTSProvider.OPENAI: 0.030  # $30 per 1M characters
        }
        
        cost_per_char = costs.get(provider, 0.01) / 1000
        return text_length * cost_per_char
    
    def estimate_speech_duration(self, text: str, words_per_minute: int = 150) -> float:
        """
        Estimate speech duration based on text length
        
        Args:
            text: Text to estimate
            words_per_minute: Speaking rate (default 150 for normal speech)
        
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        duration_minutes = word_count / words_per_minute
        return duration_minutes * 60
    
    def optimize_text_for_speech(self, text: str) -> str:
        """
        Optimize text for better speech synthesis
        
        - Expand abbreviations
        - Convert numbers to words
        - Fix punctuation for natural pauses
        """
        # Expand common abbreviations
        abbreviations = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Missus',
            'Ms.': 'Miss',
            'Prof.': 'Professor',
            'St.': 'Street',
            'Ave.': 'Avenue',
            'etc.': 'et cetera',
            'vs.': 'versus',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'U.S.': 'United States',
            'U.K.': 'United Kingdom'
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        # Add pauses after sentences
        text = text.replace('. ', '. ')
        text = text.replace('! ', '! ')
        text = text.replace('? ', '? ')
        
        return text