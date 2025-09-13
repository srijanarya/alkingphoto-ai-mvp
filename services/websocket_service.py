"""
TalkingPhoto AI MVP - WebSocket Service
Real-time progress tracking and notifications
"""

import json
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Set, Optional
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request, current_app
import structlog
from redis import Redis
import jwt

logger = structlog.get_logger()


class WebSocketService:
    """
    WebSocket service for real-time video generation progress updates
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.redis_client = Redis(
            host=current_app.config.get('REDIS_HOST', 'localhost'),
            port=current_app.config.get('REDIS_PORT', 6379),
            decode_responses=True
        )
        
        # Track active connections
        self.active_connections: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.session_to_user: Dict[str, str] = {}  # session_id -> user_id
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """
        Register WebSocket event handlers
        """
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Authenticate user
                user_id = self._authenticate_connection(auth)
                if not user_id:
                    disconnect()
                    return False
                
                session_id = request.sid
                
                # Track connection
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = set()
                self.active_connections[user_id].add(session_id)
                self.session_to_user[session_id] = user_id
                
                # Join user's personal room
                join_room(f"user_{user_id}")
                
                # Send connection confirmation
                emit('connected', {
                    'message': 'Connected to video generation service',
                    'session_id': session_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                logger.info("WebSocket client connected", user_id=user_id, session_id=session_id)
                return True
                
            except Exception as e:
                logger.error("Connection failed", error=str(e))
                disconnect()
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                session_id = request.sid
                
                if session_id in self.session_to_user:
                    user_id = self.session_to_user[session_id]
                    
                    # Remove from tracking
                    if user_id in self.active_connections:
                        self.active_connections[user_id].discard(session_id)
                        if not self.active_connections[user_id]:
                            del self.active_connections[user_id]
                    
                    del self.session_to_user[session_id]
                    
                    # Leave rooms
                    leave_room(f"user_{user_id}")
                    
                    logger.info("WebSocket client disconnected", user_id=user_id, session_id=session_id)
                    
            except Exception as e:
                logger.error("Disconnection handler failed", error=str(e))
        
        @self.socketio.on('subscribe_to_video')
        def handle_subscribe(data):
            """Subscribe to video generation updates"""
            try:
                session_id = request.sid
                if session_id not in self.session_to_user:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                user_id = self.session_to_user[session_id]
                video_id = data.get('video_id')
                
                if not video_id:
                    emit('error', {'message': 'Video ID required'})
                    return
                
                # Verify user owns this video
                if not self._verify_video_ownership(user_id, video_id):
                    emit('error', {'message': 'Access denied'})
                    return
                
                # Join video-specific room
                room_name = f"video_{video_id}"
                join_room(room_name)
                
                # Send current progress
                progress = self._get_video_progress(video_id)
                emit('video_progress', {
                    'video_id': video_id,
                    'progress': progress,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                logger.info("Client subscribed to video", user_id=user_id, video_id=video_id)
                
            except Exception as e:
                logger.error("Subscribe failed", error=str(e))
                emit('error', {'message': 'Subscription failed'})
        
        @self.socketio.on('unsubscribe_from_video')
        def handle_unsubscribe(data):
            """Unsubscribe from video generation updates"""
            try:
                session_id = request.sid
                video_id = data.get('video_id')
                
                if video_id:
                    room_name = f"video_{video_id}"
                    leave_room(room_name)
                    
                    emit('unsubscribed', {'video_id': video_id})
                    
            except Exception as e:
                logger.error("Unsubscribe failed", error=str(e))
        
        @self.socketio.on('get_active_videos')
        def handle_get_active():
            """Get all active video generations for user"""
            try:
                session_id = request.sid
                if session_id not in self.session_to_user:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                user_id = self.session_to_user[session_id]
                
                # Get active videos from Redis
                active_videos = self._get_user_active_videos(user_id)
                
                emit('active_videos', {
                    'videos': active_videos,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
            except Exception as e:
                logger.error("Get active videos failed", error=str(e))
                emit('error', {'message': 'Failed to get active videos'})
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping for connection keep-alive"""
            emit('pong', {'timestamp': time.time()})
    
    def _authenticate_connection(self, auth: Dict[str, Any]) -> Optional[str]:
        """
        Authenticate WebSocket connection
        """
        try:
            if not auth or 'token' not in auth:
                return None
            
            token = auth['token']
            
            # Verify JWT token
            secret_key = current_app.config.get('JWT_SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            return payload.get('user_id')
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token in WebSocket auth")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token in WebSocket auth")
            return None
        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            return None
    
    def _verify_video_ownership(self, user_id: str, video_id: str) -> bool:
        """
        Verify user owns the video generation
        """
        try:
            # Check in Redis cache first
            ownership_key = f"video_owner:{video_id}"
            cached_owner = self.redis_client.get(ownership_key)
            
            if cached_owner:
                return cached_owner == user_id
            
            # In production, check database
            # For now, assume ownership if user is authenticated
            return True
            
        except Exception as e:
            logger.error("Ownership verification failed", error=str(e))
            return False
    
    def _get_video_progress(self, video_id: str) -> Dict[str, Any]:
        """
        Get current progress for video generation
        """
        try:
            progress_key = f"video_progress:{video_id}"
            progress_data = self.redis_client.get(progress_key)
            
            if progress_data:
                return json.loads(progress_data)
            else:
                return {
                    'percentage': 0,
                    'message': 'Initializing',
                    'status': 'pending'
                }
                
        except Exception as e:
            logger.error("Failed to get progress", error=str(e))
            return {
                'percentage': 0,
                'message': 'Error',
                'status': 'error'
            }
    
    def _get_user_active_videos(self, user_id: str) -> list:
        """
        Get all active video generations for a user
        """
        try:
            # Get from Redis set
            active_key = f"user_active_videos:{user_id}"
            video_ids = self.redis_client.smembers(active_key)
            
            videos = []
            for video_id in video_ids:
                progress = self._get_video_progress(video_id)
                if progress['percentage'] < 100:  # Still processing
                    videos.append({
                        'video_id': video_id,
                        'progress': progress
                    })
            
            return videos
            
        except Exception as e:
            logger.error("Failed to get active videos", error=str(e))
            return []
    
    def broadcast_progress(self, video_id: str, percentage: int, message: str,
                         status: str = 'processing', metadata: Dict[str, Any] = None):
        """
        Broadcast progress update to all subscribers
        """
        try:
            # Update Redis
            progress_data = {
                'percentage': percentage,
                'message': message,
                'status': status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metadata': metadata or {}
            }
            
            progress_key = f"video_progress:{video_id}"
            self.redis_client.setex(
                progress_key,
                3600,  # 1 hour TTL
                json.dumps(progress_data)
            )
            
            # Broadcast to video room
            room_name = f"video_{video_id}"
            self.socketio.emit('video_progress', {
                'video_id': video_id,
                'progress': progress_data
            }, room=room_name)
            
            # If completed or failed, remove from active set
            if status in ['completed', 'failed']:
                # Get user ID from video ownership
                ownership_key = f"video_owner:{video_id}"
                user_id = self.redis_client.get(ownership_key)
                
                if user_id:
                    active_key = f"user_active_videos:{user_id}"
                    self.redis_client.srem(active_key, video_id)
            
            logger.info("Progress broadcast", video_id=video_id, percentage=percentage)
            
        except Exception as e:
            logger.error("Progress broadcast failed", error=str(e))
    
    def notify_video_completed(self, video_id: str, user_id: str, output_url: str,
                              metadata: Dict[str, Any] = None):
        """
        Notify user that video generation is completed
        """
        try:
            # Broadcast to video room
            self.broadcast_progress(
                video_id=video_id,
                percentage=100,
                message="Video generation completed successfully",
                status='completed',
                metadata={
                    'output_url': output_url,
                    **(metadata or {})
                }
            )
            
            # Send personal notification to user
            user_room = f"user_{user_id}"
            self.socketio.emit('video_completed', {
                'video_id': video_id,
                'output_url': output_url,
                'metadata': metadata,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=user_room)
            
            logger.info("Video completion notified", video_id=video_id, user_id=user_id)
            
        except Exception as e:
            logger.error("Completion notification failed", error=str(e))
    
    def notify_video_failed(self, video_id: str, user_id: str, error_message: str):
        """
        Notify user that video generation failed
        """
        try:
            # Broadcast failure
            self.broadcast_progress(
                video_id=video_id,
                percentage=-1,
                message=f"Video generation failed: {error_message}",
                status='failed',
                metadata={'error': error_message}
            )
            
            # Send personal notification
            user_room = f"user_{user_id}"
            self.socketio.emit('video_failed', {
                'video_id': video_id,
                'error': error_message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=user_room)
            
            logger.info("Video failure notified", video_id=video_id, user_id=user_id)
            
        except Exception as e:
            logger.error("Failure notification failed", error=str(e))
    
    def track_video_generation(self, video_id: str, user_id: str):
        """
        Start tracking a new video generation
        """
        try:
            # Store ownership
            ownership_key = f"video_owner:{video_id}"
            self.redis_client.setex(ownership_key, 7200, user_id)  # 2 hours TTL
            
            # Add to user's active videos
            active_key = f"user_active_videos:{user_id}"
            self.redis_client.sadd(active_key, video_id)
            self.redis_client.expire(active_key, 7200)  # 2 hours TTL
            
            # Initialize progress
            self.broadcast_progress(
                video_id=video_id,
                percentage=0,
                message="Video generation started",
                status='pending'
            )
            
            logger.info("Started tracking video", video_id=video_id, user_id=user_id)
            
        except Exception as e:
            logger.error("Failed to track video", error=str(e))
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket connection statistics
        """
        try:
            total_users = len(self.active_connections)
            total_sessions = sum(len(sessions) for sessions in self.active_connections.values())
            
            # Get active video counts from Redis
            active_videos = 0
            for key in self.redis_client.scan_iter("video_progress:*"):
                progress_data = self.redis_client.get(key)
                if progress_data:
                    progress = json.loads(progress_data)
                    if progress.get('status') == 'processing':
                        active_videos += 1
            
            return {
                'connected_users': total_users,
                'active_sessions': total_sessions,
                'active_video_generations': active_videos,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {
                'connected_users': 0,
                'active_sessions': 0,
                'active_video_generations': 0,
                'error': str(e)
            }


class WebSocketClient:
    """
    WebSocket client for testing and external integrations
    """
    
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.connected = False
        self.callbacks = {}
    
    async def connect(self):
        """Connect to WebSocket server"""
        import socketio
        
        self.sio = socketio.AsyncClient()
        
        @self.sio.on('connect')
        async def on_connect():
            self.connected = True
            logger.info("WebSocket client connected")
        
        @self.sio.on('disconnect')
        async def on_disconnect():
            self.connected = False
            logger.info("WebSocket client disconnected")
        
        @self.sio.on('video_progress')
        async def on_progress(data):
            if 'video_progress' in self.callbacks:
                await self.callbacks['video_progress'](data)
        
        @self.sio.on('video_completed')
        async def on_completed(data):
            if 'video_completed' in self.callbacks:
                await self.callbacks['video_completed'](data)
        
        @self.sio.on('video_failed')
        async def on_failed(data):
            if 'video_failed' in self.callbacks:
                await self.callbacks['video_failed'](data)
        
        await self.sio.connect(
            self.url,
            auth={'token': self.token}
        )
    
    async def subscribe_to_video(self, video_id: str):
        """Subscribe to video generation updates"""
        if self.connected:
            await self.sio.emit('subscribe_to_video', {'video_id': video_id})
    
    async def unsubscribe_from_video(self, video_id: str):
        """Unsubscribe from video generation updates"""
        if self.connected:
            await self.sio.emit('unsubscribe_from_video', {'video_id': video_id})
    
    async def get_active_videos(self):
        """Get all active video generations"""
        if self.connected:
            await self.sio.emit('get_active_videos')
    
    def on_progress(self, callback):
        """Register progress callback"""
        self.callbacks['video_progress'] = callback
    
    def on_completed(self, callback):
        """Register completion callback"""
        self.callbacks['video_completed'] = callback
    
    def on_failed(self, callback):
        """Register failure callback"""
        self.callbacks['video_failed'] = callback
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.connected:
            await self.sio.disconnect()