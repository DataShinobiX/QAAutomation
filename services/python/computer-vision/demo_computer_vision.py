#!/usr/bin/env python3
"""
Computer Vision Service Demo
Demonstrates OCR, component detection, and accessibility analysis capabilities
"""
import asyncio
import os
import sys
import requests
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

class ComputerVisionDemo:
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url
    
    def create_demo_screenshot(self, filename: str) -> str:
        """Create a demo screenshot with various UI elements"""
        print(f"🎨 Creating demo screenshot: {filename}")
        
        # Create a larger, more realistic UI mockup
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to load a larger font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        except:
            font_large = font_medium = font_small = None
        
        # Header section
        draw.rectangle([0, 0, 800, 80], fill='#2c3e50')
        draw.text((20, 30), "Demo Application Dashboard", fill='white', font=font_large)
        
        # Navigation menu
        nav_items = ["Home", "Products", "Services", "Contact"]
        for i, item in enumerate(nav_items):
            x = 500 + i * 80
            draw.text((x, 35), item, fill='white', font=font_medium)
        
        # Main content area
        # Title
        draw.text((50, 120), "Welcome to Our Service", fill='#2c3e50', font=font_large)
        
        # Subtitle
        draw.text((50, 160), "This is a comprehensive platform for all your needs", fill='#7f8c8d', font=font_medium)
        
        # Buttons with different styles and sizes
        # Large primary button
        draw.rectangle([50, 200, 200, 250], fill='#3498db', outline='#2980b9')
        draw.text((100, 220), "Get Started", fill='white', font=font_medium)
        
        # Medium secondary button  
        draw.rectangle([220, 200, 340, 240], fill='#95a5a6', outline='#7f8c8d')
        draw.text((250, 215), "Learn More", fill='white', font=font_small)
        
        # Small button (accessibility issue)
        draw.rectangle([360, 210, 420, 230], fill='#e74c3c', outline='#c0392b')
        draw.text((375, 215), "Help", fill='white', font=font_small)
        
        # Input fields
        # Email input
        draw.rectangle([50, 280, 350, 320], fill='white', outline='#bdc3c7', width=2)
        draw.text((60, 295), "Enter your email address", fill='#95a5a6', font=font_small)
        
        # Password input
        draw.rectangle([50, 340, 350, 380], fill='white', outline='#bdc3c7', width=2)
        draw.text((60, 355), "••••••••", fill='#2c3e50', font=font_small)
        
        # Checkboxes
        # Terms checkbox
        draw.rectangle([50, 410, 70, 430], fill='white', outline='#2c3e50', width=2)
        draw.text((80, 415), "I agree to the terms and conditions", fill='#2c3e50', font=font_small)
        
        # Newsletter checkbox
        draw.rectangle([50, 450, 70, 470], fill='white', outline='#2c3e50', width=2)
        draw.text((15, 455), "✓", fill='#27ae60', font=font_medium)  # Checked
        draw.text((80, 455), "Subscribe to newsletter", fill='#2c3e50', font=font_small)
        
        # Dropdown menu
        draw.rectangle([400, 280, 600, 320], fill='white', outline='#bdc3c7', width=2)
        draw.text((410, 295), "Select your country", fill='#95a5a6', font=font_small)
        draw.text((570, 295), "▼", fill='#7f8c8d', font=font_small)
        
        # Information cards
        for i in range(3):
            x = 450 + i * 110
            y = 350
            
            # Card background
            draw.rectangle([x, y, x + 100, y + 120], fill='#ecf0f1', outline='#bdc3c7')
            
            # Card title
            draw.text((x + 10, y + 10), f"Feature {i+1}", fill='#2c3e50', font=font_small)
            
            # Card description
            draw.text((x + 10, y + 40), "Description of", fill='#7f8c8d', font=font_small)
            draw.text((x + 10, y + 55), "this feature", fill='#7f8c8d', font=font_small)
            
            # Card button
            draw.rectangle([x + 10, y + 85, x + 90, y + 105], fill='#3498db', outline='#2980b9')
            draw.text((x + 30, y + 92), "View", fill='white', font=font_small)
        
        # Footer
        draw.rectangle([0, 520, 800, 600], fill='#34495e')
        draw.text((50, 540), "© 2024 Demo Application. All rights reserved.", fill='#bdc3c7', font=font_small)
        draw.text((50, 560), "Privacy Policy | Terms of Service | Contact Us", fill='#95a5a6', font=font_small)
        
        # Some potential accessibility issues
        # Very small text
        draw.text((600, 450), "Terms apply*", fill='#95a5a6', font=font_small)
        
        # Low contrast text
        draw.text((50, 500), "This text has low contrast", fill='#d5d8dc', font=font_small)
        
        # Save the image
        demo_path = os.path.join(os.getcwd(), filename)
        img.save(demo_path)
        print(f"✅ Demo screenshot saved: {demo_path}")
        
        return demo_path
    
    def demonstrate_ocr(self, image_path: str):
        """Demonstrate OCR text extraction"""
        print("\n🔤 OCR Text Extraction Demo")
        print("-" * 40)
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image_file': ('demo_ui.png', f, 'image/png')}
                data = {
                    'language': 'eng',
                    'preprocess': True,
                    'engine': 'auto'
                }
                
                response = requests.post(
                    f"{self.base_url}/ocr/extract-text",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OCR Success!")
                print(f"   Engine Used: {result['engine']}")
                print(f"   Confidence: {result['confidence']:.1f}%")
                print(f"   Total Text Length: {result['character_count']} characters")
                print(f"   Word Count: {result['word_count']} words")
                print(f"   Text Regions: {len(result['bounding_boxes'])} detected")
                
                print(f"\n📝 Extracted Text (first 200 chars):")
                text = result['text'][:200] + ("..." if len(result['text']) > 200 else "")
                print(f"   \"{text}\"")
                
                if result['bounding_boxes']:
                    print(f"\n📍 Sample Text Regions:")
                    for i, bbox in enumerate(result['bounding_boxes'][:3]):
                        print(f"   {i+1}. \"{bbox['text']}\" at ({bbox['x']}, {bbox['y']}) - Confidence: {bbox['confidence']}")
                
            else:
                print(f"❌ OCR failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ OCR demo error: {e}")
    
    def demonstrate_component_detection(self, image_path: str):
        """Demonstrate UI component detection"""
        print("\n🔲 UI Component Detection Demo")
        print("-" * 40)
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image_file': ('demo_ui.png', f, 'image/png')}
                data = {
                    'component_types': 'button,input,checkbox,dropdown',
                    'confidence_threshold': 0.3
                }
                
                response = requests.post(
                    f"{self.base_url}/components/detect",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Component Detection Success!")
                print(f"   Total Components: {result['total_components']}")
                
                component_counts = result['component_count']
                print(f"\n📊 Component Summary:")
                for comp_type, count in component_counts.items():
                    print(f"   • {comp_type}: {count} detected")
                
                if result['components']:
                    print(f"\n🎯 Detailed Component Analysis:")
                    for i, comp in enumerate(result['components'][:5]):  # Show first 5
                        bbox = comp['bounding_box']
                        print(f"   {i+1}. {comp['component_type'].capitalize()}")
                        print(f"      Location: ({bbox['x']}, {bbox['y']}) - Size: {bbox['width']}x{bbox['height']}px")
                        print(f"      Confidence: {comp['confidence']:.2f}")
                        print(f"      Detection Method: {comp['properties'].get('detection_method', 'unknown')}")
                        print()
                
                metadata = result['analysis_metadata']
                print(f"📋 Analysis Metadata:")
                print(f"   Image Size: {metadata['image_size']}")
                print(f"   Detection Methods: {', '.join(metadata['detection_methods'])}")
                print(f"   Components After Filtering: {metadata['final_count']}")
                
            else:
                print(f"❌ Component detection failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Component detection demo error: {e}")
    
    def demonstrate_accessibility_analysis(self, image_path: str):
        """Demonstrate accessibility analysis"""
        print("\n♿ Accessibility Analysis Demo")
        print("-" * 40)
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image_file': ('demo_ui.png', f, 'image/png')}
                data = {
                    'include_ocr': True,
                    'include_components': True,
                    'wcag_level': 'AA'
                }
                
                response = requests.post(
                    f"{self.base_url}/accessibility/analyze",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Accessibility Analysis Complete!")
                print(f"   WCAG Level: {result['wcag_level']}")
                print(f"   Overall Score: {result['score']:.2f}/1.00")
                
                issues_by_severity = {
                    "critical": len([i for i in result['issues'] if i['severity'] == 'critical']),
                    "warning": len([i for i in result['issues'] if i['severity'] == 'warning']),
                    "info": len([i for i in result['issues'] if i['severity'] == 'info'])
                }
                
                print(f"\n🚨 Issues Summary:")
                print(f"   • Critical: {issues_by_severity['critical']} issues")
                print(f"   • Warning: {issues_by_severity['warning']} issues")
                print(f"   • Info: {issues_by_severity['info']} issues")
                
                if result['issues']:
                    print(f"\n⚠️ Accessibility Issues Found:")
                    for i, issue in enumerate(result['issues'][:5]):  # Show first 5
                        print(f"   {i+1}. [{issue['severity'].upper()}] {issue['type']}")
                        print(f"      Message: {issue['message']}")
                        print(f"      WCAG Guideline: {issue['wcag_guideline']}")
                        print(f"      Recommendation: {issue['recommendation']}")
                        print()
                
                if result['recommendations']:
                    print(f"💡 Recommendations:")
                    for i, rec in enumerate(result['recommendations'][:3]):
                        print(f"   {i+1}. {rec}")
                
                print(f"\n📊 Analysis Stats:")
                print(f"   Text Elements: {len(result['text_elements'])} analyzed")
                print(f"   UI Components: {len(result['components'])} analyzed")
                
                # Color coding for score
                if result['score'] >= 0.9:
                    score_status = "🟢 Excellent"
                elif result['score'] >= 0.7:
                    score_status = "🟡 Good"
                elif result['score'] >= 0.5:
                    score_status = "🟠 Needs Improvement"
                else:
                    score_status = "🔴 Poor"
                
                print(f"\n🎯 Accessibility Rating: {score_status}")
                
            else:
                print(f"❌ Accessibility analysis failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Accessibility analysis demo error: {e}")
    
    def check_service_health(self):
        """Check if the service is running"""
        print("🔍 Checking Computer Vision Service health...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service is healthy!")
                print(f"   Service: {data['service']} v{data['version']}")
                print(f"   Status: {data['status']}")
                return True
            else:
                print(f"❌ Service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to service: {e}")
            print(f"   Make sure the service is running on {self.base_url}")
            print(f"   Start it with: ./start.sh")
            return False
    
    def show_service_capabilities(self):
        """Show service capabilities"""
        print("\n📋 Service Capabilities")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/capabilities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                print("🔤 OCR Capabilities:")
                print(f"   Engines: {', '.join(data['ocr_engines'])}")
                print(f"   Languages: {', '.join(data['supported_languages'])}")
                
                print(f"\n🖼️ Image Processing:")
                print(f"   Formats: {', '.join(data['supported_formats'])}")
                
                print(f"\n🔲 Component Detection:")
                print(f"   Types: {', '.join(data['component_types'])}")
                
                print(f"\n♿ Accessibility Features:")
                print(f"   Features: {', '.join(data['accessibility_features'])}")
                
        except Exception as e:
            print(f"❌ Failed to get capabilities: {e}")
    
    def run_demo(self):
        """Run the complete demo"""
        print("🤖 Computer Vision Service Demo")
        print("=" * 50)
        
        # Check service health
        if not self.check_service_health():
            return False
        
        # Show capabilities
        self.show_service_capabilities()
        
        # Create demo image
        demo_image = self.create_demo_screenshot("demo_ui_screenshot.png")
        
        print(f"\n🚀 Running Computer Vision Analysis...")
        print("=" * 50)
        
        # Demonstrate each capability
        self.demonstrate_ocr(demo_image)
        time.sleep(1)
        
        self.demonstrate_component_detection(demo_image)
        time.sleep(1)
        
        self.demonstrate_accessibility_analysis(demo_image)
        
        # Cleanup
        try:
            os.unlink(demo_image)
            print(f"\n🧹 Cleaned up demo image")
        except:
            pass
        
        print("\n🎉 Computer Vision Service Demo Complete!")
        print("=" * 50)
        print("✅ Key Capabilities Demonstrated:")
        print("   • OCR text extraction with confidence scoring")
        print("   • UI component detection and classification")
        print("   • WCAG accessibility compliance analysis")
        print("   • Multi-engine processing with fallbacks")
        print("   • Comprehensive REST API endpoints")
        print("\n🚀 The Computer Vision service is ready for integration!")
        
        return True

def main():
    """Main demo function"""
    print("🎪 Computer Vision Service Live Demo")
    print("Ensure the service is running: ./start.sh")
    
    # Wait for service startup
    print("\nWaiting 3 seconds for service...")
    time.sleep(3)
    
    demo = ComputerVisionDemo()
    success = demo.run_demo()
    
    if success:
        print("\n📚 Next Steps:")
        print("   1. Integrate with other QA automation services")
        print("   2. Test with real application screenshots")
        print("   3. Configure OCR engines for production")
        print("   4. Set up accessibility monitoring workflows")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)