#!/usr/bin/env python3
"""
Debug script for Validdo authentication
Investigates the specific authentication issues with demo.validdo.com
"""

import asyncio
import sys
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class ValiddoAuthDebugger:
    def __init__(self):
        self.driver = None
        
    def initialize_browser(self, headless=False):
        """Initialize Chrome WebDriver with debugging options"""
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
        
    def analyze_page_structure(self, url):
        """Analyze the page structure to understand the login form"""
        print(f"🔍 Analyzing page structure for: {url}")
        
        self.driver.get(url)
        time.sleep(3)  # Wait for page to load completely
        
        print(f"Current URL: {self.driver.current_url}")
        print(f"Page Title: {self.driver.title}")
        
        # Find all forms
        forms = self.driver.find_elements(By.TAG_NAME, "form")
        print(f"\n📋 Found {len(forms)} form(s):")
        
        for i, form in enumerate(forms):
            action = form.get_attribute("action") or "No action specified"
            method = form.get_attribute("method") or "GET (default)"
            form_id = form.get_attribute("id") or "No ID"
            form_class = form.get_attribute("class") or "No class"
            
            print(f"  Form {i+1}:")
            print(f"    - Action: {action}")
            print(f"    - Method: {method}")
            print(f"    - ID: {form_id}")
            print(f"    - Class: {form_class}")
            
            # Find inputs in this form
            inputs = form.find_elements(By.TAG_NAME, "input")
            print(f"    - Inputs ({len(inputs)}):")
            for input_elem in inputs:
                name = input_elem.get_attribute("name") or "No name"
                input_type = input_elem.get_attribute("type") or "text"
                placeholder = input_elem.get_attribute("placeholder") or "No placeholder"
                value = input_elem.get_attribute("value") or "No value"
                print(f"      * Type: {input_type}, Name: {name}, Placeholder: {placeholder}, Value: {value}")
            
            # Find buttons in this form
            buttons = form.find_elements(By.TAG_NAME, "button")
            print(f"    - Buttons ({len(buttons)}):")
            for button in buttons:
                button_type = button.get_attribute("type") or "button"
                button_text = button.text or "No text"
                onclick = button.get_attribute("onclick") or "No onclick"
                print(f"      * Type: {button_type}, Text: {button_text}, OnClick: {onclick}")
        
    def test_form_submission(self, url, username, password):
        """Test actual form submission with the provided credentials"""
        print(f"\n🔐 Testing form submission with credentials...")
        
        self.driver.get(url)
        time.sleep(3)
        
        # Try to find username field with various selectors
        username_selectors = [
            "input[name='Email']",
            "input[type='email']",
            "input[name='username']",
            "input[name='email']",
            "input[placeholder*='email' i]",
            "input[placeholder*='Email' i]"
        ]
        
        username_element = None
        for selector in username_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and elements[0].is_displayed():
                    username_element = elements[0]
                    print(f"✅ Found username field with selector: {selector}")
                    break
            except Exception:
                continue
        
        if not username_element:
            print("❌ Could not find username field")
            return False
        
        # Try to find password field
        password_selectors = [
            "input[name='Wachtwoord']",
            "input[type='password']", 
            "input[name='password']",
            "input[placeholder*='password' i]",
            "input[placeholder*='wachtwoord' i]"
        ]
        
        password_element = None
        for selector in password_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and elements[0].is_displayed():
                    password_element = elements[0]
                    print(f"✅ Found password field with selector: {selector}")
                    break
            except Exception:
                continue
        
        if not password_element:
            print("❌ Could not find password field")
            return False
        
        # Fill in the credentials
        print(f"📝 Filling credentials...")
        username_element.clear()
        username_element.send_keys(username)
        
        password_element.clear()
        password_element.send_keys(password)
        
        print(f"✅ Credentials filled successfully")
        
        # Look for submit button or form
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:contains('Login')",
            "button:contains('Inloggen')",
            ".login-button",
            "form button"
        ]
        
        submit_element = None
        for selector in submit_selectors:
            try:
                if ":contains(" in selector:
                    # For contains selector, use XPath
                    button_text = selector.split(':contains(')[1].split(')')[0].strip("'")
                    xpath_selector = f"//button[contains(text(), '{button_text}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath_selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements and elements[0].is_displayed():
                    submit_element = elements[0]
                    print(f"✅ Found submit element with selector: {selector}")
                    break
            except Exception:
                continue
        
        if submit_element:
            # Take screenshot before submission
            self.driver.save_screenshot("/tmp/validdo_before_submit.png")
            print("📸 Screenshot saved before submission")
            
            # Check the current URL before submission
            url_before = self.driver.current_url
            print(f"URL before submission: {url_before}")
            
            # Submit the form
            print("🚀 Submitting form...")
            submit_element.click()
            
            # Wait for page to respond
            time.sleep(5)
            
            # Check what happened
            url_after = self.driver.current_url
            print(f"URL after submission: {url_after}")
            
            # Take screenshot after submission
            self.driver.save_screenshot("/tmp/validdo_after_submit.png")
            print("📸 Screenshot saved after submission")
            
            # Check for success indicators
            page_source = self.driver.page_source.lower()
            
            success_indicators = [
                "dashboard", "home", "profile", "welcome", "logout", "account"
            ]
            
            error_indicators = [
                "error", "invalid", "incorrect", "failed", "wrong", "unauthorized", "denied"
            ]
            
            found_success = any(indicator in page_source or indicator in url_after.lower() 
                              for indicator in success_indicators)
            found_error = any(indicator in page_source 
                            for indicator in error_indicators)
            
            print(f"\n📊 Submission Results:")
            print(f"  - URL changed: {'Yes' if url_before != url_after else 'No'}")
            print(f"  - Success indicators found: {'Yes' if found_success else 'No'}")
            print(f"  - Error indicators found: {'Yes' if found_error else 'No'}")
            
            if found_success and not found_error:
                print("✅ Authentication appears successful!")
                return True
            elif found_error:
                print("❌ Authentication failed - error indicators found")
                return False
            elif url_before != url_after:
                print("⚠️ URL changed but unclear if successful - may need manual verification")
                return True
            else:
                print("❌ No clear indication of success")
                return False
        else:
            # Try form submission via password field
            print("⚠️ No submit button found, trying form submission via password field")
            try:
                password_element.submit()
                time.sleep(5)
                
                url_after = self.driver.current_url
                if self.driver.current_url != url:
                    print("✅ URL changed after form submit, authentication may have succeeded")
                    return True
                else:
                    print("❌ Form submission via password field failed")
                    return False
            except Exception as e:
                print(f"❌ Form submission failed: {str(e)}")
                return False
    
    def debug_javascript_behavior(self):
        """Check for JavaScript form handling"""
        print(f"\n🔧 Debugging JavaScript behavior...")
        
        # Check for JavaScript event listeners
        script_result = self.driver.execute_script("""
            var forms = document.querySelectorAll('form');
            var result = [];
            
            for (var i = 0; i < forms.length; i++) {
                var form = forms[i];
                var formInfo = {
                    action: form.action,
                    method: form.method,
                    hasOnSubmit: form.onsubmit !== null,
                    hasEventListeners: form.onclick !== null
                };
                result.push(formInfo);
            }
            
            return result;
        """)
        
        print("JavaScript form analysis:")
        for i, form_info in enumerate(script_result):
            print(f"  Form {i+1}:")
            print(f"    - Action: {form_info['action']}")
            print(f"    - Method: {form_info['method']}")
            print(f"    - Has onSubmit: {form_info['hasOnSubmit']}")
            print(f"    - Has event listeners: {form_info['hasEventListeners']}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    """Main debugging function"""
    url = "https://demo.validdo.com/"
    username = "shaghisharifian+80@gmail.com"  # Correct credentials
    password = "TestTest@1"
    
    debugger = ValiddoAuthDebugger()
    
    try:
        print("🚀 Starting Validdo Authentication Debug Session")
        print("=" * 60)
        
        # Initialize browser (non-headless for visual debugging)
        debugger.initialize_browser(headless=False)
        
        # Step 1: Analyze page structure
        debugger.analyze_page_structure(url)
        
        # Step 2: Debug JavaScript behavior
        debugger.debug_javascript_behavior()
        
        # Step 3: Test form submission
        success = debugger.test_form_submission(url, username, password)
        
        print("\n" + "=" * 60)
        print("🎯 DEBUG SESSION SUMMARY")
        print("=" * 60)
        
        if success:
            print("✅ Authentication debugging completed successfully")
            print("The form submission appears to work correctly")
        else:
            print("❌ Authentication issues identified")
            print("Check screenshots in /tmp/ for visual verification")
        
        print("\n💡 Next steps:")
        print("1. Review the screenshots: /tmp/validdo_before_submit.png and /tmp/validdo_after_submit.png")
        print("2. Check if the form uses AJAX or JavaScript for submission")
        print("3. Verify if additional waiting time is needed after submission")
        
    except Exception as e:
        print(f"❌ Debug session failed: {str(e)}")
    finally:
        print("\n🔄 Keeping browser open for 10 seconds for manual inspection...")
        time.sleep(10)
        debugger.close()

if __name__ == "__main__":
    main()