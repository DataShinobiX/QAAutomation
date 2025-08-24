"""
Authentication Manager Service - Main FastAPI Application
Handles web application authentication for QA automation
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, SecretStr, ValidationError
import httpx

from authentication_manager import AuthenticationManager, AuthenticationCredentials, AuthenticationResult

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Authentication Manager Service",
    description="Web application authentication and session management for QA automation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
auth_manager = None

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed logging"""
    logger.error("Request validation failed",
                 url=str(request.url),
                 method=request.method,
                 errors=exc.errors(),
                 body=await request.body())
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": exc.errors(),
            "message": "Check the request format - ensure all required fields are provided correctly"
        }
    )

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "auth-manager"
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class MFAConfig(BaseModel):
    type: str = Field(description="MFA type: 'totp', 'sms', 'manual'")
    secret: Optional[str] = Field(None, description="TOTP secret key")
    phone: Optional[str] = Field(None, description="Phone number for SMS")

class AuthRequest(BaseModel):
    url: str = Field(description="Target URL to authenticate with")
    username: str = Field(description="Username/email for authentication")
    password: SecretStr = Field(description="Password for authentication")
    auth_type: str = Field(default="form_based", description="Authentication type")
    additional_fields: Optional[Dict[str, str]] = Field(None, description="Additional form fields")
    mfa_config: Optional[MFAConfig] = Field(None, description="MFA configuration")
    timeout: int = Field(default=30, description="Authentication timeout in seconds")
    headless: bool = Field(default=True, description="Run browser in headless mode")

class SessionInfo(BaseModel):
    url: str
    success: bool
    authenticated_at: str
    expires_at: Optional[str] = None
    cookies_count: int
    auth_method: str
    session_valid: bool

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global auth_manager
    
    logger.info("Starting Authentication Manager Service")
    
    try:
        auth_manager = AuthenticationManager()
        logger.info("Authentication Manager initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize Authentication Manager Service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Authentication Manager Service")
    if auth_manager:
        auth_manager.clear_all_sessions()

def get_auth_manager() -> AuthenticationManager:
    if auth_manager is None:
        raise HTTPException(status_code=500, detail="Authentication manager not initialized")
    return auth_manager

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse()

