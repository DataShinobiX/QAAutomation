"""
Document Parser Service Configuration
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

try:
    from config import DocumentParserConfig
    # Create config instance
    config = DocumentParserConfig()
except ImportError:
    # Fallback configuration if shared config not available
    class FallbackConfig:
        max_file_size = 50 * 1024 * 1024  # 50MB
        upload_dir = "/tmp/uploads"
        notion_token = None
        confluence_url = None
        confluence_token = None
        host = "0.0.0.0"
        port = 8002
        debug = False
    
    config = FallbackConfig()