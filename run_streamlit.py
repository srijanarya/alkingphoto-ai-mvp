#!/usr/bin/env python3
"""
TalkingPhoto AI MVP - Streamlit Application Launcher
Epic 4: User Experience & Interface - Production Runner

This script launches the Streamlit application with proper configuration
and error handling for production deployment.
"""

import os
import sys
import subprocess
import signal
import time
import logging
from pathlib import Path
from typing import Optional
import streamlit as st
from dotenv import load_dotenv

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streamlit_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StreamlitRunner:
    """Streamlit application runner with production features"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from environment and defaults"""
        return {
            'host': os.getenv('STREAMLIT_HOST', '0.0.0.0'),
            'port': int(os.getenv('STREAMLIT_PORT', 8501)),
            'server_max_upload_size': int(os.getenv('STREAMLIT_MAX_UPLOAD_SIZE', 50)),
            'server_max_message_size': int(os.getenv('STREAMLIT_MAX_MESSAGE_SIZE', 50)),
            'theme_primary_color': os.getenv('STREAMLIT_PRIMARY_COLOR', '#667eea'),
            'theme_background_color': os.getenv('STREAMLIT_BG_COLOR', '#ffffff'),
            'theme_secondary_background_color': os.getenv('STREAMLIT_SECONDARY_BG_COLOR', '#f0f2f6'),
            'theme_text_color': os.getenv('STREAMLIT_TEXT_COLOR', '#262730'),
            'browser_gather_usage_stats': False,
            'server_enable_cors': True,
            'server_enable_xsrf_protection': True,
            'server_file_watcher_type': 'auto',
            'logger_level': os.getenv('STREAMLIT_LOG_LEVEL', 'info'),
            'environment': os.getenv('STREAMLIT_ENV', 'development')
        }
    
    def create_config_file(self):
        """Create Streamlit configuration file"""
        config_dir = Path.home() / '.streamlit'
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / 'config.toml'
        
        config_content = f"""
[server]
port = {self.config['port']}
address = "{self.config['host']}"
maxUploadSize = {self.config['server_max_upload_size']}
maxMessageSize = {self.config['server_max_message_size']}
enableCORS = {str(self.config['server_enable_cors']).lower()}
enableXsrfProtection = {str(self.config['server_enable_xsrf_protection']).lower()}
fileWatcherType = "{self.config['server_file_watcher_type']}"

[browser]
gatherUsageStats = {str(self.config['browser_gather_usage_stats']).lower()}

[theme]
primaryColor = "{self.config['theme_primary_color']}"
backgroundColor = "{self.config['theme_background_color']}"
secondaryBackgroundColor = "{self.config['theme_secondary_background_color']}"
textColor = "{self.config['theme_text_color']}"

[logger]
level = "{self.config['logger_level']}"

[client]
showErrorDetails = {str(self.config['environment'] == 'development').lower()}
toolbarMode = "minimal"
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"Created Streamlit config at: {config_path}")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        required_packages = [
            'streamlit',
            'plotly',
            'pandas',
            'pillow',
            'requests',
            'python-dotenv'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {', '.join(missing_packages)}")
            logger.info("Please install missing packages:")
            logger.info(f"pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def check_backend_connection(self):
        """Check if Flask backend is running"""
        import requests
        
        backend_url = os.getenv('API_BASE_URL', 'http://localhost:5000/api')
        health_url = backend_url.replace('/api', '/health')
        
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                logger.info("✅ Backend connection successful")
                return True
            else:
                logger.warning(f"⚠️ Backend health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Backend not available: {str(e)}")
            logger.info("Streamlit will run in offline mode")
            return False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """Start the Streamlit application"""
        logger.info("🚀 Starting TalkingPhoto AI MVP Streamlit Application")
        
        # Pre-flight checks
        if not self.check_dependencies():
            logger.error("❌ Dependency check failed")
            return False
        
        # Check backend (optional)
        self.check_backend_connection()
        
        # Create configuration
        self.create_config_file()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Prepare command
        cmd = [
            sys.executable, '-m', 'streamlit', 'run',
            'streamlit_app.py',
            '--server.port', str(self.config['port']),
            '--server.address', self.config['host'],
            '--logger.level', self.config['logger_level']
        ]
        
        # Add environment-specific flags
        if self.config['environment'] == 'production':
            cmd.extend([
                '--server.headless', 'true',
                '--server.enableCORS', 'true',
                '--server.enableXsrfProtection', 'true'
            ])
        
        try:
            logger.info(f"Launching Streamlit on {self.config['host']}:{self.config['port']}")
            logger.info(f"Environment: {self.config['environment']}")
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor the process
            self._monitor_process()
            
        except Exception as e:
            logger.error(f"❌ Failed to start Streamlit: {str(e)}")
            return False
    
    def _monitor_process(self):
        """Monitor the Streamlit process"""
        logger.info("📊 Monitoring Streamlit process...")
        
        try:
            while True:
                # Check if process is still running
                if self.process.poll() is not None:
                    logger.error("❌ Streamlit process terminated unexpectedly")
                    break
                
                # Read output
                output = self.process.stdout.readline()
                if output:
                    # Filter and log important messages
                    if any(keyword in output.lower() for keyword in ['error', 'warning', 'exception']):
                        logger.warning(f"Streamlit: {output.strip()}")
                    elif any(keyword in output.lower() for keyword in ['running', 'started', 'listening']):
                        logger.info(f"Streamlit: {output.strip()}")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error monitoring process: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the Streamlit application"""
        if self.process:
            logger.info("🛑 Stopping Streamlit application...")
            
            try:
                # Send SIGTERM for graceful shutdown
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=10)
                    logger.info("✅ Streamlit stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if not stopped
                    logger.warning("⚠️ Force killing Streamlit process")
                    self.process.kill()
                    self.process.wait()
                
            except Exception as e:
                logger.error(f"Error stopping Streamlit: {str(e)}")
            
            self.process = None
    
    def restart(self):
        """Restart the Streamlit application"""
        logger.info("🔄 Restarting Streamlit application...")
        self.stop()
        time.sleep(2)
        self.start()
    
    def status(self):
        """Check application status"""
        if self.process and self.process.poll() is None:
            logger.info("✅ Streamlit is running")
            return True
        else:
            logger.info("❌ Streamlit is not running")
            return False


def print_startup_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║               🎬 TalkingPhoto AI MVP                          ║
    ║                                                               ║
    ║              Epic 4: User Experience & Interface             ║
    ║                                                               ║
    ║               Transform Photos into Engaging Videos          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point"""
    print_startup_banner()
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='TalkingPhoto AI MVP Streamlit Runner')
    parser.add_argument('--port', type=int, default=8501, help='Port to run on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--env', choices=['development', 'production'], 
                       default='development', help='Environment')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'],
                       default='info', help='Log level')
    parser.add_argument('--check-backend', action='store_true',
                       help='Check backend connection before starting')
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ['STREAMLIT_PORT'] = str(args.port)
    os.environ['STREAMLIT_HOST'] = args.host
    os.environ['STREAMLIT_ENV'] = args.env
    os.environ['STREAMLIT_LOG_LEVEL'] = args.log_level
    
    # Create and start runner
    runner = StreamlitRunner()
    
    # Additional backend check if requested
    if args.check_backend:
        if not runner.check_backend_connection():
            logger.error("❌ Backend check failed. Use --no-check-backend to skip.")
            return 1
    
    try:
        runner.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())