@app.post("/authenticate")
async def authenticate_website(
    request: AuthRequest,
    auth_mgr: AuthenticationManager = Depends(get_auth_manager)
) -> Dict[str, Any]:
    """Authenticate with a web application"""
    
    logger.info("Authentication request received",
                url=request.url,
                username=request.username,
                auth_type=request.auth_type,
                password_length=len(str(request.password)) if request.password else 0)
    
    try:
        # Create credentials object
        credentials = AuthenticationCredentials(
            username=request.username,
            password=request.password.get_secret_value(),
            auth_type=request.auth_type,
            additional_fields=request.additional_fields,
            mfa_config=request.mfa_config.dict() if request.mfa_config else None
        )
        
        # Perform authentication
        result = await auth_mgr.authenticate_website(
            url=request.url,
            credentials=credentials,
            timeout=request.timeout,
            headless=request.headless
        )
        
        # Prepare response
        response_data = {
            "success": result.success,
            "authenticated_at": result.authenticated_at.isoformat(),
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
            "error_message": result.error_message,
            "session_data": {
                "current_url": result.session_data.get("current_url"),
                "page_title": result.session_data.get("page_title"),
                "cookies_count": len(result.cookies)
            },
            "cookies": result.cookies,
            "auth_metadata": result.auth_metadata
        }
        
        if result.success:
            logger.info("Authentication successful",
                       url=request.url,
                       cookies=len(result.cookies))
        else:
            logger.warning("Authentication failed",
                          url=request.url,
                          error=result.error_message)
        
        return response_data
        
    except Exception as e:
        logger.error("Authentication request failed", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/sessions")
async def list_sessions(
    auth_mgr: AuthenticationManager = Depends(get_auth_manager)
) -> Dict[str, Any]:
    """List all active authentication sessions"""
    
    try:
        sessions = []
        
        for url, session in auth_mgr.authenticated_sessions.items():
            sessions.append({
                "url": url,
                "success": session.success,
                "authenticated_at": session.authenticated_at.isoformat(),
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "cookies_count": len(session.cookies),
                "auth_method": session.auth_metadata.get("auth_method", "unknown"),
                "session_valid": auth_mgr.is_session_valid(url)
            })
        
        return {
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s["session_valid"]]),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.get("/sessions/{url:path}/cookies")
async def get_session_cookies(
    url: str,
    auth_mgr: AuthenticationManager = Depends(get_auth_manager)
) -> Dict[str, Any]:
    """Get cookies for a specific authenticated session"""
    
    try:
        cookies = auth_mgr.get_session_cookies(url)
        is_valid = auth_mgr.is_session_valid(url)
        
        return {
            "url": url,
            "session_valid": is_valid,
            "cookies_count": len(cookies),
            "cookies": cookies
        }
        
    except Exception as e:
        logger.error("Failed to get session cookies", url=url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get session cookies: {str(e)}")

@app.delete("/sessions/{url:path}")
async def clear_session(
    url: str,
    auth_mgr: AuthenticationManager = Depends(get_auth_manager)
) -> Dict[str, Any]:
    """Clear authentication session for specific URL"""
    
    try:
        was_present = url in auth_mgr.authenticated_sessions
        auth_mgr.clear_session(url)
        
        return {
            "url": url,
            "session_cleared": was_present,
            "message": f"Session for {url} cleared" if was_present else f"No session found for {url}"
        }
        
    except Exception as e:
        logger.error("Failed to clear session", url=url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

@app.delete("/sessions")
async def clear_all_sessions(
    auth_mgr: AuthenticationManager = Depends(get_auth_manager)
) -> Dict[str, Any]:
    """Clear all authentication sessions"""
    
    try:
        session_count = len(auth_mgr.authenticated_sessions)
        auth_mgr.clear_all_sessions()
        
        return {
            "sessions_cleared": session_count,
            "message": f"All {session_count} sessions cleared"
        }
        
    except Exception as e:
        logger.error("Failed to clear all sessions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear sessions: {str(e)}")

@app.get("/sessions/{url:path}/validate")
async def validate_session(
    url: str,
    auth_mgr: AuthenticationManager = Depends(get_auth_manager)
) -> Dict[str, Any]:
    """Validate if session is still active"""
    
    try:
        is_valid = auth_mgr.is_session_valid(url)
        session_exists = url in auth_mgr.authenticated_sessions
        
        response = {
            "url": url,
            "session_exists": session_exists,
            "session_valid": is_valid
        }
        
        if session_exists:
            session = auth_mgr.authenticated_sessions[url]
            response.update({
                "authenticated_at": session.authenticated_at.isoformat(),
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "auth_method": session.auth_metadata.get("auth_method", "unknown")
            })
        
        return response
        
    except Exception as e:
        logger.error("Failed to validate session", url=url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to validate session: {str(e)}")

@app.post("/test-connection")
async def test_connection(
    url: str,
    timeout: int = 10
) -> Dict[str, Any]:
    """Test connection to a URL and detect authentication requirements"""
    
    try:
        logger.info("Testing connection", url=url)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True)
        
        # Analyze response
        requires_auth = False
        auth_indicators = []
        
        # Check status codes
        if response.status_code in [401, 403]:
            requires_auth = True
            auth_indicators.append(f"HTTP {response.status_code}")
        
        # Check for login page indicators
        content = response.text.lower()
        login_keywords = ['login', 'signin', 'sign in', 'authenticate', 'password', 'username']
        
        found_keywords = [keyword for keyword in login_keywords if keyword in content]
        if found_keywords:
            requires_auth = True
            auth_indicators.extend(found_keywords)
        
        return {
            "url": url,
            "accessible": True,
            "status_code": response.status_code,
            "final_url": str(response.url),
            "requires_authentication": requires_auth,
            "auth_indicators": auth_indicators,
            "redirect_count": len(response.history),
            "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
        }
        
    except httpx.TimeoutException:
        return {
            "url": url,
            "accessible": False,
            "error": "Connection timeout",
            "requires_authentication": None
        }
    except Exception as e:
        return {
            "url": url,
            "accessible": False,
            "error": str(e),
            "requires_authentication": None
        }

@app.get("/status")
async def get_service_status():
    """Get detailed service status"""
    
    status_info = {
        "service": "auth-manager",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": {
            "auth_manager_available": auth_manager is not None,
            "active_sessions": len(auth_manager.authenticated_sessions) if auth_manager else 0,
            "supported_auth_types": ["form_based", "basic_auth", "oauth", "saml"]
        },
        "configuration": {
            "default_timeout": 30,
            "session_management": True,
            "mfa_support": True,
            "headless_mode": True
        }
    }
    
    return status_info

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Authentication Manager Service",
                host="0.0.0.0",
                port=8007)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
        log_level="info"
    )