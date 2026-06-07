import math
import re
from typing import List, Dict, Tuple, Set
from src.feature_store import FeatureStore
from src.graph import Graph

# Try importing scikit-learn and FAISS. Fall back to pure-Python TF-IDF vector search if not present.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import faiss
    import numpy as np
    HAS_SCIKIT_FAISS = True
except ImportError:
    HAS_SCIKIT_FAISS = False


class BaseCandidateGenerator:
    """Abstract interface for all candidate retrieval engines."""
    def generate_candidates(self, item_id: str, top_n: int = 5) -> List[str]:
        raise NotImplementedError


class CoOccurrenceCandidateGenerator(BaseCandidateGenerator):
    """
    Retrieves candidates using User-Product Bipartite Graph co-occurrence links.
    Finds items frequently purchased together by lookalike customers.
    """
    def __init__(self, graph: Graph):
        self.graph = graph

    def generate_candidates(self, item_id: str, top_n: int = 5) -> List[str]:
        # 2-hop traversal on the Adjacency List Graph
        co_purchased = self.graph.get_co_purchased_products(item_id)
        if not co_purchased:
            return []
            
        # Sort by co-purchase frequency count descending
        sorted_candidates = sorted(co_purchased.items(), key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in sorted_candidates[:top_n]]


class PurePythonTfidfVectorizer:
    """
    Custom lightweight TF-IDF Vectorizer and Cosine Similarity Search.
    Used as a zero-dependency fallback on systems missing scikit-learn or FAISS.
    """
    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: Dict[str, Dict[str, float]] = {}  # pid -> {word: tfidf}
        self.doc_norms: Dict[str, float] = {}              # pid -> L2 norm

    def _tokenize(self, text: str) -> List[str]:
        # Normalize and split on non-alphanumeric boundaries
        return re.findall(r"\b\w{2,}\b", text.lower())

    def fit_transform(self, documents: Dict[str, str]) -> None:
        """
        Fits vocabulary, computes IDF weights, and creates sparse document TF-IDF vectors.
        """
        N = len(documents)
        df: Dict[str, int] = {}
        
        # Step 1: Tokenize and count Document Frequencies (DF)
        doc_tokens = {}
        for pid, text in documents.items():
            tokens = self._tokenize(text)
            doc_tokens[pid] = tokens
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1
                
        # Step 2: Compute Inverse Document Frequencies (IDF)
        for token, count in df.items():
            self.idf[token] = math.log(1.0 + (N / (1.0 + count)))

        # Step 3: Compute TF-IDF sparse vectors and normalization factors
        for pid, tokens in doc_tokens.items():
            if not tokens:
                self.doc_vectors[pid] = {}
                self.doc_norms[pid] = 1.0
                continue
                
            tf: Dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
                
            # Compute tfidf weights
            vector = {}
            squared_sum = 0.0
            for token, count in tf.items():
                tfidf = (count / len(tokens)) * self.idf[token]
                vector[token] = tfidf
                squared_sum += tfidf * tfidf
                
            self.doc_vectors[pid] = vector
            self.doc_norms[pid] = math.sqrt(squared_sum) or 1.0

    def query_similar(self, query_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """Queries sparse vectors using Cosine Similarity: A.B / (||A||*||B||)"""
        query_vec = self.doc_vectors.get(query_id)
        query_norm = self.doc_norms.get(query_id, 1.0)
        
        if not query_vec:
            return []
            
        scores = []
        for pid, vector in self.doc_vectors.items():
            if pid == query_id:
                continue
                
            # Compute dot product
            dot_product = 0.0
            for term, val in query_vec.items():
                if term in vector:
                    dot_product += val * vector[term]
                    
            cosine_sim = dot_product / (query_norm * self.doc_norms[pid])
            scores.append((pid, cosine_sim))
            
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]


