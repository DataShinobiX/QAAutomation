"""
Entity Extractor
Advanced named entity recognition and extraction using spaCy and transformers
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
import structlog
from datetime import datetime
import re
from collections import defaultdict

import spacy
from spacy.matcher import Matcher
from spacy.util import filter_spans
from spacy.tokens import Doc
import en_core_web_sm

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config

logger = structlog.get_logger()

class EntityExtractionResult:
    """Result of entity extraction process"""
    def __init__(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        extraction_metadata: Dict[str, Any]
    ):
        self.text = text
        self.entities = entities
        self.extraction_metadata = extraction_metadata
        self.extracted_at = datetime.utcnow()
    
    def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get entities of specific type"""
        return [entity for entity in self.entities if entity["label"] == entity_type]
    
    def get_entity_counts(self) -> Dict[str, int]:
        """Get count of entities by type"""
        counts = defaultdict(int)
        for entity in self.entities:
            counts[entity["label"]] += 1
        return dict(counts)

class EntityExtractor:
    """Advanced entity extraction with custom patterns and rules"""
    
    def __init__(self):
        self.nlp = None
        self.matcher = None
        self.custom_patterns = {}
        
        # Initialize spaCy model and matcher
        self._initialize_models()
        self._setup_custom_patterns()
        
        logger.info("Entity Extractor initialized",
                   model_available=self.nlp is not None,
                   custom_patterns=len(self.custom_patterns))
    
    def _initialize_models(self):
        """Initialize spaCy models"""
        try:
            # Try to load the best available English model
            model_names = ["en_core_web_lg", "en_core_web_md", "en_core_web_sm"]
            
            for model_name in model_names:
                try:
                    self.nlp = spacy.load(model_name)
                    logger.info(f"Loaded spaCy model: {model_name}")
                    break
                except OSError:
                    continue
            
            if not self.nlp:
                # Fallback to basic model
                self.nlp = en_core_web_sm.load()
                logger.info("Loaded fallback spaCy model")
            
            # Initialize matcher
            self.matcher = Matcher(self.nlp.vocab)
            
        except Exception as e:
            logger.error("Failed to initialize spaCy models", error=str(e))
    
    def _setup_custom_patterns(self):
        """Setup custom entity patterns for domain-specific extraction"""
        if not self.nlp or not self.matcher:
            return
        
        # Email pattern
        email_pattern = [
            {"LIKE_EMAIL": True}
        ]
        self.matcher.add("EMAIL", [email_pattern])
        self.custom_patterns["EMAIL"] = "Email address"
        
        # URL pattern
        url_pattern = [
            {"LIKE_URL": True}
        ]
        self.matcher.add("URL", [url_pattern])
        self.custom_patterns["URL"] = "Web URL"
        
        # Phone number patterns
        phone_patterns = [
            # (123) 456-7890
            [{"SHAPE": "(ddd)"}, {"SHAPE": "ddd-dddd"}],
            # 123-456-7890
            [{"SHAPE": "ddd-ddd-dddd"}],
            # 123.456.7890
            [{"SHAPE": "ddd.ddd.dddd"}],
            # 1234567890
            [{"SHAPE": "dddddddddd"}]
        ]
        self.matcher.add("PHONE", phone_patterns)
        self.custom_patterns["PHONE"] = "Phone number"
        
        # Version number pattern (e.g., v1.2.3, 2.0.1)
        version_patterns = [
            [{"TEXT": {"REGEX": r"v?\d+\.\d+(\.\d+)?(-\w+)?"}},]
        ]
        self.matcher.add("VERSION", version_patterns)
        self.custom_patterns["VERSION"] = "Version number"
        
        # IP address pattern
        ip_pattern = [
            {"TEXT": {"REGEX": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"}}
        ]
        self.matcher.add("IP_ADDRESS", [ip_pattern])
        self.custom_patterns["IP_ADDRESS"] = "IP address"
        
        # Test case identifier patterns
        test_case_patterns = [
            # TC-001, TEST-001, T001
            [{"TEXT": {"REGEX": r"(TC|TEST|T)-?\d+"}}],
            # Test_Case_001
            [{"TEXT": {"REGEX": r"Test_Case_\d+"}}]
        ]
        self.matcher.add("TEST_CASE", test_case_patterns)
        self.custom_patterns["TEST_CASE"] = "Test case identifier"
        
        # Bug/Issue ID patterns  
        bug_patterns = [
            # BUG-001, ISSUE-001, JIRA-001
            [{"TEXT": {"REGEX": r"(BUG|ISSUE|JIRA|TICKET)-?\d+"}}]
        ]
        self.matcher.add("BUG_ID", bug_patterns)
        self.custom_patterns["BUG_ID"] = "Bug/Issue identifier"
        
        # Requirement ID patterns
        req_patterns = [
            # REQ-001, REQUIREMENT-001
            [{"TEXT": {"REGEX": r"(REQ|REQUIREMENT)-?\d+"}}],
            # R001, FR001 (Functional Requirement)
            [{"TEXT": {"REGEX": r"(R|FR|NFR)\d+"}}]
        ]
        self.matcher.add("REQUIREMENT_ID", req_patterns)
        self.custom_patterns["REQUIREMENT_ID"] = "Requirement identifier"
        
        # User story patterns
        user_story_patterns = [
            # US-001, USER_STORY-001
            [{"TEXT": {"REGEX": r"(US|USER_STORY)-?\d+"}}]
        ]
        self.matcher.add("USER_STORY", user_story_patterns)
        self.custom_patterns["USER_STORY"] = "User story identifier"
        
        # API endpoint patterns
        api_patterns = [
            # /api/v1/users, /users/{id}
            [{"TEXT": {"REGEX": r"/[a-zA-Z0-9/_{}]+"}}]
        ]
        self.matcher.add("API_ENDPOINT", api_patterns)
        self.custom_patterns["API_ENDPOINT"] = "API endpoint"
        
        # Database table/field patterns
        db_patterns = [
            # table.field, database.table.field
            [{"TEXT": {"REGEX": r"\w+\.\w+(\.\w+)?"}}]
        ]
        self.matcher.add("DATABASE_FIELD", db_patterns)
        self.custom_patterns["DATABASE_FIELD"] = "Database field"
        
        # Configuration keys (e.g., CONFIG_KEY, config.setting)
        config_patterns = [
            [{"TEXT": {"REGEX": r"[A-Z_]+[A-Z0-9_]*"}}, {"TEXT": "="}, {"IS_ALPHA": True}],
            [{"TEXT": {"REGEX": r"config\.[a-zA-Z_][a-zA-Z0-9_]*"}}]
        ]
        self.matcher.add("CONFIG_SETTING", config_patterns)
        self.custom_patterns["CONFIG_SETTING"] = "Configuration setting"
        
        logger.info(f"Setup {len(self.custom_patterns)} custom entity patterns")
    
    async def extract_entities(
        self,
        text: str,
        include_custom: bool = True,
        include_builtin: bool = True,
        confidence_threshold: Optional[float] = None
    ) -> EntityExtractionResult:
        """
        Extract entities from text using both built-in and custom patterns
        
        Args:
            text: Text to analyze
            include_custom: Include custom pattern matching
            include_builtin: Include spaCy built-in entities
            confidence_threshold: Minimum confidence for entity inclusion
        """
        logger.info("Starting entity extraction",
                   text_length=len(text),
                   include_custom=include_custom,
                   include_builtin=include_builtin)
        
        if not self.nlp:
            raise ValueError("spaCy model not available")
        
        if confidence_threshold is None:
            confidence_threshold = config.confidence_threshold
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            entities = []
            start_time = datetime.utcnow()
            
            # Extract built-in spaCy entities
            if include_builtin:
                builtin_entities = await self._extract_builtin_entities(doc, confidence_threshold)
                entities.extend(builtin_entities)
            
            # Extract custom pattern entities
            if include_custom:
                custom_entities = await self._extract_custom_entities(doc)
                entities.extend(custom_entities)
            
            # Post-process entities
            entities = await self._post_process_entities(entities, doc)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            extraction_metadata = {
                "spacy_model": self.nlp.meta["name"],
                "text_length": len(text),
                "confidence_threshold": confidence_threshold,
                "processing_time": processing_time,
                "entity_types_found": list(set(entity["label"] for entity in entities)),
                "extraction_methods": []
            }
            
            if include_builtin:
                extraction_metadata["extraction_methods"].append("spacy_builtin")
            if include_custom:
                extraction_metadata["extraction_methods"].append("custom_patterns")
            
            result = EntityExtractionResult(
                text=text,
                entities=entities,
                extraction_metadata=extraction_metadata
            )
            
            logger.info("Entity extraction completed",
                       entities_found=len(entities),
                       entity_types=len(set(entity["label"] for entity in entities)),
                       processing_time=processing_time)
            
            return result
            
        except Exception as e:
            logger.error("Entity extraction failed", error=str(e))
            raise
    
    async def _extract_builtin_entities(
        self,
        doc: Doc,
        confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """Extract built-in spaCy entities"""
        entities = []
        
        for ent in doc.ents:
            # Filter by entity type and confidence
            if ent.label_ in config.entity_types:
                # spaCy doesn't provide confidence scores by default
                # We'll assign a default high confidence for built-in entities
                confidence = 0.9
                
                if confidence >= confidence_threshold:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "description": spacy.explain(ent.label_) or self.custom_patterns.get(ent.label_, ""),
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "confidence": confidence,
                        "extraction_method": "spacy_builtin"
                    })
        
        return entities
    
    async def _extract_custom_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """Extract entities using custom patterns"""
        entities = []
        
        if not self.matcher:
            return entities
        
        # Find matches using custom patterns
        matches = self.matcher(doc)
        
        # Convert matches to entities
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            entities.append({
                "text": span.text,
                "label": label,
                "description": self.custom_patterns.get(label, ""),
                "start_char": span.start_char,
                "end_char": span.end_char,
                "confidence": 0.8,  # Default confidence for pattern matches
                "extraction_method": "custom_pattern"
            })
        
        return entities
    
    async def _post_process_entities(
        self,
        entities: List[Dict[str, Any]],
        doc: Doc
    ) -> List[Dict[str, Any]]:
        """Post-process entities to remove overlaps and improve quality"""
        
        # Remove duplicate entities (same text and label)
        unique_entities = {}
        for entity in entities:
            key = (entity["text"].lower(), entity["label"], entity["start_char"])
            if key not in unique_entities or entity["confidence"] > unique_entities[key]["confidence"]:
                unique_entities[key] = entity
        
        entities = list(unique_entities.values())
        
        # Remove overlapping entities (keep highest confidence)
        entities = sorted(entities, key=lambda x: (x["start_char"], x["confidence"]), reverse=True)
        
        non_overlapping = []
        for entity in entities:
            overlaps = False
            for existing in non_overlapping:
                # Check for overlap
                if not (entity["end_char"] <= existing["start_char"] or 
                       entity["start_char"] >= existing["end_char"]):
                    overlaps = True
                    break
            
            if not overlaps:
                non_overlapping.append(entity)
        
        # Sort by position in text
        non_overlapping.sort(key=lambda x: x["start_char"])
        
        # Add context information
        for entity in non_overlapping:
            entity["context"] = self._get_entity_context(entity, doc)
        
        return non_overlapping
    
    def _get_entity_context(self, entity: Dict[str, Any], doc: Doc) -> Dict[str, Any]:
        """Get contextual information around an entity"""
        start_char = entity["start_char"]
        end_char = entity["end_char"]
        
        # Find the token span for this entity
        entity_span = doc.char_span(start_char, end_char)
        if not entity_span:
            return {}
        
        # Get sentence containing the entity
        sentence = None
        for sent in doc.sents:
            if start_char >= sent.start_char and end_char <= sent.end_char:
                sentence = sent
                break
        
        context = {}
        
        if sentence:
            context["sentence"] = sentence.text.strip()
            context["sentence_start"] = sentence.start_char
            context["sentence_end"] = sentence.end_char
        
        # Get surrounding words (5 words before and after)
        entity_tokens = [token.i for token in entity_span]
        if entity_tokens:
            start_token = max(0, min(entity_tokens) - 5)
            end_token = min(len(doc), max(entity_tokens) + 6)
            
            surrounding_tokens = doc[start_token:end_token]
            context["surrounding_text"] = surrounding_tokens.text.strip()
        
        return context
    
    async def extract_entities_by_type(
        self,
        text: str,
        entity_types: List[str],
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract specific types of entities from text
        
        Args:
            text: Text to analyze
            entity_types: List of entity types to extract
            confidence_threshold: Minimum confidence threshold
        """
        result = await self.extract_entities(
            text=text,
            confidence_threshold=confidence_threshold
        )
        
        # Group entities by type
        entities_by_type = defaultdict(list)
        for entity in result.entities:
            if entity["label"] in entity_types:
                entities_by_type[entity["label"]].append(entity)
        
        return dict(entities_by_type)
    
    async def find_entity_relationships(
        self,
        entities: List[Dict[str, Any]],
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Find relationships between extracted entities
        
        Args:
            entities: List of extracted entities
            text: Original text
        """
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        relationships = []
        
        # Simple relationship detection based on proximity and patterns
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                
                # Check if entities are in the same sentence
                if abs(entity1["start_char"] - entity2["start_char"]) < 200:  # Within 200 characters
                    
                    # Determine relationship type based on entity types
                    rel_type = self._determine_relationship_type(entity1, entity2, doc)
                    
                    if rel_type:
                        relationships.append({
                            "entity1": entity1,
                            "entity2": entity2,
                            "relationship_type": rel_type,
                            "confidence": 0.6,  # Conservative confidence for relationships
                            "distance": abs(entity1["start_char"] - entity2["start_char"])
                        })
        
        # Sort by confidence and distance
        relationships.sort(key=lambda x: (x["confidence"], -x["distance"]), reverse=True)
        
        return relationships
    
    def _determine_relationship_type(
        self,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any],
        doc: Doc
    ) -> Optional[str]:
        """Determine the type of relationship between two entities"""
        
        label1, label2 = entity1["label"], entity2["label"]
        
        # Define relationship patterns
        relationship_patterns = {
            ("PERSON", "ORG"): "works_for",
            ("PERSON", "PERSON"): "associated_with",
            ("ORG", "PRODUCT"): "produces",
            ("GPE", "ORG"): "located_in",
            ("DATE", "EVENT"): "occurs_on",
            ("MONEY", "PRODUCT"): "costs",
            ("TEST_CASE", "BUG_ID"): "tests_for",
            ("REQUIREMENT_ID", "TEST_CASE"): "verified_by",
            ("USER_STORY", "REQUIREMENT_ID"): "detailed_by",
            ("API_ENDPOINT", "DATABASE_FIELD"): "accesses"
        }
        
        # Check direct patterns
        if (label1, label2) in relationship_patterns:
            return relationship_patterns[(label1, label2)]
        
        if (label2, label1) in relationship_patterns:
            return relationship_patterns[(label2, label1)]
        
        # Generic relationships based on proximity
        if label1 != label2:
            return "related_to"
        
        return None