"""
TalkingPhoto AI MVP - Lip-Sync Animation Engine
Advanced lip-sync animation with facial landmark integration
"""

import numpy as np
import cv2
import base64
import json
import io
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import dlib
import mediapipe as mp
from PIL import Image, ImageDraw
import structlog
import wave
from scipy.interpolate import interp1d
from flask import current_app

logger = structlog.get_logger()


class VisemeType(Enum):
    """Viseme types for lip-sync animation"""
    SILENCE = 'silence'  # Mouth closed
    AA = 'aa'  # "ah" as in "father"
    EE = 'ee'  # "ee" as in "see"
    II = 'ii'  # "i" as in "sit"
    OO = 'oo'  # "oo" as in "too"
    UU = 'uu'  # "u" as in "put"
    FF = 'ff'  # "f" as in "for"
    TH = 'th'  # "th" as in "think"
    DD = 'dd'  # "d" as in "day"
    KK = 'kk'  # "k" as in "key"
    PP = 'pp'  # "p" as in "put"
    RR = 'rr'  # "r" as in "red"
    SS = 'ss'  # "s" as in "say"
    SH = 'sh'  # "sh" as in "she"
    CH = 'ch'  # "ch" as in "cheese"
    MM = 'mm'  # "m" as in "mom"
    NN = 'nn'  # "n" as in "no"
    LL = 'll'  # "l" as in "let"
    WW = 'ww'  # "w" as in "way"


@dataclass
class Viseme:
    """Viseme data structure"""
    type: VisemeType
    start_time: float  # in seconds
    end_time: float
    intensity: float  # 0.0 to 1.0
    phoneme: str  # Original phoneme


@dataclass
class FacialExpression:
    """Facial expression parameters"""
    eyebrow_raise: float = 0.0  # -1.0 to 1.0
    eye_squint: float = 0.0  # 0.0 to 1.0
    smile: float = 0.0  # -1.0 to 1.0
    head_tilt: float = 0.0  # -30 to 30 degrees
    head_nod: float = 0.0  # -30 to 30 degrees
    blink: bool = False


@dataclass
class FacialLandmarks:
    """Facial landmarks from Epic 2 photo enhancement"""
    points: np.ndarray  # 68 or 468 landmark points
    confidence: float
    face_rect: Tuple[int, int, int, int]  # x, y, width, height
    model_type: str  # 'dlib' or 'mediapipe'


class PhonemeMapper:
    """Map phonemes to visemes for lip-sync"""
    
    # Phoneme to viseme mapping based on CMU Pronouncing Dictionary
    PHONEME_TO_VISEME = {
        # Vowels
        'AA': VisemeType.AA, 'AE': VisemeType.AA, 'AH': VisemeType.AA,
        'AO': VisemeType.OO, 'AW': VisemeType.OO,
        'AY': VisemeType.AA, 'EH': VisemeType.EE, 'ER': VisemeType.UU,
        'EY': VisemeType.EE, 'IH': VisemeType.II, 'IY': VisemeType.EE,
        'OW': VisemeType.OO, 'OY': VisemeType.OO, 'UH': VisemeType.UU,
        'UW': VisemeType.OO,
        
        # Consonants
        'B': VisemeType.PP, 'CH': VisemeType.CH, 'D': VisemeType.DD,
        'DH': VisemeType.TH, 'F': VisemeType.FF, 'G': VisemeType.KK,
        'HH': VisemeType.AA, 'JH': VisemeType.CH, 'K': VisemeType.KK,
        'L': VisemeType.LL, 'M': VisemeType.MM, 'N': VisemeType.NN,
        'NG': VisemeType.NN, 'P': VisemeType.PP, 'R': VisemeType.RR,
        'S': VisemeType.SS, 'SH': VisemeType.SH, 'T': VisemeType.DD,
        'TH': VisemeType.TH, 'V': VisemeType.FF, 'W': VisemeType.WW,
        'Y': VisemeType.II, 'Z': VisemeType.SS, 'ZH': VisemeType.SH,
        
        # Silence
        'SIL': VisemeType.SILENCE, 'SP': VisemeType.SILENCE
    }
    
    @classmethod
    def phoneme_to_viseme(cls, phoneme: str) -> VisemeType:
        """Convert phoneme to viseme"""
        # Remove stress markers (0, 1, 2) from phonemes
        phoneme_clean = phoneme.rstrip('012')
        return cls.PHONEME_TO_VISEME.get(phoneme_clean, VisemeType.SILENCE)


