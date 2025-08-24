#!/usr/bin/env python3
"""
Test script for Figma Integration Service
"""
import asyncio
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import FigmaServiceConfig
from figma_client import FigmaClient
from figma_analyzer import FigmaAnalyzer
from test_generator import UITestGenerator


async def test_figma_service():
    """Test Figma service functionality"""
    print("🧪 Testing Figma Integration Service...")
    
    # Initialize configuration
    config = FigmaServiceConfig()
    print(f"📋 File Key: {config.figma_file_key}")
    print(f"🔑 Token: {config.figma_token[:20]}...")
    
    # Test Figma client
    print("\n1️⃣ Testing Figma API connection...")
    client = FigmaClient(config)
    
    try:
        await client.test_connection()
        print("✅ Figma API connection successful!")
    except Exception as e:
        print(f"❌ Figma API connection failed: {e}")
        return False
    
    # Test file retrieval
    print("\n2️⃣ Testing file retrieval...")
    try:
        file_data = await client.get_file(config.figma_file_key)
        print(f"✅ File retrieved: {file_data.get('name', 'Unknown')}")
        print(f"   📊 Document has {len(file_data.get('document', {}).get('children', []))} pages")
    except Exception as e:
        print(f"❌ File retrieval failed: {e}")
        return False
    
    # Test analysis
    print("\n3️⃣ Testing design analysis...")
    analyzer = FigmaAnalyzer(config)
    
    try:
        design = await analyzer.analyze_file(file_data)
        print(f"✅ Analysis completed!")
        print(f"   🖼️  Frames found: {len(design.frames)}")
        print(f"   🎨 Styles extracted: {len(design.styles)}")
        
        if design.frames:
            first_frame = design.frames[0]
            print(f"   📐 First frame: {first_frame.name} ({first_frame.width}x{first_frame.height})")
            print(f"   🧩 Components in first frame: {len(first_frame.components)}")
            
    except Exception as e:
        print(f"❌ Design analysis failed: {e}")
        return False
    
    # Test test generation
    print("\n4️⃣ Testing UI test generation...")
    generator = UITestGenerator(config)
    
    try:
        test_suite = await generator.generate_ui_tests(design, "https://example.com")
        print(f"✅ Test generation completed!")
        print(f"   🧪 UI tests generated: {len(test_suite.ui_tests)}")
        print(f"   📝 Test suite: {test_suite.name}")
        
        if test_suite.ui_tests:
            print(f"   🔍 Sample tests:")
            for i, test in enumerate(test_suite.ui_tests[:3]):
                print(f"      {i+1}. {test.component_name} - {test.test_type} ({test.selector})")
                
    except Exception as e:
        print(f"❌ Test generation failed: {e}")
        return False
    
    # Test image retrieval
    print("\n5️⃣ Testing image retrieval...")
    try:
        images = await client.get_images(config.figma_file_key, [])
        print(f"✅ Images retrieved!")
        print(f"   🖼️  Image URLs: {len(images.get('images', {}))}")
        
        if images.get('images'):
            first_image = list(images['images'].items())[0]
            print(f"   🔗 Sample image: {first_image[0]} -> {first_image[1][:50]}...")
            
    except Exception as e:
        print(f"❌ Image retrieval failed: {e}")
        return False
    
    print("\n🎉 All Figma service tests passed!")
    return True


async def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 FIGMA INTEGRATION SERVICE TEST")
    print("=" * 60)
    
    try:
        success = await test_figma_service()
        if success:
            print("\n✅ Figma Integration Service is working correctly!")
            exit(0)
        else:
            print("\n❌ Figma Integration Service tests failed!")
            exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())