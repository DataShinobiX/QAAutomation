"""
Authentication Manager
Handles web application login and session management for QA automation
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
import structlog
from datetime import datetime, timedelta
import json
import base64
from urllib.parse import urlparse, urljoin
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

logger = structlog.get_logger()

class AuthenticationCredentials:
    """Secure credential storage"""
    def __init__(
        self,
        username: str,
        password: str,
        auth_type: str = "form_based",
        additional_fields: Dict[str, str] = None,
        mfa_config: Dict[str, Any] = None
    ):
        self.username = username
        self.password = password
        self.auth_type = auth_type
        self.additional_fields = additional_fields or {}
        self.mfa_config = mfa_config or {}
        self.created_at = datetime.utcnow()

class AuthenticationResult:
    """Result of authentication attempt"""
    def __init__(
        self,
        success: bool,
        session_data: Dict[str, Any] = None,
        cookies: List[Dict[str, Any]] = None,
        error_message: str = None,
        auth_metadata: Dict[str, Any] = None
    ):
        self.success = success
        self.session_data = session_data or {}
        self.cookies = cookies or []
        self.error_message = error_message
        self.auth_metadata = auth_metadata or {}
        self.authenticated_at = datetime.utcnow()
        self.expires_at = None
        
        # Set expiration if session timeout is known
        if auth_metadata and 'session_timeout' in auth_metadata:
            self.expires_at = self.authenticated_at + timedelta(
                seconds=auth_metadata['session_timeout']
            )

class AuthenticationManager:
    """Comprehensive web application authentication manager"""
    
    def __init__(self):
        self.driver = None
        self.authenticated_sessions = {}  # URL -> AuthenticationResult
        self.auth_patterns = self._load_authentication_patterns()
        
        logger.info("Authentication Manager initialized")
    
    def _load_authentication_patterns(self) -> Dict[str, Any]:
        """Load common authentication patterns and selectors"""
        return {
            "login_form_selectors": [
                "form[action*='login']",
                "form[id*='login']",
                "form[class*='login']",
                "form[action*='auth']",
                "form[action*='signin']",
                "form[id*='signin']",
                ".login-form",
                "#login-form",
                ".auth-form",
                ".signin-form"
            ],
            
            "username_selectors": [
                "input[name='Email']",  # Validdo specific
                "input[name='username']",
                "input[name='email']",
                "input[name='user']",
                "input[name='login']",
                "input[id='username']",
                "input[id='email']",
                "input[id='user']",
                "input[id='login']",
                "input[type='email']",
                "input[placeholder*='username' i]",
                "input[placeholder*='email' i]",
                "input[placeholder*='user' i]"
            ],
            
            "password_selectors": [
                "input[name='Wachtwoord']",  # Validdo specific (Dutch for password)
                "input[type='password']",  # Most reliable selector for password fields
                "input[name='password']",
                "input[name='pass']",
                "input[name='pwd']",
                "input[id='password']",
                "input[id='pass']",
                "input[id='pwd']",
                "input[placeholder*='password' i]",
                "input[placeholder*='wachtwoord' i]",  # Dutch
                # React-specific selectors - fields might be deeply nested
                ".login-form input[type='password']",
                ".auth-form input[type='password']",
                ".signin-form input[type='password']",
                "form input[type='password']",
                # Broader selectors for dynamically generated fields
                "*[name='Wachtwoord']",
                "*[type='password']"
            ],
            
            "submit_selectors": [
                "input[type='submit']",
                "button[type='submit']",
                "button[id*='login']",
                "button[class*='login']",
                "button[id*='signin']",
                "button[class*='signin']",
                ".login-button",
                ".signin-button",
                ".auth-button",
                "input[value*='Login' i]",
                "input[value*='Sign' i]",
                "button:contains('Login')",
                "button:contains('Sign In')",
                "button:contains('Log In')"
            ],
            
            "success_indicators": [
                # URL patterns
                "dashboard", "home", "profile", "account", "welcome",
                # Element presence
                "logout", "sign out", "user menu", "profile menu"
            ],
            
            "error_indicators": [
                "error", "invalid", "incorrect", "failed", "wrong",
                "unauthorized", "forbidden", "denied"
            ],
            
            "mfa_indicators": [
                "verification", "2fa", "two-factor", "authenticator",
                "code", "token", "otp", "sms"
            ]
        }
    
    async def authenticate_website(
        self,
        url: str,
        credentials: AuthenticationCredentials,
        timeout: int = 30,
        headless: bool = True
    ) -> AuthenticationResult:
        """
        Authenticate with a web application
        
        Args:
            url: Target URL to authenticate with
            credentials: Authentication credentials
            timeout: Maximum time to wait for authentication
            headless: Whether to run browser in headless mode
        """
        logger.info("Starting authentication process",
                   url=url,
                   auth_type=credentials.auth_type,
                   username=credentials.username)
        
        try:
            # Check if already authenticated
            if url in self.authenticated_sessions:
                session = self.authenticated_sessions[url]
                if session.expires_at and session.expires_at > datetime.utcnow():
                    logger.info("Using existing valid session", url=url)
                    return session
            
            # Initialize browser
            await self._initialize_browser(headless=headless)
            
            # Navigate to URL
            self.driver.get(url)
            
            # Detect authentication method
            auth_method = await self._detect_authentication_method(url)
            
            # Perform authentication based on detected method
            if auth_method == "form_based":
                result = await self._authenticate_form_based(credentials, timeout)
            elif auth_method == "oauth":
                result = await self._authenticate_oauth(credentials, timeout)
            elif auth_method == "saml":
                result = await self._authenticate_saml(credentials, timeout)
            elif auth_method == "basic_auth":
                result = await self._authenticate_basic_auth(url, credentials)
            else:
                result = await self._authenticate_generic(credentials, timeout)
            
            # Store session if successful
            if result.success:
                self.authenticated_sessions[url] = result
                logger.info("Authentication successful", 
                           url=url, 
                           session_cookies=len(result.cookies))
            else:
                logger.error("Authentication failed", 
                           url=url, 
                           error=result.error_message)
            
            return result
            
        except Exception as e:
            logger.error("Authentication process failed", url=url, error=str(e))
            return AuthenticationResult(
                success=False,
                error_message=f"Authentication process failed: {str(e)}"
            )
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    async def _initialize_browser(self, headless: bool = True):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    async def _detect_authentication_method(self, url: str) -> str:
        """Detect the authentication method used by the website"""
        try:
            # Check for common authentication patterns
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            # OAuth detection
            if any(pattern in current_url or pattern in page_source for pattern in 
                   ['oauth', 'auth0', 'google', 'microsoft', 'github', 'facebook']):
                return "oauth"
            
            # SAML detection
            if any(pattern in current_url or pattern in page_source for pattern in
                   ['saml', 'sso', 'adfs', 'okta', 'ping']):
                return "saml"
            
            # Basic auth detection (browser prompt)
            if "401" in str(self.driver.execute_script("return document.readyState")):
                return "basic_auth"
            
            # Form-based authentication (most common)
            login_forms = self.driver.find_elements(By.CSS_SELECTOR, 
                                                   ", ".join(self.auth_patterns["login_form_selectors"]))
            if login_forms:
                return "form_based"
            
            return "generic"
            
        except Exception as e:
            logger.warning("Failed to detect authentication method", error=str(e))
            return "generic"
    
    async def _authenticate_form_based(
        self,
        credentials: AuthenticationCredentials,
        timeout: int
    ) -> AuthenticationResult:
        """Authenticate using form-based login"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            # Detect if this is a React/SPA application
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            is_react_app = (
                "validdo.com" in current_url or
                "react" in page_source or
                "noscript" in page_source and "enable javascript" in page_source or
                any(indicator in page_source for indicator in ["__react", "_react_", "react-dom"])
            )
            
            if is_react_app:
                logger.info("Detected React/SPA application - using enhanced element detection")
                # Wait longer for React components to fully render
                await asyncio.sleep(3)
            
            # Find login form elements with React-aware waiting
            username_element = await self._find_element_by_selectors(
                self.auth_patterns["username_selectors"],
                wait_time=15 if is_react_app else 10,
                react_app=is_react_app
            )
            password_element = await self._find_element_by_selectors(
                self.auth_patterns["password_selectors"],
                wait_time=15 if is_react_app else 10,
                react_app=is_react_app
            )
            
            if not username_element or not password_element:
                error_details = []
                if not username_element:
                    error_details.append("username field")
                if not password_element:
                    error_details.append("password field")
                
                # For React apps, try additional debugging
                if is_react_app and not password_element:
                    logger.warning("Password field not found in React app - checking for dynamic rendering")
                    
                    # Try to trigger password field rendering by interacting with username field
                    if username_element:
                        try:
                            username_element.click()
                            username_element.send_keys("test")  # Temporary input to trigger field rendering
                            await asyncio.sleep(2)  # Wait for React state updates
                            
                            # Try finding password field again
                            password_element = await self._find_element_by_selectors(
                                self.auth_patterns["password_selectors"],
                                wait_time=5,
                                react_app=True
                            )
                            
                            if password_element:
                                logger.info("Password field found after interaction trigger")
                                username_element.clear()  # Clear the test input
                            else:
                                logger.warning("Password field still not found after interaction trigger")
                        except Exception as e:
                            logger.warning(f"Error during React field detection: {e}")
                
                if not username_element or not password_element:
                    return AuthenticationResult(
                        success=False,
                        error_message=f"Could not find {' and '.join(error_details)} in {'React app' if is_react_app else 'form'}"
                    )
            
            # Fill credentials
            username_element.clear()
            username_element.send_keys(credentials.username)
            
            password_element.clear()
            password_element.send_keys(credentials.password)
            
            # Handle additional fields (like domain, company code, etc.)
            for field_name, field_value in credentials.additional_fields.items():
                try:
                    field_element = self.driver.find_element(
                        By.CSS_SELECTOR, f"input[name='{field_name}'], input[id='{field_name}']"
                    )
                    field_element.clear()
                    field_element.send_keys(field_value)
                except NoSuchElementException:
                    logger.warning(f"Additional field not found: {field_name}")
            
            # Submit form
            submit_element = await self._find_element_by_selectors(
                self.auth_patterns["submit_selectors"],
                wait_time=10 if is_react_app else 5,
                react_app=is_react_app
            )
            
            # Check if this is a GET method form (likely React/JavaScript-based)
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            is_get_form = False
            
            for form in form_elements:
                method = (form.get_attribute("method") or "get").lower()
                if method == "get":
                    is_get_form = True
                    logger.info("Detected GET method form - likely JavaScript/React authentication")
                    break
            
            current_url = self.driver.current_url.lower()
            
            # Special handling for JavaScript-based forms (GET method or Validdo)
            if is_get_form or "validdo.com" in current_url:
                logger.info("Applying JavaScript-based form authentication handling")
                
                if submit_element:
                    # First try: Standard click
                    submit_element.click()
                    await asyncio.sleep(3)
                    
                    # Check if we're still on login page
                    if "login" in self.driver.current_url.lower():
                        logger.info("Still on login page after click, trying JavaScript submission")
                        
                        # Second try: JavaScript click to bypass any event handlers
                        try:
                            self.driver.execute_script("arguments[0].click();", submit_element)
                            await asyncio.sleep(3)
                        except Exception as e:
                            logger.warning(f"JavaScript click failed: {e}")
                        
                        # Third try: Submit via form if still on login page
                        if "login" in self.driver.current_url.lower():
                            logger.info("Trying form submission via JavaScript")
                            try:
                                # Find the form and submit it programmatically
                                form_element = submit_element.find_element(By.XPATH, "./ancestor::form")
                                self.driver.execute_script("arguments[0].submit();", form_element)
                                await asyncio.sleep(3)
                            except Exception as e:
                                logger.warning(f"JavaScript form submit failed: {e}")
                        
                        # Fourth try: Press Enter on password field
                        if "login" in self.driver.current_url.lower():
                            logger.info("Trying Enter key on password field")
                            try:
                                from selenium.webdriver.common.keys import Keys
                                password_element.send_keys(Keys.RETURN)
                                await asyncio.sleep(3)
                            except Exception as e:
                                logger.warning(f"Enter key submission failed: {e}")
                    
                    # Wait longer for AJAX responses
                    await asyncio.sleep(5)
                else:
                    logger.warning("No submit button found, trying password field submission")
                    try:
                        from selenium.webdriver.common.keys import Keys
                        password_element.send_keys(Keys.RETURN)
                        await asyncio.sleep(5)
                    except Exception as e:
                        logger.warning(f"Password field submission failed: {e}")
            else:
                # Standard form handling for other sites
                if submit_element:
                    submit_element.click()
                else:
                    # Try form submission
                    password_element.submit()
                
                # Wait for navigation and check success
                await asyncio.sleep(2)  # Give page time to load
            
            # Check for MFA requirement
            if await self._is_mfa_required():
                mfa_result = await self._handle_mfa(credentials.mfa_config, timeout)
                if not mfa_result:
                    return AuthenticationResult(
                        success=False,
                        error_message="MFA verification failed"
                    )
            
            # Verify authentication success
            success, error_msg = await self._verify_authentication_success()
            
            if success:
                # Collect session data
                cookies = [
                    {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie.get("path", "/"),
                        "secure": cookie.get("secure", False),
                        "httpOnly": cookie.get("httpOnly", False)
                    }
                    for cookie in self.driver.get_cookies()
                ]
                
                session_data = {
                    "current_url": self.driver.current_url,
                    "page_title": self.driver.title,
                    "local_storage": self.driver.execute_script(
                        "return JSON.stringify(localStorage);"
                    )
                }
                
                return AuthenticationResult(
                    success=True,
                    session_data=session_data,
                    cookies=cookies,
                    auth_metadata={
                        "auth_method": "form_based",
                        "login_url": self.driver.current_url,
                        "session_timeout": 3600  # Default 1 hour
                    }
                )
            else:
                return AuthenticationResult(
                    success=False,
                    error_message=error_msg or "Authentication verification failed"
                )
            
        except TimeoutException:
            return AuthenticationResult(
                success=False,
                error_message="Authentication timeout - page took too long to respond"
            )
        except Exception as e:
            return AuthenticationResult(
                success=False,
                error_message=f"Form-based authentication failed: {str(e)}"
            )
    
    async def _find_element_by_selectors(self, selectors: List[str], wait_time: int = 10, react_app: bool = False):
        """Find element using multiple CSS selectors with enhanced waiting for React apps"""
        
        if react_app:
            # For React apps, wait longer and check multiple times
            max_attempts = 5
            wait_between_attempts = 2
        else:
            max_attempts = 2
            wait_between_attempts = 1
        
        for attempt in range(max_attempts):
            for selector in selectors:
                try:
                    # Use WebDriverWait for more reliable element detection
                    wait = WebDriverWait(self.driver, wait_time)
                    
                    # Wait for element to be present and visible
                    elements = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # Check if any element is actually visible and interactable
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                logger.info(f"Found element with selector: {selector}")
                                return element
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            # If not found and this is a React app, wait and try again
            if react_app and attempt < max_attempts - 1:
                logger.info(f"React app: Waiting {wait_between_attempts}s before retry {attempt + 2}/{max_attempts}")
                await asyncio.sleep(wait_between_attempts)
        
        logger.warning(f"Could not find element with any of the selectors: {selectors}")
        return None
    
    async def _is_mfa_required(self) -> bool:
        """Check if MFA/2FA is required"""
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            for indicator in self.auth_patterns["mfa_indicators"]:
                if indicator in page_source or indicator in current_url:
                    return True
            
            # Check for common MFA elements
            mfa_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "input[name*='code'], input[name*='token'], input[name*='otp'], "
                "input[placeholder*='code' i], input[placeholder*='token' i]"
            )
            
            return len(mfa_elements) > 0
            
        except Exception:
            return False
    
    async def _handle_mfa(self, mfa_config: Dict[str, Any], timeout: int) -> bool:
        """Handle Multi-Factor Authentication"""
        try:
            if not mfa_config:
                logger.warning("MFA required but no configuration provided")
                return False
            
            mfa_type = mfa_config.get("type", "manual")
            
            if mfa_type == "totp":
                # Time-based OTP (like Google Authenticator)
                secret = mfa_config.get("secret")
                if secret:
                    import pyotp
                    totp = pyotp.TOTP(secret)
                    code = totp.now()
                    
                    # Find MFA input field
                    code_element = await self._find_element_by_selectors([
                        "input[name*='code']",
                        "input[name*='token']", 
                        "input[name*='otp']",
                        "input[placeholder*='code' i]"
                    ])
                    
                    if code_element:
                        code_element.clear()
                        code_element.send_keys(code)
                        
                        # Submit
                        submit_element = await self._find_element_by_selectors(
                            self.auth_patterns["submit_selectors"]
                        )
                        if submit_element:
                            submit_element.click()
                        
                        await asyncio.sleep(3)
                        return True
            
            elif mfa_type == "sms":
                # SMS-based OTP - would require external SMS service integration
                logger.warning("SMS MFA not yet implemented")
                return False
            
            elif mfa_type == "manual":
                # Manual input - pause and wait for user
                logger.info("Manual MFA required - waiting for user input")
                
                # Wait for page to change (indicating MFA completion)
                current_url = self.driver.current_url
                wait_time = 0
                max_wait = timeout
                
                while wait_time < max_wait:
                    await asyncio.sleep(5)
                    wait_time += 5
                    
                    if self.driver.current_url != current_url:
                        return True
                
                return False
            
            return False
            
        except Exception as e:
            logger.error("MFA handling failed", error=str(e))
            return False
    
    async def _verify_authentication_success(self) -> Tuple[bool, Optional[str]]:
        """Verify if authentication was successful"""
        try:
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()
            
            # Special handling for React/JavaScript-based sites (including Validdo)
            is_react_site = "validdo.com" in current_url or any(
                indicator in page_source for indicator in ["react", "javascript", "spa"]
            )
            
            if is_react_site:
                logger.info("Using React/SPA-specific authentication verification")
                
                # Wait a bit longer for React state updates
                await asyncio.sleep(2)
                
                # Re-fetch current state after waiting
                current_url = self.driver.current_url.lower()
                page_source = self.driver.page_source.lower()
                
                # Check if we're redirected away from login page
                if "login" not in current_url:
                    logger.info("React authentication successful - redirected from login page")
                    return True, None
                
                # Check for success indicators in React apps
                react_success_indicators = [
                    "dashboard", "home", "main", "app", "workspace", "account", 
                    "portal", "admin", "user", "profile", "settings"
                ]
                
                for indicator in react_success_indicators:
                    if indicator in current_url or indicator in page_source:
                        logger.info(f"React authentication successful - found indicator: {indicator}")
                        return True, None
                
                # Check for logout or user menu elements (more comprehensive)
                logout_selectors = [
                    "a[href*='logout']", "button[onclick*='logout']", ".logout", "#logout",
                    ".user-menu", ".profile-menu", ".user-dropdown", "[data-testid*='user']",
                    "[data-testid*='logout']", "[aria-label*='user']", "[aria-label*='logout']",
                    ".avatar", ".user-avatar", ".profile-avatar"
                ]
                
                for selector in logout_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            logger.info(f"React authentication successful - found logout/user element: {selector}")
                            return True, None
                    except Exception:
                        continue
                
                # Check if login form is no longer visible (React might hide it)
                login_form_visible = False
                try:
                    login_forms = self.driver.find_elements(By.CSS_SELECTOR, "form")
                    for form in login_forms:
                        if form.is_displayed():
                            form_class = (form.get_attribute("class") or "").lower()
                            form_action = (form.get_attribute("action") or "").lower()
                            if "login" in form_class or "login" in form_action:
                                login_form_visible = True
                                break
                except Exception:
                    pass
                
                if not login_form_visible:
                    logger.info("React authentication may be successful - no visible login form")
                    return True, None
                
                # Check for React-specific error indicators
                react_error_indicators = [
                    "incorrect", "invalid", "error", "failed", "wrong", "unauthorized",
                    "ongeldig", "fout", "onjuist",  # Dutch
                    "authentication failed", "login failed", "credentials"
                ]
                
                # Also check for error states in common React error elements
                error_selectors = [
                    ".error", ".alert", ".notification", ".toast", ".message",
                    "[role='alert']", "[data-testid*='error']", ".text-red", ".text-danger"
                ]
                
                for selector in error_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                element_text = element.text.lower()
                                for error_indicator in react_error_indicators:
                                    if error_indicator in element_text:
                                        return False, f"React authentication failed - found error: {error_indicator}"
                    except Exception:
                        continue
                
                # Check page source for errors
                for error_indicator in react_error_indicators:
                    if error_indicator in page_source:
                        return False, f"React authentication failed - found error indicator: {error_indicator}"
                
                # If we're still on login page but no clear errors, wait a bit more and check again
                logger.info("React authentication status unclear - waiting for state changes")
                await asyncio.sleep(3)
                
                # Final check after additional waiting
                final_url = self.driver.current_url.lower()
                if "login" not in final_url:
                    logger.info("React authentication successful after additional wait")
                    return True, None
                
                logger.warning("React authentication status unclear - still on login page after extended wait")
                return False, "Still on login page - authentication may have failed or requires manual verification"
            
            # Standard verification for other sites
            # Check for error indicators first
            for error_indicator in self.auth_patterns["error_indicators"]:
                if error_indicator in page_source or error_indicator in page_title:
                    return False, f"Authentication failed - found error indicator: {error_indicator}"
            
            # Check for success indicators
            for success_indicator in self.auth_patterns["success_indicators"]:
                if success_indicator in current_url or success_indicator in page_source:
                    return True, None
            
            # Check if URL changed significantly (usually indicates success)
            if not any(term in current_url for term in ["login", "signin", "auth"]):
                return True, None
            
            # Check for logout elements (indicates successful login)
            logout_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a[href*='logout'], button[onclick*='logout'], .logout, #logout"
            )
            if logout_elements:
                return True, None
            
            return False, "Could not verify authentication success"
            
        except Exception as e:
            return False, f"Authentication verification failed: {str(e)}"
    
    async def _authenticate_oauth(self, credentials: AuthenticationCredentials, timeout: int) -> AuthenticationResult:
        """Handle OAuth authentication"""
        # OAuth authentication would require specific provider handling
        # This is a placeholder for OAuth implementation
        return AuthenticationResult(
            success=False,
            error_message="OAuth authentication not yet implemented"
        )
    
    async def _authenticate_saml(self, credentials: AuthenticationCredentials, timeout: int) -> AuthenticationResult:
        """Handle SAML authentication"""
        # SAML authentication would require SAML library integration
        return AuthenticationResult(
            success=False,
            error_message="SAML authentication not yet implemented"
        )
    
    async def _authenticate_basic_auth(self, url: str, credentials: AuthenticationCredentials) -> AuthenticationResult:
        """Handle HTTP Basic Authentication"""
        try:
            # Parse URL and add credentials
            parsed_url = urlparse(url)
            auth_url = f"{parsed_url.scheme}://{credentials.username}:{credentials.password}@{parsed_url.netloc}{parsed_url.path}"
            
            # Test authentication with requests
            response = requests.get(auth_url, timeout=10)
            
            if response.status_code == 200:
                # Navigate browser to authenticated URL
                self.driver.get(auth_url)
                
                cookies = [
                    {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"]
                    }
                    for cookie in self.driver.get_cookies()
                ]
                
                return AuthenticationResult(
                    success=True,
                    session_data={"current_url": self.driver.current_url},
                    cookies=cookies,
                    auth_metadata={"auth_method": "basic_auth"}
                )
            else:
                return AuthenticationResult(
                    success=False,
                    error_message=f"Basic authentication failed - HTTP {response.status_code}"
                )
                
        except Exception as e:
            return AuthenticationResult(
                success=False,
                error_message=f"Basic authentication error: {str(e)}"
            )
    
    async def _authenticate_generic(self, credentials: AuthenticationCredentials, timeout: int) -> AuthenticationResult:
        """Generic authentication fallback"""
        # Try form-based authentication as fallback
        return await self._authenticate_form_based(credentials, timeout)
    
    def get_session_cookies(self, url: str) -> List[Dict[str, Any]]:
        """Get stored session cookies for URL"""
        if url in self.authenticated_sessions:
            return self.authenticated_sessions[url].cookies
        return []
    
    def is_session_valid(self, url: str) -> bool:
        """Check if stored session is still valid"""
        if url not in self.authenticated_sessions:
            return False
        
        session = self.authenticated_sessions[url]
        if session.expires_at and session.expires_at <= datetime.utcnow():
            return False
        
        return session.success
    
    def clear_session(self, url: str):
        """Clear stored session for URL"""
        if url in self.authenticated_sessions:
            del self.authenticated_sessions[url]
    
    def clear_all_sessions(self):
        """Clear all stored sessions"""
        self.authenticated_sessions.clear()