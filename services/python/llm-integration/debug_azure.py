#!/usr/bin/env python3
"""
Debug script to test Azure OpenAI configuration and find correct deployment names
"""
import os
import asyncio
import sys
from openai import AzureOpenAI

# Add shared modules to path
sys.path.insert(0, '../shared')

async def test_azure_deployments():
    """Test different deployment names to find the correct one"""
    
    api_key = "EW78F4lIwjq3fWP1vSN0G3vv1FjwfM8eu36ZyPIoUMX8ppmJTsGDJQQJ99ALACHYHv6XJ3w3AAAAACOG4NXq"
    endpoint = "https://mozhd-m4she0ns-eastus2.cognitiveservices.azure.com/"
    
    # Common deployment names to try
    deployment_names = [
        "gpt-4",
        "gpt-35-turbo", 
        "gpt-3.5-turbo",
        "gpt4",
        "gpt35turbo",
        "mozhd-m4she0ns-eastus2",  # Original name from user
        "text-davinci-003",
        "gpt-4-32k",
        "deployment1",  # Generic names
        "deployment2"
    ]
    
    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-02-01"
    )
    
    print("🔍 Testing Azure OpenAI deployments...")
    print(f"📍 Endpoint: {endpoint}")
    print(f"🔑 API Key: {api_key[:10]}...")
    print()
    
    working_deployments = []
    
    for deployment_name in deployment_names:
        print(f"🧪 Testing deployment: {deployment_name}")
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0
            )
            print(f"✅ SUCCESS: {deployment_name} works!")
            working_deployments.append(deployment_name)
            break  # Stop at first working deployment
            
        except Exception as e:
            error_msg = str(e)
            if "DeploymentNotFound" in error_msg:
                print(f"❌ {deployment_name}: Deployment not found")
            elif "InvalidApiVersionParameter" in error_msg:
                print(f"❌ {deployment_name}: Invalid API version")
            elif "Unauthorized" in error_msg:
                print(f"❌ {deployment_name}: Unauthorized (check API key)")
            elif "quota" in error_msg.lower():
                print(f"⚠️ {deployment_name}: Rate limit/quota exceeded")
            else:
                print(f"❌ {deployment_name}: {error_msg}")
    
    print()
    if working_deployments:
        print(f"✅ Working deployments found: {', '.join(working_deployments)}")
        print(f"💡 Use deployment name: {working_deployments[0]}")
    else:
        print("❌ No working deployments found")
        print("💡 Check your Azure OpenAI resource configuration:")
        print("   - Verify the endpoint URL")
        print("   - Verify the API key") 
        print("   - Create a model deployment in Azure Portal")

if __name__ == "__main__":
    asyncio.run(test_azure_deployments())