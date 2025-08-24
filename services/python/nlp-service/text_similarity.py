"""
Text Similarity
Advanced text similarity and semantic comparison using multiple algorithms
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple, Union
import structlog
from datetime import datetime
import re
from collections import Counter
import math

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import textdistance
from sentence_transformers import SentenceTransformer

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config

logger = structlog.get_logger()

class SimilarityResult:
    """Result of text similarity comparison"""
    def __init__(
        self,
        text1: str,
        text2: str,
        similarity_scores: Dict[str, float],
        comparison_metadata: Dict[str, Any]
    ):
        self.text1 = text1
        self.text2 = text2
        self.similarity_scores = similarity_scores
        self.comparison_metadata = comparison_metadata
        self.compared_at = datetime.utcnow()
    
    def get_overall_similarity(self) -> float:
        """Get weighted overall similarity score"""
        if "semantic" in self.similarity_scores:
            return self.similarity_scores["semantic"]
        elif "cosine" in self.similarity_scores:
            return self.similarity_scores["cosine"]
        else:
            return max(self.similarity_scores.values()) if self.similarity_scores else 0.0

class TextClusterResult:
    """Result of text clustering analysis"""
    def __init__(
        self,
        texts: List[str],
        clusters: Dict[int, List[int]],
        cluster_metadata: Dict[str, Any]
    ):
        self.texts = texts
        self.clusters = clusters
        self.cluster_metadata = cluster_metadata
        self.clustered_at = datetime.utcnow()
    
    def get_cluster_summaries(self) -> Dict[int, Dict[str, Any]]:
        """Get summary information for each cluster"""
        summaries = {}
        for cluster_id, text_indices in self.clusters.items():
            cluster_texts = [self.texts[i] for i in text_indices]
            summaries[cluster_id] = {
                "size": len(text_indices),
                "text_indices": text_indices,
                "sample_texts": cluster_texts[:3],  # First 3 texts as samples
                "avg_length": sum(len(text) for text in cluster_texts) / len(cluster_texts),
                "keywords": self._extract_cluster_keywords(cluster_texts)
            }
        return summaries
    
    def _extract_cluster_keywords(self, texts: List[str]) -> List[str]:
        """Extract common keywords from cluster texts"""
        # Simple keyword extraction using word frequency
        all_words = []
        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            all_words.extend(words)
        
        word_counts = Counter(all_words)
        # Return top 5 most common words (excluding very common ones)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those'}
        
        keywords = [word for word, count in word_counts.most_common(10) 
                   if word not in stop_words and len(word) > 2]
        return keywords[:5]

class TextSimilarityAnalyzer:
    """Advanced text similarity analysis with multiple algorithms"""
    
    def __init__(self):
        self.sentence_model = None
        self.tfidf_vectorizer = None
        
        # Initialize models
        self._initialize_models()
        
        logger.info("Text Similarity Analyzer initialized",
                   sentence_model_available=self.sentence_model is not None)
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        try:
            # Initialize sentence transformer for semantic similarity
            self.sentence_model = SentenceTransformer(config.sentence_transformer_model)
            logger.info(f"Loaded sentence transformer: {config.sentence_transformer_model}")
        except Exception as e:
            logger.warning("Failed to load sentence transformer", error=str(e))
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    async def compare_texts(
        self,
        text1: str,
        text2: str,
        algorithms: Optional[List[str]] = None,
        include_semantic: bool = True
    ) -> SimilarityResult:
        """
        Compare two texts using multiple similarity algorithms
        
        Args:
            text1: First text to compare
            text2: Second text to compare
            algorithms: List of algorithms to use
            include_semantic: Whether to include semantic similarity
        """
        if algorithms is None:
            algorithms = config.similarity_algorithms
        
        logger.info("Starting text similarity comparison",
                   text1_length=len(text1),
                   text2_length=len(text2),
                   algorithms=algorithms)
        
        try:
            start_time = datetime.utcnow()
            similarity_scores = {}
            
            # Lexical similarity algorithms
            if "jaccard" in algorithms:
                similarity_scores["jaccard"] = await self._jaccard_similarity(text1, text2)
            
            if "cosine" in algorithms:
                similarity_scores["cosine"] = await self._cosine_similarity(text1, text2)
            
            if "levenshtein" in algorithms:
                similarity_scores["levenshtein"] = await self._levenshtein_similarity(text1, text2)
            
            if "jaro_winkler" in algorithms:
                similarity_scores["jaro_winkler"] = await self._jaro_winkler_similarity(text1, text2)
            
            # Semantic similarity
            if "semantic" in algorithms and include_semantic and self.sentence_model:
                similarity_scores["semantic"] = await self._semantic_similarity(text1, text2)
            
            # Additional text-based metrics
            similarity_scores["character_overlap"] = await self._character_overlap(text1, text2)
            similarity_scores["word_overlap"] = await self._word_overlap(text1, text2)
            similarity_scores["sentence_overlap"] = await self._sentence_overlap(text1, text2)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            comparison_metadata = {
                "algorithms_used": list(similarity_scores.keys()),
                "text1_length": len(text1),
                "text2_length": len(text2),
                "processing_time": processing_time,
                "semantic_available": self.sentence_model is not None
            }
            
            result = SimilarityResult(
                text1=text1,
                text2=text2,
                similarity_scores=similarity_scores,
                comparison_metadata=comparison_metadata
            )
            
            logger.info("Text similarity comparison completed",
                       overall_similarity=result.get_overall_similarity(),
                       algorithms_used=len(similarity_scores),
                       processing_time=processing_time)
            
            return result
            
        except Exception as e:
            logger.error("Text similarity comparison failed", error=str(e))
            raise
    
    async def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity coefficient"""
        # Convert to word sets
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF cosine similarity"""
        try:
            # Fit and transform texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            return float(similarity_matrix[0, 1])
            
        except Exception as e:
            logger.warning("Cosine similarity calculation failed", error=str(e))
            return 0.0
    
    async def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """Calculate normalized Levenshtein distance similarity"""
        try:
            distance = textdistance.levenshtein.distance(text1, text2)
            max_len = max(len(text1), len(text2))
            
            if max_len == 0:
                return 1.0
            
            return 1.0 - (distance / max_len)
            
        except Exception as e:
            logger.warning("Levenshtein similarity calculation failed", error=str(e))
            return 0.0
    
    async def _jaro_winkler_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaro-Winkler similarity"""
        try:
            return textdistance.jaro_winkler(text1, text2)
        except Exception as e:
            logger.warning("Jaro-Winkler similarity calculation failed", error=str(e))
            return 0.0
    
    async def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using sentence embeddings"""
        if not self.sentence_model:
            return 0.0
        
        try:
            # Generate embeddings
            embeddings = self.sentence_model.encode([text1, text2])
            
            # Calculate cosine similarity between embeddings
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0, 0]
            
            return float(similarity)
            
        except Exception as e:
            logger.warning("Semantic similarity calculation failed", error=str(e))
            return 0.0
    
    async def _character_overlap(self, text1: str, text2: str) -> float:
        """Calculate character-level overlap percentage"""
        chars1 = set(text1.lower())
        chars2 = set(text2.lower())
        
        if not chars1 and not chars2:
            return 1.0
        
        intersection = len(chars1.intersection(chars2))
        total_unique = len(chars1.union(chars2))
        
        return intersection / total_unique if total_unique > 0 else 0.0
    
    async def _word_overlap(self, text1: str, text2: str) -> float:
        """Calculate word-level overlap percentage"""
        words1 = re.findall(r'\b\w+\b', text1.lower())
        words2 = re.findall(r'\b\w+\b', text2.lower())
        
        if not words1 and not words2:
            return 1.0
        
        # Calculate overlap based on word frequency
        counter1 = Counter(words1)
        counter2 = Counter(words2)
        
        # Intersection of counters (minimum counts)
        intersection = sum((counter1 & counter2).values())
        
        # Total words
        total_words = len(words1) + len(words2)
        
        return (2 * intersection) / total_words if total_words > 0 else 0.0
    
    async def _sentence_overlap(self, text1: str, text2: str) -> float:
        """Calculate sentence-level overlap"""
        # Simple sentence splitting
        sentences1 = [s.strip() for s in re.split(r'[.!?]+', text1) if s.strip()]
        sentences2 = [s.strip() for s in re.split(r'[.!?]+', text2) if s.strip()]
        
        if not sentences1 and not sentences2:
            return 1.0
        
        # Find similar sentences (using word overlap)
        similar_count = 0
        
        for sent1 in sentences1:
            for sent2 in sentences2:
                word_sim = await self._word_overlap(sent1, sent2)
                if word_sim > 0.5:  # Threshold for sentence similarity
                    similar_count += 1
                    break  # Count each sentence1 only once
        
        total_sentences = len(sentences1) + len(sentences2)
        
        return (2 * similar_count) / total_sentences if total_sentences > 0 else 0.0
    
    async def find_similar_texts(
        self,
        query_text: str,
        candidate_texts: List[str],
        top_k: int = 5,
        algorithm: str = "semantic",
        threshold: float = 0.5
    ) -> List[Tuple[int, str, float]]:
        """
        Find most similar texts from a list of candidates
        
        Args:
            query_text: Text to find similarities for
            candidate_texts: List of candidate texts to compare against
            top_k: Number of top results to return
            algorithm: Similarity algorithm to use
            threshold: Minimum similarity threshold
        
        Returns:
            List of (index, text, similarity_score) tuples
        """
        logger.info("Finding similar texts",
                   query_length=len(query_text),
                   candidates=len(candidate_texts),
                   algorithm=algorithm)
        
        try:
            similarities = []
            
            if algorithm == "semantic" and self.sentence_model:
                # Use semantic similarity for efficient batch processing
                all_texts = [query_text] + candidate_texts
                embeddings = self.sentence_model.encode(all_texts)
                
                query_embedding = embeddings[0]
                candidate_embeddings = embeddings[1:]
                
                # Calculate similarities
                similarity_scores = cosine_similarity([query_embedding], candidate_embeddings)[0]
                
                for i, score in enumerate(similarity_scores):
                    if score >= threshold:
                        similarities.append((i, candidate_texts[i], float(score)))
            
            else:
                # Use other algorithms
                for i, candidate_text in enumerate(candidate_texts):
                    result = await self.compare_texts(
                        query_text, candidate_text,
                        algorithms=[algorithm],
                        include_semantic=(algorithm == "semantic")
                    )
                    
                    score = result.similarity_scores.get(algorithm, 0.0)
                    if score >= threshold:
                        similarities.append((i, candidate_text, score))
            
            # Sort by similarity score (descending) and return top k
            similarities.sort(key=lambda x: x[2], reverse=True)
            
            logger.info("Similar texts found",
                       matches_found=len(similarities),
                       top_k_returned=min(top_k, len(similarities)))
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error("Similar text search failed", error=str(e))
            return []
    
    async def cluster_texts(
        self,
        texts: List[str],
        algorithm: str = "semantic",
        min_samples: int = 2,
        eps: float = 0.3
    ) -> TextClusterResult:
        """
        Cluster texts based on similarity
        
        Args:
            texts: List of texts to cluster
            algorithm: Algorithm to use for similarity calculation
            min_samples: Minimum samples for DBSCAN clustering
            eps: DBSCAN epsilon parameter (max distance for cluster membership)
        """
        logger.info("Starting text clustering",
                   text_count=len(texts),
                   algorithm=algorithm)
        
        try:
            if len(texts) < 2:
                return TextClusterResult(
                    texts=texts,
                    clusters={0: list(range(len(texts)))},
                    cluster_metadata={
                        "algorithm": algorithm,
                        "total_clusters": 1 if texts else 0,
                        "noise_points": 0
                    }
                )
            
            # Generate embeddings or similarity matrix
            if algorithm == "semantic" and self.sentence_model:
                embeddings = self.sentence_model.encode(texts)
                clustering_data = embeddings
            else:
                # Create similarity matrix for other algorithms
                similarity_matrix = np.zeros((len(texts), len(texts)))
                
                for i in range(len(texts)):
                    for j in range(i + 1, len(texts)):
                        result = await self.compare_texts(
                            texts[i], texts[j],
                            algorithms=[algorithm],
                            include_semantic=(algorithm == "semantic")
                        )
                        sim_score = result.similarity_scores.get(algorithm, 0.0)
                        similarity_matrix[i, j] = sim_score
                        similarity_matrix[j, i] = sim_score
                
                # Convert similarity to distance for clustering
                distance_matrix = 1.0 - similarity_matrix
                clustering_data = distance_matrix
            
            # Perform DBSCAN clustering
            if algorithm == "semantic":
                dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
                cluster_labels = dbscan.fit_predict(clustering_data)
            else:
                dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
                cluster_labels = dbscan.fit_predict(clustering_data)
            
            # Group texts by cluster
            clusters = {}
            noise_points = 0
            
            for i, label in enumerate(cluster_labels):
                if label == -1:  # Noise point
                    noise_points += 1
                    if -1 not in clusters:
                        clusters[-1] = []
                    clusters[-1].append(i)
                else:
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(i)
            
            cluster_metadata = {
                "algorithm": algorithm,
                "total_clusters": len([k for k in clusters.keys() if k != -1]),
                "noise_points": noise_points,
                "eps": eps,
                "min_samples": min_samples,
                "silhouette_score": None  # Could add silhouette analysis
            }
            
            result = TextClusterResult(
                texts=texts,
                clusters=clusters,
                cluster_metadata=cluster_metadata
            )
            
            logger.info("Text clustering completed",
                       clusters_found=cluster_metadata["total_clusters"],
                       noise_points=noise_points)
            
            return result
            
        except Exception as e:
            logger.error("Text clustering failed", error=str(e))
            # Return single cluster on failure
            return TextClusterResult(
                texts=texts,
                clusters={0: list(range(len(texts)))},
                cluster_metadata={"error": str(e)}
            )
    
    async def detect_duplicates(
        self,
        texts: List[str],
        threshold: float = 0.9,
        algorithm: str = "semantic"
    ) -> List[Tuple[int, int, float]]:
        """
        Detect duplicate or near-duplicate texts
        
        Args:
            texts: List of texts to check for duplicates
            threshold: Similarity threshold for considering texts as duplicates
            algorithm: Algorithm to use for similarity calculation
        
        Returns:
            List of (index1, index2, similarity_score) for detected duplicates
        """
        logger.info("Detecting duplicate texts",
                   text_count=len(texts),
                   threshold=threshold,
                   algorithm=algorithm)
        
        try:
            duplicates = []
            
            if len(texts) < 2:
                return duplicates
            
            # Compare all pairs of texts
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    result = await self.compare_texts(
                        texts[i], texts[j],
                        algorithms=[algorithm],
                        include_semantic=(algorithm == "semantic")
                    )
                    
                    similarity = result.similarity_scores.get(algorithm, 0.0)
                    
                    if similarity >= threshold:
                        duplicates.append((i, j, similarity))
            
            # Sort by similarity score (descending)
            duplicates.sort(key=lambda x: x[2], reverse=True)
            
            logger.info("Duplicate detection completed",
                       duplicates_found=len(duplicates))
            
            return duplicates
            
        except Exception as e:
            logger.error("Duplicate detection failed", error=str(e))
            return []