#!/bin/bash

echo "Testing the /workflows/complete-qa endpoint..."

# Test the complete-qa endpoint
curl -X POST http://localhost:8008/workflows/complete-qa \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://demo.validdo.com/signup",
    "figma_file_key": "SL2zhCoS31dtNI5YRwti2F",
    "credentials": {
      "username": "demo@example.com",
      "password": "demopass"
    },
    "user_stories": [
      "As a user, I want to sign up quickly",
      "As a user, I want clear validation messages"
    ],
    "business_requirements": [
      "Sign up form must be accessible", 
      "Form validation should be real-time"
    ],
    "test_scope": "full_analysis",
    "include_accessibility": true,
    "include_performance": true
  }'