class TfidfVectorSearchGenerator(BaseCandidateGenerator):
    """
    Content-Based Candidate Retrieval. Encodes product descriptions/tags
    into TF-IDF vectors and runs fast similarity lookups using FAISS or custom fallback.
    """
    def __init__(self, products_map: dict):
        self.products_map = products_map
        self.pids_list: List[str] = []
        self.vectorizer = None
        self.faiss_index = None
        self.fallback_vectorizer = None
        self._fit_vectorizer()

    def _fit_vectorizer(self):
        # Construct combined texts representing product profiles
        documents = {}
        for pid, prod in self.products_map.items():
            # Combine title, category, description and tags for rich retrieval signal
            profile_text = f"{prod.name} {prod.category} {' '.join(prod.tags)}"
            documents[pid] = profile_text

        self.pids_list = list(documents.keys())

        if HAS_SCIKIT_FAISS:
            # 1. Fit standard Scikit-Learn TfidfVectorizer
            self.vectorizer = TfidfVectorizer(stop_words="english")
            texts = [documents[pid] for pid in self.pids_list]
            tfidf_matrix = self.vectorizer.fit_transform(texts).toarray().astype('float32')
            
            # Normalize vectors to L2 norm for Cosine Similarity search via dot product
            faiss.normalize_L2(tfidf_matrix)
            
            # 2. Initialize FAISS flat inner product index (equivalent to Cosine Similarity)
            dimension = tfidf_matrix.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(tfidf_matrix)
        else:
            # Fall back to custom sparse vectorizer
            self.fallback_vectorizer = PurePythonTfidfVectorizer()
            self.fallback_vectorizer.fit_transform(documents)

    def generate_candidates(self, item_id: str, top_n: int = 5) -> List[str]:
        if item_id not in self.pids_list:
            return []

        if HAS_SCIKIT_FAISS:
            # FAISS ANN Search Path
            idx = self.pids_list.index(item_id)
            query_vector = self.vectorizer.transform([self.products_map[item_id].name]).toarray().astype('float32')
            faiss.normalize_L2(query_vector)
            
            # Query FAISS index: returns distances (similarities) and indices
            similarities, indices = self.faiss_index.search(query_vector, top_n + 1)
            
            candidates = []
            for i in indices[0]:
                pid = self.pids_list[i]
                if pid != item_id:
                    candidates.append(pid)
            return candidates[:top_n]
        else:
            # Custom Cosine Similarity Fallback Path
            sims = self.fallback_vectorizer.query_similar(item_id, top_n)
            return [pid for pid, _ in sims]


class ColdStartFallbackGenerator(BaseCandidateGenerator):
    """
    Fallback orchestrator to solve the 'Cold Start' problem.
    If a primary generator returns insufficient candidates,
    it falls back to global category bestsellers or popular items.
    """
    def __init__(self, primary_generator: BaseCandidateGenerator, feature_store: FeatureStore):
        self.primary_generator = primary_generator
        self.feature_store = feature_store

    def generate_candidates(self, item_id: str, top_n: int = 5) -> List[str]:
        candidates = self.primary_generator.generate_candidates(item_id, top_n)
        
        # If we have enough candidates, return them
        if len(candidates) >= top_n:
            return candidates[:top_n]

        # Cold Start Fallback: Fetch category-popular backups
        # Get category of the target product
        target_item_feat = self.feature_store.get_item_features(item_id)
        category = target_item_feat.get("category", "Unknown")
        
        # Collect items in same category, sorted by popularity weight
        backup_candidates = []
        for pid, feats in self.feature_store.item_features.items():
            if pid == item_id or pid in candidates:
                continue
            if feats["category"] == category:
                backup_candidates.append((pid, feats["popularity_score"]))

        # Sort category items by popularity score descending
        sorted_backups = sorted(backup_candidates, key=lambda x: x[1], reverse=True)
        
        # Fill candidates with backups
        for pid, _ in sorted_backups:
            candidates.append(pid)
            if len(candidates) >= top_n:
                break
                
        # If still not enough, fill with overall popular products
        if len(candidates) < top_n:
            all_popular = sorted(
                self.feature_store.item_features.items(),
                key=lambda x: x[1]["popularity_score"],
                reverse=True
            )
            for pid, _ in all_popular:
                if pid != item_id and pid not in candidates:
                    candidates.append(pid)
                    if len(candidates) >= top_n:
                        break

        return candidates[:top_n]
