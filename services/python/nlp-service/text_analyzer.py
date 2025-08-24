"""
Text Analyzer
Core NLP processing with spaCy and transformers for comprehensive text analysis
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple, Union
import structlog
from datetime import datetime
import re
import string
from collections import Counter, defaultdict

import spacy
from spacy import displacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import textstat
from textblob import TextBlob
from langdetect import detect
import contractions
import emoji
from unidecode import unidecode

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config

logger = structlog.get_logger()

class TextAnalysisResult:
    """Result of comprehensive text analysis"""
    def __init__(
        self,
        text: str,
        language: str,
        analysis_metadata: Dict[str, Any]
    ):
        self.text = text
        self.language = language
        self.analysis_metadata = analysis_metadata
        self.analyzed_at = datetime.utcnow()
        
        # Analysis results (populated by analyzer)
        self.entities = []
        self.keywords = []
        self.sentences = []
        self.tokens = []
        self.readability_scores = {}
        self.sentiment_scores = {}
        self.linguistic_features = {}
        self.text_statistics = {}

class TextAnalyzer:
    """Advanced text analysis using spaCy and NLTK"""
    
    def __init__(self):
        self.nlp_models = {}
        self.lemmatizer = None
        self.stop_words = set()
        
        # Download required NLTK data
        self._download_nltk_data()
        
        # Initialize models
        self._load_spacy_models()
        self._initialize_nltk_components()
        
        logger.info("Text Analyzer initialized",
                   spacy_models=list(self.nlp_models.keys()),
                   nltk_ready=self.lemmatizer is not None)
    
    def _download_nltk_data(self):
        """Download required NLTK datasets"""
        try:
            nltk_downloads = [
                'punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger',
                'vader_lexicon', 'omw-1.4', 'brown', 'names'
            ]
            
            for dataset in nltk_downloads:
                try:
                    nltk.download(dataset, quiet=True)
                except Exception as e:
                    logger.warning(f"Failed to download NLTK dataset: {dataset}", error=str(e))
                    
        except Exception as e:
            logger.warning("NLTK data download failed", error=str(e))
    
    def _load_spacy_models(self):
        """Load available spaCy models"""
        for model_name in config.spacy_models:
            try:
                nlp = spacy.load(model_name)
                self.nlp_models[model_name] = nlp
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(f"spaCy model not available: {model_name}")
        
        # Fallback to basic English model if none loaded
        if not self.nlp_models:
            try:
                nlp = spacy.load("en_core_web_sm")
                self.nlp_models["en_core_web_sm"] = nlp
                logger.info("Loaded fallback spaCy model: en_core_web_sm")
            except OSError:
                logger.error("No spaCy models available. Install with: python -m spacy download en_core_web_sm")
    
    def _initialize_nltk_components(self):
        """Initialize NLTK components"""
        try:
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
            logger.info("NLTK components initialized")
        except Exception as e:
            logger.warning("NLTK initialization failed", error=str(e))
    
    def _get_spacy_model(self, language: str = "en") -> Optional[spacy.Language]:
        """Get appropriate spaCy model for language"""
        # Language to model mapping
        lang_models = {
            "en": ["en_core_web_lg", "en_core_web_md", "en_core_web_sm"],
            "es": ["es_core_news_sm"],
            "fr": ["fr_core_news_sm"],
            "de": ["de_core_news_sm"]
        }
        
        # Try to find best model for language
        for model_name in lang_models.get(language, ["en_core_web_sm"]):
            if model_name in self.nlp_models:
                return self.nlp_models[model_name]
        
        # Fallback to any available model
        if self.nlp_models:
            return list(self.nlp_models.values())[0]
        
        return None
    
    async def analyze_text(
        self,
        text: str,
        language: Optional[str] = None,
        include_entities: bool = True,
        include_sentiment: bool = True,
        include_readability: bool = True,
        include_keywords: bool = True,
        include_linguistic_features: bool = True
    ) -> TextAnalysisResult:
        """
        Comprehensive text analysis
        
        Args:
            text: Text to analyze
            language: Language code (auto-detected if None)
            include_entities: Extract named entities
            include_sentiment: Perform sentiment analysis
            include_readability: Calculate readability metrics
            include_keywords: Extract keywords and key phrases
            include_linguistic_features: Analyze linguistic patterns
        """
        logger.info("Starting text analysis",
                   text_length=len(text),
                   language=language,
                   features_requested={
                       "entities": include_entities,
                       "sentiment": include_sentiment,
                       "readability": include_readability,
                       "keywords": include_keywords,
                       "linguistic": include_linguistic_features
                   })
        
        try:
            # Validate text length
            if len(text) > config.max_text_length:
                raise ValueError(f"Text too long: {len(text)} chars (max: {config.max_text_length})")
            
            # Detect language if not provided
            if not language:
                language = await self._detect_language(text)
            
            # Get appropriate model
            nlp = self._get_spacy_model(language)
            if not nlp:
                raise ValueError("No spaCy model available for analysis")
            
            # Process text with spaCy
            doc = nlp(text)
            
            # Create result object
            result = TextAnalysisResult(
                text=text,
                language=language,
                analysis_metadata={
                    "spacy_model": nlp.meta["name"],
                    "text_length": len(text),
                    "processing_time": 0,  # Will be updated
                    "features_included": {
                        "entities": include_entities,
                        "sentiment": include_sentiment,
                        "readability": include_readability,
                        "keywords": include_keywords,
                        "linguistic": include_linguistic_features
                    }
                }
            )
            
            start_time = datetime.utcnow()
            
            # Basic text statistics
            result.text_statistics = await self._calculate_text_statistics(text, doc)
            
            # Extract entities
            if include_entities:
                result.entities = await self._extract_entities(doc)
            
            # Sentiment analysis
            if include_sentiment:
                result.sentiment_scores = await self._analyze_sentiment(text)
            
            # Readability analysis
            if include_readability:
                result.readability_scores = await self._calculate_readability(text)
            
            # Keyword extraction
            if include_keywords:
                result.keywords = await self._extract_keywords(text, doc)
            
            # Linguistic features
            if include_linguistic_features:
                result.linguistic_features = await self._analyze_linguistic_features(doc)
            
            # Extract sentences and tokens
            result.sentences = [sent.text.strip() for sent in doc.sents]
            result.tokens = [
                {
                    "text": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_,
                    "tag": token.tag_,
                    "is_alpha": token.is_alpha,
                    "is_stop": token.is_stop,
                    "is_punct": token.is_punct
                }
                for token in doc
                if not token.is_space
            ]
            
            # Update processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.analysis_metadata["processing_time"] = processing_time
            
            logger.info("Text analysis completed",
                       language=language,
                       entities_found=len(result.entities),
                       keywords_found=len(result.keywords),
                       sentences=len(result.sentences),
                       tokens=len(result.tokens),
                       processing_time=processing_time)
            
            return result
            
        except Exception as e:
            logger.error("Text analysis failed", error=str(e))
            raise
    
    async def _detect_language(self, text: str) -> str:
        """Detect text language"""
        try:
            # Use first 1000 characters for detection
            sample_text = text[:1000]
            
            # Detect language
            detected_lang = detect(sample_text)
            
            # Map to supported languages
            if detected_lang in config.supported_languages:
                return detected_lang
            
            # Default to English
            return "en"
            
        except Exception as e:
            logger.warning("Language detection failed", error=str(e))
            return "en"
    
    async def _calculate_text_statistics(self, text: str, doc: spacy.Doc) -> Dict[str, Any]:
        """Calculate basic text statistics"""
        words = [token.text for token in doc if token.is_alpha]
        sentences = list(doc.sents)
        
        # Character counts
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # Word statistics
        word_count = len(words)
        unique_words = len(set(word.lower() for word in words))
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Sentence statistics
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Complexity metrics
        syllable_count = sum(self._count_syllables(word) for word in words)
        
        # POS tag distribution
        pos_tags = Counter(token.pos_ for token in doc if not token.is_space)
        
        return {
            "character_count": char_count,
            "character_count_no_spaces": char_count_no_spaces,
            "word_count": word_count,
            "unique_words": unique_words,
            "sentence_count": sentence_count,
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "syllable_count": syllable_count,
            "lexical_diversity": round(unique_words / word_count, 3) if word_count > 0 else 0,
            "pos_distribution": dict(pos_tags)
        }
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)  # Minimum 1 syllable per word
    
    async def _extract_entities(self, doc: spacy.Doc) -> List[Dict[str, Any]]:
        """Extract named entities from document"""
        entities = []
        
        for ent in doc.ents:
            # Filter by confidence and type
            if ent.label_ in config.entity_types:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "description": spacy.explain(ent.label_),
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                    "confidence": getattr(ent, 'confidence', 0.9)  # spaCy doesn't provide confidence by default
                })
        
        # Remove duplicates and sort by confidence
        unique_entities = {}
        for entity in entities:
            key = (entity["text"].lower(), entity["label"])
            if key not in unique_entities or entity["confidence"] > unique_entities[key]["confidence"]:
                unique_entities[key] = entity
        
        return sorted(unique_entities.values(), key=lambda x: x["confidence"], reverse=True)
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using multiple approaches"""
        sentiments = {}
        
        # TextBlob sentiment
        try:
            blob = TextBlob(text)
            sentiments["textblob"] = {
                "polarity": round(blob.sentiment.polarity, 3),  # -1 to 1
                "subjectivity": round(blob.sentiment.subjectivity, 3),  # 0 to 1
                "classification": self._classify_polarity(blob.sentiment.polarity)
            }
        except Exception as e:
            logger.warning("TextBlob sentiment analysis failed", error=str(e))
        
        # VADER sentiment (via NLTK)
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            
            sia = SentimentIntensityAnalyzer()
            vader_scores = sia.polarity_scores(text)
            
            sentiments["vader"] = {
                "compound": round(vader_scores["compound"], 3),
                "positive": round(vader_scores["pos"], 3),
                "negative": round(vader_scores["neg"], 3),
                "neutral": round(vader_scores["neu"], 3),
                "classification": self._classify_compound_score(vader_scores["compound"])
            }
        except Exception as e:
            logger.warning("VADER sentiment analysis failed", error=str(e))
        
        # Overall sentiment (weighted average)
        if sentiments:
            overall_score = 0
            weight_sum = 0
            
            if "textblob" in sentiments:
                overall_score += sentiments["textblob"]["polarity"] * 0.5
                weight_sum += 0.5
            
            if "vader" in sentiments:
                overall_score += sentiments["vader"]["compound"] * 0.5
                weight_sum += 0.5
            
            if weight_sum > 0:
                overall_score /= weight_sum
                sentiments["overall"] = {
                    "score": round(overall_score, 3),
                    "classification": self._classify_polarity(overall_score)
                }
        
        return sentiments
    
    def _classify_polarity(self, score: float) -> str:
        """Classify sentiment polarity score"""
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        else:
            return "neutral"
    
    def _classify_compound_score(self, score: float) -> str:
        """Classify VADER compound score"""
        if score >= 0.05:
            return "positive"
        elif score <= -0.05:
            return "negative"
        else:
            return "neutral"
    
    async def _calculate_readability(self, text: str) -> Dict[str, Any]:
        """Calculate various readability metrics"""
        readability = {}
        
        try:
            # Flesch Reading Ease
            readability["flesch_reading_ease"] = {
                "score": round(textstat.flesch_reading_ease(text), 2),
                "interpretation": self._interpret_flesch_reading_ease(textstat.flesch_reading_ease(text))
            }
            
            # Flesch-Kincaid Grade Level
            readability["flesch_kincaid_grade"] = {
                "score": round(textstat.flesch_kincaid_grade(text), 2),
                "interpretation": "Grade level required to understand the text"
            }
            
            # SMOG Index
            readability["smog_index"] = {
                "score": round(textstat.smog_index(text), 2),
                "interpretation": "Years of education needed to understand the text"
            }
            
            # Automated Readability Index
            readability["automated_readability_index"] = {
                "score": round(textstat.automated_readability_index(text), 2),
                "interpretation": "Grade level (US) required to understand the text"
            }
            
            # Coleman-Liau Index
            readability["coleman_liau_index"] = {
                "score": round(textstat.coleman_liau_index(text), 2),
                "interpretation": "Grade level required to understand the text"
            }
            
            # Gunning Fog Index
            readability["gunning_fog"] = {
                "score": round(textstat.gunning_fog(text), 2),
                "interpretation": "Years of formal education required to understand the text"
            }
            
            # Overall readability classification
            avg_grade_level = (
                readability["flesch_kincaid_grade"]["score"] +
                readability["automated_readability_index"]["score"] +
                readability["coleman_liau_index"]["score"] +
                readability["gunning_fog"]["score"]
            ) / 4
            
            readability["overall"] = {
                "average_grade_level": round(avg_grade_level, 2),
                "classification": self._classify_reading_level(avg_grade_level)
            }
            
        except Exception as e:
            logger.warning("Readability calculation failed", error=str(e))
        
        return readability
    
    def _interpret_flesch_reading_ease(self, score: float) -> str:
        """Interpret Flesch Reading Ease score"""
        if score >= 90:
            return "Very Easy (5th grade)"
        elif score >= 80:
            return "Easy (6th grade)"
        elif score >= 70:
            return "Fairly Easy (7th grade)"
        elif score >= 60:
            return "Standard (8th-9th grade)"
        elif score >= 50:
            return "Fairly Difficult (10th-12th grade)"
        elif score >= 30:
            return "Difficult (College level)"
        else:
            return "Very Difficult (Graduate level)"
    
    def _classify_reading_level(self, grade_level: float) -> str:
        """Classify overall reading level"""
        if grade_level <= 6:
            return "Elementary"
        elif grade_level <= 9:
            return "Middle School"
        elif grade_level <= 12:
            return "High School"
        elif grade_level <= 16:
            return "College"
        else:
            return "Graduate"
    
    async def _extract_keywords(self, text: str, doc: spacy.Doc) -> List[Dict[str, Any]]:
        """Extract keywords using multiple methods"""
        keywords = []
        
        try:
            # Method 1: TF-IDF based keywords using spaCy
            # Get meaningful tokens (no stop words, punctuation, spaces)
            tokens = [
                token.lemma_.lower()
                for token in doc
                if not token.is_stop
                and not token.is_punct
                and not token.is_space
                and token.is_alpha
                and len(token.text) > 2
            ]
            
            # Calculate token frequencies
            token_freq = Counter(tokens)
            total_tokens = len(tokens)
            
            # Simple TF-IDF approximation (without IDF for single document)
            for token, count in token_freq.most_common(config.max_keywords):
                tf_score = count / total_tokens
                if tf_score >= config.keyword_min_score:
                    keywords.append({
                        "text": token,
                        "score": round(tf_score, 4),
                        "frequency": count,
                        "method": "tf_frequency"
                    })
            
            # Method 2: Named entities as keywords
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "PRODUCT", "EVENT", "GPE"]:
                    keywords.append({
                        "text": ent.text,
                        "score": 0.8,  # High score for named entities
                        "frequency": 1,
                        "method": "named_entity",
                        "entity_type": ent.label_
                    })
            
            # Method 3: Noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3 and len(chunk.text) > 3:  # Multi-word phrases
                    keywords.append({
                        "text": chunk.text.lower(),
                        "score": 0.6,
                        "frequency": 1,
                        "method": "noun_phrase"
                    })
            
            # Remove duplicates and sort by score
            unique_keywords = {}
            for keyword in keywords:
                key = keyword["text"].lower()
                if key not in unique_keywords or keyword["score"] > unique_keywords[key]["score"]:
                    unique_keywords[key] = keyword
            
            # Sort by score and return top keywords
            sorted_keywords = sorted(
                unique_keywords.values(),
                key=lambda x: x["score"],
                reverse=True
            )[:config.max_keywords]
            
            return sorted_keywords
            
        except Exception as e:
            logger.warning("Keyword extraction failed", error=str(e))
            return []
    
    async def _analyze_linguistic_features(self, doc: spacy.Doc) -> Dict[str, Any]:
        """Analyze linguistic features and patterns"""
        features = {}
        
        try:
            # POS tag analysis
            pos_counts = Counter(token.pos_ for token in doc if not token.is_space)
            total_tokens = sum(pos_counts.values())
            
            features["pos_distribution"] = {
                pos: round(count / total_tokens, 3)
                for pos, count in pos_counts.items()
            }
            
            # Dependency parsing analysis
            dep_counts = Counter(token.dep_ for token in doc if not token.is_space)
            features["dependency_distribution"] = dict(dep_counts.most_common(10))
            
            # Sentence complexity
            sentences = list(doc.sents)
            if sentences:
                sentence_lengths = [len([t for t in sent if not t.is_space]) for sent in sentences]
                features["sentence_complexity"] = {
                    "avg_sentence_length": round(sum(sentence_lengths) / len(sentence_lengths), 2),
                    "max_sentence_length": max(sentence_lengths),
                    "min_sentence_length": min(sentence_lengths),
                    "sentence_length_variance": round(
                        sum((x - sum(sentence_lengths) / len(sentence_lengths)) ** 2 for x in sentence_lengths) / len(sentence_lengths),
                        2
                    )
                }
            
            # Lexical features
            tokens = [token for token in doc if not token.is_space and not token.is_punct]
            if tokens:
                features["lexical_features"] = {
                    "noun_ratio": round(sum(1 for t in tokens if t.pos_ == "NOUN") / len(tokens), 3),
                    "verb_ratio": round(sum(1 for t in tokens if t.pos_ == "VERB") / len(tokens), 3),
                    "adjective_ratio": round(sum(1 for t in tokens if t.pos_ == "ADJ") / len(tokens), 3),
                    "adverb_ratio": round(sum(1 for t in tokens if t.pos_ == "ADV") / len(tokens), 3),
                    "stop_word_ratio": round(sum(1 for t in tokens if t.is_stop) / len(tokens), 3)
                }
            
            # Text patterns
            features["text_patterns"] = {
                "has_questions": bool(re.search(r'\?', doc.text)),
                "has_exclamations": bool(re.search(r'!', doc.text)),
                "has_urls": bool(re.search(r'https?://', doc.text)),
                "has_emails": bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', doc.text)),
                "has_numbers": bool(re.search(r'\d+', doc.text)),
                "has_uppercase_words": bool(re.search(r'\b[A-Z]{2,}\b', doc.text))
            }
            
        except Exception as e:
            logger.warning("Linguistic feature analysis failed", error=str(e))
        
        return features
    
    async def preprocess_text(
        self,
        text: str,
        options: Optional[Dict[str, bool]] = None
    ) -> str:
        """
        Preprocess text according to specified options
        
        Args:
            text: Input text to preprocess
            options: Preprocessing options override
        """
        if options is None:
            options = config.preprocessing_options
        
        processed_text = text
        
        try:
            # Remove extra whitespace
            if options.get("remove_extra_whitespace", True):
                processed_text = re.sub(r'\s+', ' ', processed_text).strip()
            
            # Expand contractions
            if options.get("expand_contractions", True):
                processed_text = contractions.fix(processed_text)
            
            # Remove URLs
            if options.get("remove_urls", False):
                processed_text = re.sub(r'https?://\S+', '', processed_text)
            
            # Remove emails
            if options.get("remove_emails", False):
                processed_text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', processed_text)
            
            # Remove phone numbers
            if options.get("remove_phone_numbers", False):
                processed_text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', processed_text)
            
            # Convert to lowercase
            if options.get("lowercase", True):
                processed_text = processed_text.lower()
            
            # Remove punctuation
            if options.get("remove_punctuation", False):
                processed_text = processed_text.translate(str.maketrans('', '', string.punctuation))
            
            # Remove stopwords and lemmatize (requires spaCy processing)
            if options.get("remove_stopwords", False) or options.get("lemmatization", True):
                nlp = self._get_spacy_model("en")
                if nlp:
                    doc = nlp(processed_text)
                    
                    tokens = []
                    for token in doc:
                        if token.is_space:
                            continue
                        
                        token_text = token.lemma_ if options.get("lemmatization", True) else token.text
                        
                        if options.get("remove_stopwords", False) and token.is_stop:
                            continue
                        
                        tokens.append(token_text)
                    
                    processed_text = ' '.join(tokens)
            
            logger.debug("Text preprocessing completed",
                        original_length=len(text),
                        processed_length=len(processed_text),
                        options=options)
            
            return processed_text
            
        except Exception as e:
            logger.error("Text preprocessing failed", error=str(e))
            return text  # Return original text on failure