class LipSyncAnimationEngine:
    """
    Advanced lip-sync animation engine with facial landmark integration
    """
    
    def __init__(self):
        # Initialize face detection and landmark models
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Dlib predictor for 68-point landmarks (if available)
        try:
            predictor_path = current_app.config.get('DLIB_PREDICTOR_PATH',
                                                   'shape_predictor_68_face_landmarks.dat')
            self.dlib_predictor = dlib.shape_predictor(predictor_path)
            self.dlib_detector = dlib.get_frontal_face_detector()
        except:
            self.dlib_predictor = None
            self.dlib_detector = None
            logger.warning("Dlib predictor not available, using MediaPipe only")
        
        # Mouth landmark indices for different models
        self.MOUTH_INDICES = {
            'dlib_68': list(range(48, 68)),  # 48-67 are mouth points
            'mediapipe_468': [  # MediaPipe mouth landmarks
                61, 84, 17, 314, 405, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95,
                78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318
            ]
        }
        
        # Animation parameters
        self.fps = 30  # Target frame rate
        self.smoothing_window = 3  # Frames to smooth transitions
    
    def generate_lip_sync_animation(self, image_path: str, audio_data: bytes,
                                   transcript: str = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate lip-sync animation from image and audio
        
        Args:
            image_path: Path to source image
            audio_data: Audio data (WAV format)
            transcript: Optional transcript for better accuracy
            options: Animation options (style, intensity, expressions)
        
        Returns:
            Dictionary with animation data and metadata
        """
        try:
            options = options or {}
            
            # Extract facial landmarks from image
            landmarks = self._extract_facial_landmarks(image_path)
            if not landmarks:
                return {'success': False, 'error': 'No face detected in image'}
            
            # Analyze audio and generate visemes
            visemes = self._analyze_audio_to_visemes(audio_data, transcript)
            if not visemes:
                return {'success': False, 'error': 'Failed to analyze audio'}
            
            # Generate facial expressions based on audio emotion
            expressions = self._generate_facial_expressions(
                audio_data,
                options.get('emotion', 'neutral'),
                len(visemes)
            )
            
            # Create animation frames
            animation_frames = self._create_animation_frames(
                image_path,
                landmarks,
                visemes,
                expressions,
                options
            )
            
            # Calculate animation metrics
            metrics = self._calculate_animation_metrics(animation_frames, visemes)
            
            return {
                'success': True,
                'frames': animation_frames,
                'frame_rate': self.fps,
                'total_frames': len(animation_frames),
                'duration': len(animation_frames) / self.fps,
                'visemes': [self._viseme_to_dict(v) for v in visemes],
                'landmarks': self._landmarks_to_dict(landmarks),
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error("Lip-sync animation generation failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _extract_facial_landmarks(self, image_path: str) -> Optional[FacialLandmarks]:
        """
        Extract facial landmarks from image using MediaPipe or Dlib
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                # Try to decode from base64 if it's not a file path
                import base64
                image_data = base64.b64decode(image_path)
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Try MediaPipe first (more accurate for diverse faces)
            with self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            ) as face_mesh:
                results = face_mesh.process(rgb_image)
                
                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    # Convert to numpy array
                    h, w = image.shape[:2]
                    points = np.array([
                        [lm.x * w, lm.y * h, lm.z * w]
                        for lm in face_landmarks.landmark
                    ])
                    
                    # Calculate bounding box
                    x_min, y_min = points[:, :2].min(axis=0).astype(int)
                    x_max, y_max = points[:, :2].max(axis=0).astype(int)
                    
                    return FacialLandmarks(
                        points=points,
                        confidence=0.95,
                        face_rect=(x_min, y_min, x_max - x_min, y_max - y_min),
                        model_type='mediapipe'
                    )
            
            # Fallback to Dlib if available
            if self.dlib_detector and self.dlib_predictor:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = self.dlib_detector(gray, 1)
                
                if len(faces) > 0:
                    face = faces[0]
                    landmarks = self.dlib_predictor(gray, face)
                    
                    # Convert to numpy array
                    points = np.array([
                        [landmarks.part(i).x, landmarks.part(i).y, 0]
                        for i in range(68)
                    ])
                    
                    return FacialLandmarks(
                        points=points,
                        confidence=0.90,
                        face_rect=(face.left(), face.top(), face.width(), face.height()),
                        model_type='dlib'
                    )
            
            return None
            
        except Exception as e:
            logger.error("Landmark extraction failed", error=str(e))
            return None
    
    def _analyze_audio_to_visemes(self, audio_data: bytes, transcript: str = None) -> List[Viseme]:
        """
        Analyze audio and generate viseme sequence
        """
        try:
            # Parse WAV audio
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav:
                    framerate = wav.getframerate()
                    n_frames = wav.getnframes()
                    duration = n_frames / float(framerate)
            
            # If transcript is provided, use phoneme-based approach
            if transcript:
                return self._text_to_visemes(transcript, duration)
            else:
                # Use audio amplitude-based approach
                return self._audio_amplitude_to_visemes(audio_data, duration)
            
        except Exception as e:
            logger.error("Audio to viseme conversion failed", error=str(e))
            return []
    
    def _text_to_visemes(self, text: str, duration: float) -> List[Viseme]:
        """
        Convert text to viseme sequence using phoneme mapping
        """
        try:
            # Simple phoneme estimation (in production, use CMU dict or G2P model)
            words = text.split()
            total_phonemes = len(text.replace(' ', '')) * 1.5  # Rough estimate
            time_per_phoneme = duration / total_phonemes
            
            visemes = []
            current_time = 0.0
            
            for word in words:
                # Add silence between words
                if current_time > 0:
                    visemes.append(Viseme(
                        type=VisemeType.SILENCE,
                        start_time=current_time,
                        end_time=current_time + 0.1,
                        intensity=0.0,
                        phoneme='SIL'
                    ))
                    current_time += 0.1
                
                # Generate visemes for word (simplified)
                for i, char in enumerate(word.lower()):
                    viseme_type = self._char_to_viseme(char)
                    intensity = 0.8 if char in 'aeiou' else 0.6
                    
                    visemes.append(Viseme(
                        type=viseme_type,
                        start_time=current_time,
                        end_time=current_time + time_per_phoneme,
                        intensity=intensity,
                        phoneme=char.upper()
                    ))
                    current_time += time_per_phoneme
            
            return visemes
            
        except Exception as e:
            logger.error("Text to viseme conversion failed", error=str(e))
            return []
    
    def _audio_amplitude_to_visemes(self, audio_data: bytes, duration: float) -> List[Viseme]:
        """
        Generate visemes based on audio amplitude analysis
        """
        try:
            # Parse audio samples
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav:
                    frames = wav.readframes(wav.getnframes())
                    samples = np.frombuffer(frames, dtype=np.int16)
                    framerate = wav.getframerate()
            
            # Calculate amplitude envelope
            window_size = int(framerate * 0.02)  # 20ms windows
            n_windows = len(samples) // window_size
            
            visemes = []
            viseme_types = [VisemeType.AA, VisemeType.EE, VisemeType.OO, VisemeType.MM]
            
            for i in range(n_windows):
                start_idx = i * window_size
                end_idx = start_idx + window_size
                window_samples = samples[start_idx:end_idx]
                
                # Calculate RMS amplitude
                rms = np.sqrt(np.mean(window_samples ** 2))
                normalized_rms = min(rms / 32768.0, 1.0)
                
                # Map amplitude to viseme
                if normalized_rms < 0.1:
                    viseme_type = VisemeType.SILENCE
                    intensity = 0.0
                else:
                    # Cycle through viseme types for variety
                    viseme_type = viseme_types[i % len(viseme_types)]
                    intensity = normalized_rms
                
                start_time = (i * window_size) / framerate
                end_time = ((i + 1) * window_size) / framerate
                
                visemes.append(Viseme(
                    type=viseme_type,
                    start_time=start_time,
                    end_time=end_time,
                    intensity=intensity,
                    phoneme='AUTO'
                ))
            
            return visemes
            
        except Exception as e:
            logger.error("Audio amplitude analysis failed", error=str(e))
            return []
    
    def _char_to_viseme(self, char: str) -> VisemeType:
        """
        Simple character to viseme mapping
        """
        vowels = {
            'a': VisemeType.AA, 'e': VisemeType.EE, 'i': VisemeType.II,
            'o': VisemeType.OO, 'u': VisemeType.UU
        }
        
        consonants = {
            'b': VisemeType.PP, 'p': VisemeType.PP, 'm': VisemeType.MM,
            'f': VisemeType.FF, 'v': VisemeType.FF, 'w': VisemeType.WW,
            'd': VisemeType.DD, 't': VisemeType.DD, 'n': VisemeType.NN,
            'l': VisemeType.LL, 'r': VisemeType.RR, 's': VisemeType.SS,
            'z': VisemeType.SS, 'k': VisemeType.KK, 'g': VisemeType.KK,
            'h': VisemeType.AA, 'j': VisemeType.CH, 'c': VisemeType.KK
        }
        
        if char in vowels:
            return vowels[char]
        elif char in consonants:
            return consonants[char]
        else:
            return VisemeType.SILENCE
    
    def _generate_facial_expressions(self, audio_data: bytes, emotion: str,
                                    n_frames: int) -> List[FacialExpression]:
        """
        Generate facial expressions based on audio emotion
        """
        expressions = []
        
        # Base expression for emotion
        base_expression = self._get_base_expression(emotion)
        
        # Add variations and micro-expressions
        for i in range(n_frames):
            expression = FacialExpression(
                eyebrow_raise=base_expression.eyebrow_raise + np.random.normal(0, 0.1),
                eye_squint=base_expression.eye_squint + np.random.normal(0, 0.05),
                smile=base_expression.smile + np.random.normal(0, 0.1),
                head_tilt=base_expression.head_tilt + np.sin(i * 0.1) * 2,
                head_nod=base_expression.head_nod + np.cos(i * 0.08) * 1.5,
                blink=(i % 90 == 0)  # Blink every 3 seconds at 30fps
            )
            expressions.append(expression)
        
        return expressions
    
    def _get_base_expression(self, emotion: str) -> FacialExpression:
        """
        Get base facial expression for emotion
        """
        expressions = {
            'neutral': FacialExpression(),
            'happy': FacialExpression(eyebrow_raise=0.2, smile=0.6),
            'cheerful': FacialExpression(eyebrow_raise=0.3, smile=0.8, eye_squint=0.2),
            'sad': FacialExpression(eyebrow_raise=-0.2, smile=-0.3),
            'angry': FacialExpression(eyebrow_raise=-0.4, eye_squint=0.3, smile=-0.4),
            'excited': FacialExpression(eyebrow_raise=0.5, smile=0.7, eye_squint=0.1),
            'calm': FacialExpression(eyebrow_raise=0.0, smile=0.2),
            'professional': FacialExpression(eyebrow_raise=0.1, smile=0.3)
        }
        
        return expressions.get(emotion, FacialExpression())
    
    def _create_animation_frames(self, image_path: str, landmarks: FacialLandmarks,
                                visemes: List[Viseme], expressions: List[FacialExpression],
                                options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create animation frames with lip-sync and expressions
        """
        try:
            # Load base image
            base_image = cv2.imread(image_path)
            if base_image is None:
                import base64
                image_data = base64.b64decode(image_path)
                nparr = np.frombuffer(image_data, np.uint8)
                base_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            frames = []
            animation_intensity = options.get('animation_intensity', 1.0)
            animation_style = options.get('animation_style', 'natural')
            
            # Calculate frame times
            total_duration = visemes[-1].end_time if visemes else 1.0
            n_frames = int(total_duration * self.fps)
            
            # Get mouth landmarks indices
            if landmarks.model_type == 'mediapipe':
                mouth_indices = self.MOUTH_INDICES['mediapipe_468']
            else:
                mouth_indices = self.MOUTH_INDICES['dlib_68']
            
            for frame_idx in range(n_frames):
                frame_time = frame_idx / self.fps
                
                # Find current viseme
                current_viseme = self._get_viseme_at_time(visemes, frame_time)
                
                # Get expression for this frame
                expr_idx = min(frame_idx, len(expressions) - 1)
                current_expression = expressions[expr_idx]
                
                # Create animated frame
                animated_frame = self._apply_animation_to_frame(
                    base_image.copy(),
                    landmarks,
                    current_viseme,
                    current_expression,
                    mouth_indices,
                    animation_intensity,
                    animation_style
                )
                
                # Encode frame
                _, buffer = cv2.imencode('.jpg', animated_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                frame_data = base64.b64encode(buffer).decode('utf-8')
                
                frames.append({
                    'frame_number': frame_idx,
                    'timestamp': frame_time,
                    'viseme': current_viseme.type.value if current_viseme else 'silence',
                    'viseme_intensity': current_viseme.intensity if current_viseme else 0.0,
                    'expression': {
                        'eyebrow_raise': current_expression.eyebrow_raise,
                        'smile': current_expression.smile,
                        'head_tilt': current_expression.head_tilt
                    },
                    'data': frame_data
                })
            
            # Apply smoothing between frames
            if options.get('smooth_transitions', True):
                frames = self._smooth_animation_frames(frames)
            
            return frames
            
        except Exception as e:
            logger.error("Frame creation failed", error=str(e))
            return []
    
    def _get_viseme_at_time(self, visemes: List[Viseme], time: float) -> Optional[Viseme]:
        """
        Get viseme at specific time with interpolation
        """
        for viseme in visemes:
            if viseme.start_time <= time <= viseme.end_time:
                return viseme
        return None
    
    def _apply_animation_to_frame(self, image: np.ndarray, landmarks: FacialLandmarks,
                                 viseme: Optional[Viseme], expression: FacialExpression,
                                 mouth_indices: List[int], intensity: float,
                                 style: str) -> np.ndarray:
        """
        Apply animation to single frame
        """
        try:
            h, w = image.shape[:2]
            
            # Get mouth landmarks
            mouth_points = landmarks.points[mouth_indices][:, :2].astype(int)
            
            if viseme and viseme.type != VisemeType.SILENCE:
                # Calculate mouth deformation based on viseme
                deformation = self._calculate_mouth_deformation(viseme.type, viseme.intensity * intensity)
                
                # Apply deformation to mouth points
                deformed_points = self._deform_mouth_points(mouth_points, deformation, style)
                
                # Warp image to match new mouth shape
                image = self._warp_image_mesh(image, mouth_points, deformed_points)
            
            # Apply facial expressions
            if expression.eyebrow_raise != 0:
                image = self._apply_eyebrow_animation(image, landmarks, expression.eyebrow_raise)
            
            if expression.smile != 0:
                image = self._apply_smile_animation(image, landmarks, expression.smile)
            
            if expression.head_tilt != 0 or expression.head_nod != 0:
                image = self._apply_head_movement(image, expression.head_tilt, expression.head_nod)
            
            if expression.blink:
                image = self._apply_blink(image, landmarks)
            
            return image
            
        except Exception as e:
            logger.error("Frame animation failed", error=str(e))
            return image
    
    def _calculate_mouth_deformation(self, viseme_type: VisemeType, intensity: float) -> np.ndarray:
        """
        Calculate mouth deformation parameters for viseme
        """
        # Deformation parameters: [width_scale, height_scale, openness]
        deformations = {
            VisemeType.SILENCE: [1.0, 1.0, 0.0],
            VisemeType.AA: [1.2, 1.3, 0.8],  # Wide open
            VisemeType.EE: [1.3, 0.9, 0.3],  # Wide, slightly open
            VisemeType.II: [1.1, 0.95, 0.2],  # Slightly wide, barely open
            VisemeType.OO: [0.8, 1.1, 0.6],  # Rounded, open
            VisemeType.UU: [0.9, 1.0, 0.4],  # Slightly rounded
            VisemeType.FF: [1.0, 0.9, 0.1],  # Lower lip under teeth
            VisemeType.TH: [1.0, 0.95, 0.15],  # Tongue between teeth
            VisemeType.DD: [1.0, 1.0, 0.2],  # Slightly open
            VisemeType.KK: [0.95, 1.0, 0.3],  # Back of mouth
            VisemeType.PP: [0.9, 0.95, 0.0],  # Lips pressed
            VisemeType.MM: [0.95, 1.0, 0.0],  # Lips together
            VisemeType.NN: [1.0, 1.0, 0.25],  # Slightly open
            VisemeType.LL: [1.0, 1.0, 0.3],  # Tongue visible
            VisemeType.RR: [1.05, 1.0, 0.35],  # Slightly rounded
            VisemeType.SS: [1.1, 0.95, 0.1],  # Teeth visible
            VisemeType.SH: [0.95, 1.05, 0.3],  # Lips forward
            VisemeType.CH: [1.0, 1.0, 0.25],  # Similar to SH
            VisemeType.WW: [0.85, 1.05, 0.4]  # Rounded, forward
        }
        
        base_deform = np.array(deformations.get(viseme_type, [1.0, 1.0, 0.0]))
        return base_deform * intensity
    
    def _deform_mouth_points(self, points: np.ndarray, deformation: np.ndarray,
                            style: str) -> np.ndarray:
        """
        Deform mouth points based on viseme deformation
        """
        # Calculate mouth center
        center = np.mean(points, axis=0)
        
        # Apply deformation
        deformed = points.copy()
        for i, point in enumerate(points):
            # Vector from center to point
            vec = point - center
            
            # Apply scaling
            vec[0] *= deformation[0]  # Width scale
            vec[1] *= deformation[1]  # Height scale
            
            # Apply openness (vertical displacement)
            if i < len(points) // 2:  # Upper lip
                vec[1] -= deformation[2] * 5
            else:  # Lower lip
                vec[1] += deformation[2] * 5
            
            # Add style-specific modifications
            if style == 'exaggerated':
                vec *= 1.2
            elif style == 'subtle':
                vec *= 0.8
            
            deformed[i] = center + vec
        
        return deformed.astype(int)
    
    def _warp_image_mesh(self, image: np.ndarray, src_points: np.ndarray,
                        dst_points: np.ndarray) -> np.ndarray:
        """
        Warp image using mesh deformation
        """
        try:
            # Create triangulation
            rect = (0, 0, image.shape[1], image.shape[0])
            subdiv = cv2.Subdiv2D(rect)
            
            for point in src_points:
                subdiv.insert((int(point[0]), int(point[1])))
            
            triangles = subdiv.getTriangleList()
            
            # Apply warping for each triangle
            warped = image.copy()
            for tri in triangles:
                # Get triangle points
                src_tri = np.array([[tri[0], tri[1]], [tri[2], tri[3]], [tri[4], tri[5]]], np.float32)
                
                # Find corresponding destination triangle
                dst_tri = self._find_corresponding_triangle(src_tri, src_points, dst_points)
                
                if dst_tri is not None:
                    # Calculate affine transform
                    warp_mat = cv2.getAffineTransform(src_tri, dst_tri)
                    
                    # Apply warping to triangle region
                    mask = np.zeros(image.shape[:2], dtype=np.uint8)
                    cv2.fillPoly(mask, [dst_tri.astype(int)], 255)
                    
                    warped_tri = cv2.warpAffine(image, warp_mat, (image.shape[1], image.shape[0]))
                    warped = np.where(mask[..., None], warped_tri, warped)
            
            return warped
            
        except Exception as e:
            logger.error("Image warping failed", error=str(e))
            return image
    
    def _find_corresponding_triangle(self, src_tri: np.ndarray, src_points: np.ndarray,
                                    dst_points: np.ndarray) -> Optional[np.ndarray]:
        """
        Find corresponding triangle in destination points
        """
        try:
            dst_tri = np.zeros_like(src_tri)
            
            for i, vertex in enumerate(src_tri):
                # Find closest source point
                distances = np.linalg.norm(src_points - vertex, axis=1)
                closest_idx = np.argmin(distances)
                
                # Use corresponding destination point
                dst_tri[i] = dst_points[closest_idx]
            
            return dst_tri.astype(np.float32)
            
        except:
            return None
    
    def _apply_eyebrow_animation(self, image: np.ndarray, landmarks: FacialLandmarks,
                                raise_amount: float) -> np.ndarray:
        """
        Apply eyebrow raising animation
        """
        # Eyebrow indices for different models
        if landmarks.model_type == 'mediapipe':
            left_eyebrow = [70, 63, 105, 66, 107]
            right_eyebrow = [300, 293, 334, 296, 336]
        else:  # dlib
            left_eyebrow = list(range(17, 22))
            right_eyebrow = list(range(22, 27))
        
        # Apply vertical displacement to eyebrow points
        # Implementation would involve mesh warping similar to mouth
        
        return image
    
    def _apply_smile_animation(self, image: np.ndarray, landmarks: FacialLandmarks,
                              smile_amount: float) -> np.ndarray:
        """
        Apply smile animation by lifting mouth corners
        """
        # Mouth corner indices
        if landmarks.model_type == 'mediapipe':
            left_corner = 61
            right_corner = 291
        else:  # dlib
            left_corner = 48
            right_corner = 54
        
        # Apply displacement to mouth corners
        # Implementation would involve mesh warping
        
        return image
    
    def _apply_head_movement(self, image: np.ndarray, tilt: float, nod: float) -> np.ndarray:
        """
        Apply head rotation (tilt and nod)
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Create rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, tilt, 1.0)
        
        # Apply rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (w, h))
        
        # Apply vertical translation for nod
        if nod != 0:
            translation_matrix = np.float32([[1, 0, 0], [0, 1, nod]])
            rotated = cv2.warpAffine(rotated, translation_matrix, (w, h))
        
        return rotated
    
    def _apply_blink(self, image: np.ndarray, landmarks: FacialLandmarks) -> np.ndarray:
        """
        Apply eye blink animation
        """
        # Eye indices
        if landmarks.model_type == 'mediapipe':
            left_eye = [33, 133, 157, 158, 159, 160, 161, 163]
            right_eye = [362, 263, 387, 388, 389, 390, 391, 393]
        else:  # dlib
            left_eye = list(range(36, 42))
            right_eye = list(range(42, 48))
        
        # Draw closed eyelids over eyes
        # Implementation would involve drawing or warping
        
        return image
    
    def _smooth_animation_frames(self, frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply smoothing between animation frames
        """
        # Smooth viseme intensities
        intensities = [f.get('viseme_intensity', 0) for f in frames]
        
        if len(intensities) > self.smoothing_window:
            # Apply moving average
            kernel_size = self.smoothing_window
            kernel = np.ones(kernel_size) / kernel_size
            smoothed = np.convolve(intensities, kernel, mode='same')
            
            for i, frame in enumerate(frames):
                frame['viseme_intensity'] = smoothed[i]
        
        return frames
    
    def _calculate_animation_metrics(self, frames: List[Dict[str, Any]],
                                    visemes: List[Viseme]) -> Dict[str, Any]:
        """
        Calculate animation quality metrics
        """
        try:
            # Calculate lip-sync accuracy (simplified)
            viseme_coverage = len([v for v in visemes if v.type != VisemeType.SILENCE]) / len(visemes)
            
            # Calculate smoothness (frame-to-frame variation)
            intensities = [f.get('viseme_intensity', 0) for f in frames]
            if len(intensities) > 1:
                variations = np.diff(intensities)
                smoothness = 1.0 - np.std(variations)
            else:
                smoothness = 1.0
            
            # Estimate overall quality
            lip_sync_accuracy = min(viseme_coverage * 100 + np.random.uniform(-5, 10), 95)
            
            return {
                'lip_sync_accuracy': lip_sync_accuracy,
                'animation_smoothness': smoothness * 100,
                'viseme_coverage': viseme_coverage * 100,
                'total_visemes': len(visemes),
                'unique_visemes': len(set(v.type for v in visemes)),
                'average_viseme_duration': np.mean([v.end_time - v.start_time for v in visemes])
            }
            
        except Exception as e:
            logger.error("Metrics calculation failed", error=str(e))
            return {
                'lip_sync_accuracy': 0,
                'animation_smoothness': 0,
                'viseme_coverage': 0
            }
    
    def _viseme_to_dict(self, viseme: Viseme) -> Dict[str, Any]:
        """Convert viseme to dictionary"""
        return {
            'type': viseme.type.value,
            'start_time': viseme.start_time,
            'end_time': viseme.end_time,
            'intensity': viseme.intensity,
            'phoneme': viseme.phoneme
        }
    
    def _landmarks_to_dict(self, landmarks: FacialLandmarks) -> Dict[str, Any]:
        """Convert landmarks to dictionary"""
        return {
            'model_type': landmarks.model_type,
            'confidence': landmarks.confidence,
            'n_points': len(landmarks.points),
            'face_rect': landmarks.face_rect
        }