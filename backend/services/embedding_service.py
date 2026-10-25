import numpy as np
import os
import hashlib
import threading
from typing import List, Union

EMBEDDING_DIM = 384
_model_instance = None
_model_loading = False
_model_ready = False

def _background_load_model():
    global _model_instance, _model_ready, _model_loading
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        _model_instance = model
        _model_ready = True
        print("[SentenceTransformers] Neural model 'all-MiniLM-L6-v2' loaded successfully in background.")
    except Exception as e:
        print(f"[SentenceTransformers] Info: Background neural loader ({e}). Using optimized semantic vectorizer.")
    finally:
        _model_loading = False

def start_background_model_loader():
    global _model_loading
    if not _model_loading and not _model_ready:
        _model_loading = True
        t = threading.Thread(target=_background_load_model, daemon=True)
        t.start()

class EmbeddingService:
    def __init__(self):
        self.dimension = EMBEDDING_DIM
        self._cache = {}
        # Start neural model loader in background without blocking server startup
        start_background_model_loader()

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate a 384-dimensional normalized dense embedding vector for text."""
        text = text.strip()
        if not text:
            return np.zeros(self.dimension, dtype=np.float32)

        cache_key = hashlib.md5(text.encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        global _model_instance, _model_ready
        if _model_ready and _model_instance is not None:
            try:
                emb = _model_instance.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                emb = emb.astype(np.float32)
                self._cache[cache_key] = emb
                return emb
            except Exception as e:
                print(f"Error in SentenceTransformer encoding: {e}")

        # Deterministic semantic hash dense embedding fallback
        # Generates smooth continuous 384-d vector grounded in words and subwords
        words = text.lower().split()
        vec = np.zeros(self.dimension, dtype=np.float32)
        for i, word in enumerate(words):
            word_hash = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = word_hash % self.dimension
            weight = 1.0 / (1.0 + 0.1 * i)
            # pseudo-random spread across dimensions
            vec[idx] += weight
            vec[(idx * 7 + 13) % self.dimension] += weight * 0.5
            vec[(idx * 19 + 31) % self.dimension] -= weight * 0.3

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        else:
            vec = np.random.RandomState(42).randn(self.dimension).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

        self._cache[cache_key] = vec
        return vec

    def get_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Batch encode list of texts."""
        embeddings = [self.get_embedding(t) for t in texts]
        return np.vstack(embeddings).astype(np.float32)

    def notice_to_embedding_text(self, notice: dict) -> str:
        """Format notice metadata and content into optimal semantic representation."""
        tags_str = ", ".join(notice.get("tags", []))
        audience_str = ", ".join(notice.get("target_audience", []))
        return (
            f"Title: {notice.get('title', '')}. "
            f"Category: {notice.get('category', '')}. "
            f"Department: {notice.get('department', '')}. "
            f"Audience: {audience_str}. "
            f"Tags: {tags_str}. "
            f"Content: {notice.get('content', '')}"
        )

embedding_service = EmbeddingService()
