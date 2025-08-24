#!/usr/bin/env python3
"""
NLP Processing Service Test Suite
Tests text analysis, entity extraction, and similarity analysis functionality
"""
import asyncio
import os
import sys
import time
import json
from pathlib import Path
import requests

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

class NLPServiceTester:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.test_texts = {}
        
    def create_test_texts(self):
        """Create various test texts for different scenarios"""
        print("📝 Creating test texts...")
        
        self.test_texts = {
            "requirements_doc": """
            User Story US-001: As a logged-in user, I want to view my account dashboard 
            so that I can see my profile information and recent activities.
            
            Acceptance Criteria:
            - The dashboard must display user's name, email, and profile picture
            - Recent activities should show last 10 actions with timestamps
            - Page should load within 2 seconds
            - All personal information must be encrypted during transmission
            
            Technical Requirements:
            REQ-001: The system shall support up to 10,000 concurrent users
            REQ-002: API endpoint /api/v1/dashboard must return JSON response
            REQ-003: Database table user_profiles.personal_info must be indexed
            """,
            
            "bug_report": """
            BUG-2024-001: Login form validation error
            
            When users enter an invalid email format on the login page,
            the system displays a generic error message instead of specific
            validation feedback. This causes confusion and poor user experience.
            
            Steps to reproduce:
            1. Navigate to login page at /login
            2. Enter 'invalid-email' in email field
            3. Click submit button
            
            Expected: Specific message "Please enter a valid email address"
            Actual: Generic message "Login failed"
            
            Reported by: John Doe (john@example.com)
            Priority: Medium
            Component: Authentication
            """,
            
            "test_case": """
            TEST-001: User Login Functionality Test
            
            Objective: Verify that users can successfully log in with valid credentials
            
            Preconditions:
            - Test user account exists with email 'testuser@example.com'
            - Password is 'TestPass123!'
            - Login page is accessible
            
            Test Steps:
            1. Open browser and navigate to https://app.example.com/login
            2. Enter valid email address in email field
            3. Enter correct password in password field  
            4. Click 'Sign In' button
            
            Expected Results:
            - User is redirected to dashboard page
            - Welcome message displays user's name
            - Navigation menu shows all authorized options
            - Session timeout is set to 30 minutes
            """,
            
            "technical_spec": """
            API Specification: User Authentication Service v2.1
            
            Overview:
            The Authentication Service provides secure user login and session management
            capabilities using JWT tokens and OAuth 2.0 integration.
            
            Endpoints:
            POST /auth/login - User authentication
            POST /auth/logout - Session termination  
            GET /auth/profile - Retrieve user profile
            PUT /auth/profile - Update user information
            
            Security:
            - All endpoints require HTTPS (TLS 1.3)
            - JWT tokens expire after 24 hours
            - Rate limiting: 100 requests per minute per IP
            - Input validation using JSON schema
            
            Database Tables:
            - users: id, email, password_hash, created_at
            - sessions: token_id, user_id, expires_at, ip_address
            
            Configuration:
            JWT_SECRET=super_secret_key_2024
            SESSION_TIMEOUT=1440
            """,
            
            "user_feedback": """
            Great product! I love the new dashboard design. It's much cleaner
            and easier to navigate than the previous version. The loading speed
            has improved significantly - pages now load almost instantly.
            
            However, I did notice a few issues:
            - The search function sometimes doesn't find results even when I know they exist
            - Mobile version could use better responsive design
            - Would love to see dark mode option added
            
            Overall rating: 4.5/5 stars. Keep up the excellent work!
            
            Contact: happy.customer@email.com
            Date: 2024-01-15
            """,
            
            "duplicate_text_1": """
            The user authentication system provides secure login functionality
            with password validation and session management capabilities.
            """,
            
            "duplicate_text_2": """
            The user authentication system offers secure login functionality
            with password validation and session management features.
            """,
            
            "similar_text": """
            Our authentication module ensures secure user access through
            credential verification and active session tracking.
            """
        }
        
        print(f"✅ Created {len(self.test_texts)} test texts")
    
    def test_health_check(self):
        """Test health check endpoint"""
        print("\n🔍 Testing health check...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Service: {data['service']} v{data['version']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_capabilities(self):
        """Test capabilities endpoint"""
        print("\n📋 Testing service capabilities...")
        
        try:
            response = requests.get(f"{self.base_url}/capabilities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Capabilities retrieved:")
                print(f"   Text Analysis Features: {len(data['text_analysis_features'])} available")
                print(f"   Entity Types: {len(data['entity_types'])} supported")
                print(f"   Similarity Algorithms: {data['similarity_algorithms']}")
                print(f"   Languages: {data['supported_languages']}")
                return True
            else:
                print(f"❌ Capabilities test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Capabilities error: {e}")
            return False
    
    def test_text_analysis(self):
        """Test comprehensive text analysis"""
        print("\n📊 Testing text analysis...")
        
        test_text = self.test_texts["requirements_doc"]
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze/text",
                json={
                    "text": test_text,
                    "include_entities": True,
                    "include_sentiment": True,
                    "include_readability": True,
                    "include_keywords": True,
                    "include_linguistic_features": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Text analysis successful!")
                print(f"   Language: {result['language']}")
                print(f"   Word Count: {result['text_statistics']['word_count']}")
                print(f"   Entities Found: {len(result['entities'])}")
                print(f"   Keywords: {len(result['keywords'])}")
                print(f"   Sentences: {len(result['sentences'])}")
                
                # Show sample entities
                if result['entities']:
                    print(f"   Sample Entities:")
                    for entity in result['entities'][:3]:
                        print(f"     • {entity['text']} ({entity['label']})")
                
                # Show sample keywords  
                if result['keywords']:
                    print(f"   Sample Keywords:")
                    for keyword in result['keywords'][:5]:
                        print(f"     • {keyword['text']} (score: {keyword['score']})")
                
                # Show readability
                if result['readability_scores']:
                    overall = result['readability_scores'].get('overall', {})
                    if overall:
                        print(f"   Readability: {overall['classification']} (Grade {overall['average_grade_level']})")
                
                # Show sentiment
                if result['sentiment_scores']:
                    overall = result['sentiment_scores'].get('overall', {})
                    if overall:
                        print(f"   Sentiment: {overall['classification']} (score: {overall['score']})")
                
                return True
                
            else:
                print(f"❌ Text analysis failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Text analysis error: {e}")
            return False
    
    def test_entity_extraction(self):
        """Test named entity extraction"""
        print("\n🏷️ Testing entity extraction...")
        
        test_text = self.test_texts["technical_spec"]
        
        try:
            response = requests.post(
                f"{self.base_url}/extract/entities",
                json={
                    "text": test_text,
                    "include_custom": True,
                    "include_builtin": True,
                    "confidence_threshold": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Entity extraction successful!")
                print(f"   Total Entities: {len(result['entities'])}")
                
                entity_counts = result['entity_counts']
                print(f"   Entity Types Found:")
                for entity_type, count in entity_counts.items():
                    print(f"     • {entity_type}: {count}")
                
                # Show detailed entities
                if result['entities']:
                    print(f"   Sample Entities:")
                    for entity in result['entities'][:8]:
                        print(f"     • '{entity['text']}' → {entity['label']} ({entity['confidence']:.2f})")
                
                return True
                
            else:
                print(f"❌ Entity extraction failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Entity extraction error: {e}")
            return False
    
    def test_similarity_comparison(self):
        """Test text similarity comparison"""
        print("\n🔗 Testing text similarity comparison...")
        
        text1 = self.test_texts["duplicate_text_1"]
        text2 = self.test_texts["duplicate_text_2"]
        
        try:
            response = requests.post(
                f"{self.base_url}/similarity/compare",
                json={
                    "text1": text1,
                    "text2": text2,
                    "algorithms": ["cosine", "jaccard", "semantic"],
                    "include_semantic": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Similarity comparison successful!")
                print(f"   Overall Similarity: {result['overall_similarity']:.3f}")
                
                print(f"   Detailed Scores:")
                for algorithm, score in result['similarity_scores'].items():
                    print(f"     • {algorithm.capitalize()}: {score:.3f}")
                
                return True
                
            else:
                print(f"❌ Similarity comparison failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Similarity comparison error: {e}")
            return False
    
    def test_similar_text_search(self):
        """Test finding similar texts"""
        print("\n🔍 Testing similar text search...")
        
        query_text = self.test_texts["duplicate_text_1"]
        candidate_texts = [
            self.test_texts["duplicate_text_2"],
            self.test_texts["similar_text"],
            self.test_texts["bug_report"],
            self.test_texts["user_feedback"]
        ]
        
        try:
            response = requests.post(
                f"{self.base_url}/similarity/find-similar",
                json={
                    "query_text": query_text,
                    "candidate_texts": candidate_texts,
                    "top_k": 3,
                    "algorithm": "semantic",
                    "threshold": 0.3
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Similar text search successful!")
                print(f"   Candidates Searched: {result['candidates_searched']}")
                print(f"   Matches Found: {result['matches_found']}")
                
                if result['similar_texts']:
                    print(f"   Similar Texts:")
                    for i, match in enumerate(result['similar_texts'], 1):
                        print(f"     {i}. Index {match['index']}: {match['similarity_score']:.3f} similarity")
                        print(f"        \"{match['text'][:80]}...\"")
                
                return True
                
            else:
                print(f"❌ Similar text search failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Similar text search error: {e}")
            return False
    
    def test_duplicate_detection(self):
        """Test duplicate text detection"""
        print("\n👥 Testing duplicate detection...")
        
        texts_to_check = [
            self.test_texts["duplicate_text_1"],
            self.test_texts["duplicate_text_2"],
            self.test_texts["similar_text"],
            self.test_texts["requirements_doc"],
            self.test_texts["duplicate_text_1"]  # Exact duplicate
        ]
        
        try:
            response = requests.post(
                f"{self.base_url}/similarity/detect-duplicates",
                json={
                    "texts": texts_to_check,
                    "threshold": 0.8,
                    "algorithm": "semantic"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Duplicate detection successful!")
                print(f"   Texts Analyzed: {result['total_texts']}")
                print(f"   Duplicates Found: {result['duplicates_found']}")
                
                if result['duplicates']:
                    print(f"   Detected Duplicates:")
                    for i, duplicate in enumerate(result['duplicates'], 1):
                        print(f"     {i}. Texts {duplicate['index1']} & {duplicate['index2']}: {duplicate['similarity_score']:.3f}")
                        print(f"        Text 1: \"{duplicate['text1'][:60]}...\"")
                        print(f"        Text 2: \"{duplicate['text2'][:60]}...\"")
                
                return True
                
            else:
                print(f"❌ Duplicate detection failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Duplicate detection error: {e}")
            return False
    
    def test_language_detection(self):
        """Test language detection"""
        print("\n🌍 Testing language detection...")
        
        test_text = "Hello, this is a sample text in English for testing the language detection capability."
        
        try:
            response = requests.get(
                f"{self.base_url}/analyze/language",
                params={"text": test_text},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Language detection successful!")
                print(f"   Detected Language: {result['detected_language']}")
                print(f"   Confidence Scores:")
                for lang_prob in result['language_probabilities'][:3]:
                    print(f"     • {lang_prob['language']}: {lang_prob['probability']:.3f}")
                
                return True
                
            else:
                print(f"❌ Language detection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Language detection error: {e}")
            return False
    
    def test_text_preprocessing(self):
        """Test text preprocessing"""
        print("\n🔧 Testing text preprocessing...")
        
        test_text = "  This is a SAMPLE text with   extra spaces, URLs like https://example.com, and contractions like don't!  "
        
        try:
            response = requests.post(
                f"{self.base_url}/preprocess/text",
                json={
                    "text": test_text,
                    "options": {
                        "lowercase": True,
                        "remove_extra_whitespace": True,
                        "expand_contractions": True,
                        "remove_urls": False
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Text preprocessing successful!")
                print(f"   Original: \"{result['original_text']}\"")
                print(f"   Processed: \"{result['processed_text']}\"")
                print(f"   Length: {result['original_length']} → {result['processed_length']} chars")
                print(f"   Reduction: {result['reduction_ratio']:.1%}")
                
                return True
                
            else:
                print(f"❌ Text preprocessing failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Text preprocessing error: {e}")
            return False
    
    def test_service_status(self):
        """Test detailed service status"""
        print("\n📊 Testing service status...")
        
        try:
            response = requests.get(f"{self.base_url}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Service status retrieved:")
                print(f"   Service: {data['service']} v{data['version']}")
                print(f"   Status: {data['status']}")
                
                capabilities = data.get('capabilities', {})
                print("   Capabilities:")
                for cap, available in capabilities.items():
                    status = "✅" if available else "❌"
                    print(f"     {status} {cap}: {available}")
                
                model_info = data.get('model_info', {})
                if model_info:
                    print("   Model Information:")
                    print(f"     Sentence Transformer: {model_info.get('sentence_transformer')}")
                    print(f"     spaCy Models: {model_info.get('spacy_models')}")
                
                return True
            else:
                print(f"❌ Service status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service status error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 NLP Processing Service Test Suite")
        print("=" * 50)
        
        # Create test data
        self.create_test_texts()
        
        # Track test results
        tests = [
            ("Health Check", self.test_health_check),
            ("Service Capabilities", self.test_capabilities),
            ("Service Status", self.test_service_status),
            ("Text Analysis", self.test_text_analysis),
            ("Entity Extraction", self.test_entity_extraction),
            ("Similarity Comparison", self.test_similarity_comparison),
            ("Similar Text Search", self.test_similar_text_search),
            ("Duplicate Detection", self.test_duplicate_detection),
            ("Language Detection", self.test_language_detection),
            ("Text Preprocessing", self.test_text_preprocessing),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ {test_name} error: {e}")
        
        # Results summary
        print("\n" + "=" * 50)
        print("🎯 TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {passed}/{total} tests")
        print(f"❌ Failed: {total - passed}/{total} tests")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! NLP Processing Service is working correctly.")
            print("\n🚀 READY FOR PRODUCTION:")
            print("   • Comprehensive text analysis with sentiment and readability")
            print("   • Advanced named entity recognition with custom patterns")
            print("   • Multi-algorithm text similarity and semantic search")
            print("   • Duplicate detection and text clustering")
            print("   • Multi-language support with preprocessing")
            print("   • High-performance REST API endpoints")
        else:
            print(f"\n⚠️ {total - passed} tests failed. Check the service configuration.")
            print("   Make sure all required models are downloaded:")
            print("   • python -m spacy download en_core_web_sm")
            print("   • NLTK data should auto-download on first run")
        
        return passed == total

def main():
    """Main test function"""
    print("🧠 NLP Processing Service Tester")
    print("Ensure the service is running on http://localhost:8003")
    print("You can start it with: ./start.sh")
    
    # Wait a moment for potential startup
    print("\nWaiting 3 seconds for service startup...")
    time.sleep(3)
    
    # Run tests
    tester = NLPServiceTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ NLP Processing Service is ready!")
        print("\n📚 Next Steps:")
        print("   1. Integrate with other QA automation services")
        print("   2. Test with real project documentation")
        print("   3. Configure custom entity patterns for your domain")
        print("   4. Set up production deployment with proper resources")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)