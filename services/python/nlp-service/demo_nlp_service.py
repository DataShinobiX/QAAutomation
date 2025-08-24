#!/usr/bin/env python3
"""
NLP Processing Service Demo
Demonstrates comprehensive text analysis, entity extraction, and similarity analysis
"""
import asyncio
import os
import sys
import requests
import json
import time

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

class NLPServiceDemo:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
    
    def check_service_health(self):
        """Check if the service is running"""
        print("🔍 Checking NLP Processing Service health...")
        
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
    
    def demonstrate_text_analysis(self):
        """Demonstrate comprehensive text analysis"""
        print("\n📊 Text Analysis Demo")
        print("-" * 40)
        
        sample_text = """
        User Story US-2024-001: As a project manager, I want to track team productivity 
        metrics in real-time so that I can identify bottlenecks and optimize workflows.
        
        Acceptance Criteria:
        - Dashboard must display current sprint progress with percentage completion
        - Team velocity should be calculated based on story points per sprint
        - System should send alerts when velocity drops below 80% of average
        - All data must be refreshed every 15 minutes automatically
        
        Technical Requirements:
        REQ-PM-001: API response time must be under 200ms for dashboard queries
        REQ-PM-002: Database must support up to 1000 concurrent dashboard users
        
        Priority: High
        Estimated Effort: 8 story points
        Reporter: Sarah Johnson (sarah.johnson@company.com)
        Epic: EPIC-2024-Q1-Analytics
        """
        
        try:
            print(f"📝 Sample Text:")
            print(f"   Length: {len(sample_text)} characters")
            print(f"   Preview: \"{sample_text.strip()[:100]}...\"")
            
            response = requests.post(
                f"{self.base_url}/analyze/text",
                json={
                    "text": sample_text,
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
                
                print(f"\n✅ Analysis Results:")
                print(f"   📍 Language: {result['language']}")
                
                # Text Statistics
                stats = result['text_statistics']
                print(f"   📊 Statistics:")
                print(f"      • Words: {stats['word_count']}")
                print(f"      • Sentences: {stats['sentence_count']}")
                print(f"      • Unique words: {stats['unique_words']}")
                print(f"      • Lexical diversity: {stats['lexical_diversity']}")
                
                # Entities
                if result['entities']:
                    print(f"   🏷️ Named Entities ({len(result['entities'])} found):")
                    for entity in result['entities'][:8]:
                        print(f"      • '{entity['text']}' → {entity['label']} ({entity['confidence']:.2f})")
                
                # Keywords
                if result['keywords']:
                    print(f"   🔑 Keywords ({len(result['keywords'])} found):")
                    for keyword in result['keywords'][:6]:
                        print(f"      • '{keyword['text']}' (score: {keyword['score']:.3f})")
                
                # Readability
                if result['readability_scores']:
                    overall = result['readability_scores'].get('overall', {})
                    if overall:
                        print(f"   📖 Readability: {overall['classification']} (Grade {overall['average_grade_level']:.1f})")
                
                # Sentiment
                if result['sentiment_scores']:
                    overall = result['sentiment_scores'].get('overall', {})
                    if overall:
                        print(f"   😊 Sentiment: {overall['classification']} (score: {overall['score']:.2f})")
                
                # Linguistic Features
                if result['linguistic_features']:
                    lexical = result['linguistic_features'].get('lexical_features', {})
                    if lexical:
                        print(f"   🔤 Language Features:")
                        print(f"      • Nouns: {lexical.get('noun_ratio', 0):.1%}")
                        print(f"      • Verbs: {lexical.get('verb_ratio', 0):.1%}")
                        print(f"      • Adjectives: {lexical.get('adjective_ratio', 0):.1%}")
                
                return True
                
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return False
    
    def demonstrate_entity_extraction(self):
        """Demonstrate entity extraction with custom patterns"""
        print("\n🏷️ Entity Extraction Demo")
        print("-" * 40)
        
        technical_text = """
        BUG-2024-0156: API endpoint /api/v1/users/profile returns 500 error
        
        The getUserProfile function in UserService.java throws NullPointerException
        when accessing database table user_profiles.personal_info for user ID 12345.
        
        Environment: production-cluster-us-east-1.amazonaws.com
        Database: postgresql://db-prod-01:5432/userdata
        Log file: /var/log/app/errors.log
        
        Contact: DevOps Team (devops@company.com)
        Jira ticket: PROJ-1234
        Priority: Critical
        Affected version: v2.3.1
        
        Configuration:
        DB_HOST=db-prod-01.internal
        API_TIMEOUT=30000
        MAX_CONNECTIONS=200
        """
        
        try:
            print(f"🔧 Technical Text Sample:")
            print(f"   Content: Bug report with system details")
            print(f"   Length: {len(technical_text)} characters")
            
            response = requests.post(
                f"{self.base_url}/extract/entities",
                json={
                    "text": technical_text,
                    "include_custom": True,
                    "include_builtin": True,
                    "confidence_threshold": 0.6
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n✅ Entity Extraction Results:")
                print(f"   📊 Total entities: {len(result['entities'])}")
                
                # Group entities by type
                entity_counts = result['entity_counts']
                print(f"   📈 Entity types found:")
                for entity_type, count in sorted(entity_counts.items()):
                    print(f"      • {entity_type}: {count}")
                
                # Show detailed entities
                print(f"   🔍 Detailed entities:")
                for entity in result['entities']:
                    method = entity.get('extraction_method', 'unknown')
                    print(f"      • '{entity['text']}' → {entity['label']} ({entity['confidence']:.2f}) [{method}]")
                
                # Highlight custom patterns detected
                custom_entities = [e for e in result['entities'] if e.get('extraction_method') == 'custom_pattern']
                if custom_entities:
                    print(f"   ⭐ Custom patterns detected ({len(custom_entities)}):")
                    for entity in custom_entities:
                        print(f"      • {entity['text']} → {entity['label']}")
                
                return True
                
            else:
                print(f"❌ Entity extraction failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Entity extraction error: {e}")
            return False
    
    def demonstrate_similarity_analysis(self):
        """Demonstrate text similarity and duplicate detection"""
        print("\n🔗 Text Similarity Demo")
        print("-" * 40)
        
        texts = {
            "original": "The user authentication system provides secure login functionality with password validation and session management.",
            "paraphrase": "Our authentication module offers secure user access through credential verification and session handling capabilities.",
            "similar": "The login system ensures user security by validating passwords and managing active sessions.",
            "different": "The weather forecast shows sunny skies with temperatures reaching 75 degrees Fahrenheit today.",
            "duplicate": "The user authentication system provides secure login functionality with password validation and session management."
        }
        
        try:
            print("📝 Text Samples:")
            for name, text in texts.items():
                print(f"   {name.capitalize()}: \"{text[:60]}...\"")
            
            # Compare original with each other text
            print(f"\n🔍 Similarity Comparisons:")
            original_text = texts["original"]
            
            for name, text in texts.items():
                if name == "original":
                    continue
                
                response = requests.post(
                    f"{self.base_url}/similarity/compare",
                    json={
                        "text1": original_text,
                        "text2": text,
                        "algorithms": ["cosine", "semantic", "jaccard"],
                        "include_semantic": True
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    overall_sim = result['overall_similarity']
                    
                    # Color coding for similarity
                    if overall_sim >= 0.9:
                        status = "🟢 Very High"
                    elif overall_sim >= 0.7:
                        status = "🟡 High"
                    elif overall_sim >= 0.5:
                        status = "🟠 Medium"
                    else:
                        status = "🔴 Low"
                    
                    print(f"   vs {name.capitalize()}: {overall_sim:.3f} {status}")
                    
                    # Show detailed scores
                    scores = result['similarity_scores']
                    print(f"      Cosine: {scores.get('cosine', 0):.3f} | "
                          f"Semantic: {scores.get('semantic', 0):.3f} | "
                          f"Jaccard: {scores.get('jaccard', 0):.3f}")
            
            # Demonstrate duplicate detection
            print(f"\n👥 Duplicate Detection:")
            all_texts = list(texts.values())
            
            response = requests.post(
                f"{self.base_url}/similarity/detect-duplicates",
                json={
                    "texts": all_texts,
                    "threshold": 0.9,
                    "algorithm": "semantic"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Texts analyzed: {result['total_texts']}")
                print(f"   Duplicates found: {result['duplicates_found']}")
                
                if result['duplicates']:
                    for duplicate in result['duplicates']:
                        print(f"   • Texts {duplicate['index1']} & {duplicate['index2']}: {duplicate['similarity_score']:.3f} similarity")
                else:
                    print("   No duplicates detected above threshold")
            
            return True
            
        except Exception as e:
            print(f"❌ Similarity analysis error: {e}")
            return False
    
    def demonstrate_advanced_features(self):
        """Demonstrate advanced NLP features"""
        print("\n🚀 Advanced Features Demo")
        print("-" * 40)
        
        try:
            # Language Detection
            multilingual_texts = [
                ("English", "This is a sample text in English for testing language detection."),
                ("Spanish", "Este es un texto de muestra en español para probar la detección de idiomas."),
                ("French", "Ceci est un exemple de texte en français pour tester la détection de langue.")
            ]
            
            print("🌍 Language Detection:")
            for lang_name, text in multilingual_texts:
                response = requests.get(
                    f"{self.base_url}/analyze/language",
                    params={"text": text},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    detected = result['detected_language']
                    confidence = result['language_probabilities'][0]['probability']
                    print(f"   {lang_name}: detected as '{detected}' ({confidence:.3f} confidence)")
            
            # Text Preprocessing
            print(f"\n🔧 Text Preprocessing:")
            messy_text = "   This is a MESSY text with    extra spaces, contractions like don't and won't, and URLs like https://example.com!  "
            
            response = requests.post(
                f"{self.base_url}/preprocess/text",
                json={
                    "text": messy_text,
                    "options": {
                        "lowercase": True,
                        "remove_extra_whitespace": True,
                        "expand_contractions": True,
                        "remove_urls": True
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Original:  \"{result['original_text']}\"")
                print(f"   Processed: \"{result['processed_text']}\"")
                print(f"   Reduction: {result['reduction_ratio']:.1%} size reduction")
            
            # Similar Text Search
            print(f"\n🔍 Similar Text Search:")
            query = "user authentication and login security"
            candidates = [
                "secure user login with password verification",
                "weather forecast and temperature readings",
                "authentication system for user access control", 
                "database optimization and query performance",
                "login security and user credential management"
            ]
            
            response = requests.post(
                f"{self.base_url}/similarity/find-similar",
                json={
                    "query_text": query,
                    "candidate_texts": candidates,
                    "top_k": 3,
                    "algorithm": "semantic",
                    "threshold": 0.3
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Query: \"{query}\"")
                print(f"   Top matches:")
                for i, match in enumerate(result['similar_texts'], 1):
                    print(f"     {i}. \"{candidates[match['index']]}\" ({match['similarity_score']:.3f})")
            
            return True
            
        except Exception as e:
            print(f"❌ Advanced features error: {e}")
            return False
    
    def show_service_capabilities(self):
        """Show detailed service capabilities"""
        print("\n📋 Service Capabilities")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/capabilities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                print("🧠 Text Analysis Features:")
                features = data['text_analysis_features']
                for i, feature in enumerate(features, 1):
                    print(f"   {i:2d}. {feature.replace('_', ' ').title()}")
                
                print(f"\n🏷️ Entity Types ({len(data['entity_types'])} supported):")
                for entity_type in data['entity_types'][:12]:  # Show first 12
                    print(f"   • {entity_type}")
                if len(data['entity_types']) > 12:
                    print(f"   • ... and {len(data['entity_types']) - 12} more")
                
                print(f"\n🔗 Similarity Algorithms:")
                for algorithm in data['similarity_algorithms']:
                    print(f"   • {algorithm.replace('_', ' ').title()}")
                
                print(f"\n🌍 Supported Languages ({len(data['supported_languages'])}):")
                langs = ', '.join(data['supported_languages'])
                print(f"   {langs}")
                
        except Exception as e:
            print(f"❌ Failed to get capabilities: {e}")
    
    def run_demo(self):
        """Run the complete demo"""
        print("🧠 NLP Processing Service Demo")
        print("=" * 50)
        
        # Check service health
        if not self.check_service_health():
            return False
        
        # Show capabilities
        self.show_service_capabilities()
        
        print(f"\n🚀 Running NLP Processing Demonstrations...")
        print("=" * 50)
        
        # Run demos
        demos = [
            ("Text Analysis", self.demonstrate_text_analysis),
            ("Entity Extraction", self.demonstrate_entity_extraction), 
            ("Similarity Analysis", self.demonstrate_similarity_analysis),
            ("Advanced Features", self.demonstrate_advanced_features)
        ]
        
        success_count = 0
        for demo_name, demo_func in demos:
            try:
                if demo_func():
                    success_count += 1
                time.sleep(1.5)  # Brief pause between demos
            except Exception as e:
                print(f"❌ {demo_name} demo error: {e}")
        
        print("\n🎉 NLP Processing Service Demo Complete!")
        print("=" * 50)
        print(f"✅ Successfully demonstrated: {success_count}/{len(demos)} features")
        print("\n🌟 Key Capabilities Showcased:")
        print("   • Comprehensive text analysis with sentiment and readability")
        print("   • Advanced named entity recognition with custom patterns")
        print("   • Multi-algorithm text similarity and semantic search")
        print("   • Duplicate detection and language identification")
        print("   • Text preprocessing and normalization")
        print("   • Production-ready REST API with comprehensive endpoints")
        
        print("\n🚀 The NLP Processing service is ready for integration!")
        
        return success_count == len(demos)

def main():
    """Main demo function"""
    print("🎪 NLP Processing Service Live Demo")
    print("Ensure the service is running: ./start.sh")
    
    # Wait for service startup
    print("\nWaiting 3 seconds for service...")
    time.sleep(3)
    
    demo = NLPServiceDemo()
    success = demo.run_demo()
    
    if success:
        print("\n📚 Next Steps:")
        print("   1. Integrate with QA automation workflow")
        print("   2. Test with real project documentation")
        print("   3. Customize entity patterns for your domain")
        print("   4. Set up production deployment with proper resources")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)