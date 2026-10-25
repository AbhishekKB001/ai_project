import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from .embedding_service import embedding_service, EMBEDDING_DIM

FAISS_AVAILABLE = False
faiss = None

try:
    import faiss
    FAISS_AVAILABLE = True
    print("FAISS C++ library loaded successfully.")
except Exception as e:
    FAISS_AVAILABLE = False
    print(f"FAISS not loaded directly ({e}). Using optimized cosine vector index.")

class VectorSearchService:
    def __init__(self):
        self.dimension = EMBEDDING_DIM
        self.index = None
        self.id_to_notice_id = []
        self.notice_id_to_idx = {}
        self.vectors = np.empty((0, self.dimension), dtype=np.float32)
        self.notices_cache = {}
        self._init_index()

    def _init_index(self):
        if FAISS_AVAILABLE:
            # Inner Product (IP) on normalized vectors is exact Cosine Similarity
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = None

    def build_index(self, notices: List[dict]):
        """Build or rebuild the FAISS vector index from a list of notices."""
        self._init_index()
        self.id_to_notice_id = []
        self.notice_id_to_idx = {}
        self.notices_cache = {n["id"]: n for n in notices}

        if not notices:
            self.vectors = np.empty((0, self.dimension), dtype=np.float32)
            return

        texts = [embedding_service.notice_to_embedding_text(n) for n in notices]
        embeddings = embedding_service.get_embeddings_batch(texts)
        self.vectors = embeddings

        for idx, n in enumerate(notices):
            self.id_to_notice_id.append(n["id"])
            self.notice_id_to_idx[n["id"]] = idx

        if FAISS_AVAILABLE and self.index is not None:
            self.index.reset()
            self.index.add(embeddings)
        
        print(f"Vector search index successfully built with {len(notices)} notices. Engine: {'FAISS' if FAISS_AVAILABLE else 'Numpy Cosine'}")

    def add_notice(self, notice: dict):
        """Add a single notice vector to the index."""
        text = embedding_service.notice_to_embedding_text(notice)
        emb = embedding_service.get_embedding(text).reshape(1, -1)

        notice_id = notice["id"]
        self.notices_cache[notice_id] = notice

        if notice_id in self.notice_id_to_idx:
            # Rebuild index to update cleanly
            self.build_index(list(self.notices_cache.values()))
            return

        idx = len(self.id_to_notice_id)
        self.id_to_notice_id.append(notice_id)
        self.notice_id_to_idx[notice_id] = idx

        if len(self.vectors) == 0:
            self.vectors = emb
        else:
            self.vectors = np.vstack([self.vectors, emb])

        if FAISS_AVAILABLE and self.index is not None:
            self.index.add(emb)

    def search_by_vector(
        self,
        query_vector: np.ndarray,
        top_k: int = 8,
        category: Optional[str] = None,
        department: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search nearest notices using a pre-computed query vector."""
        if len(self.id_to_notice_id) == 0:
            return []

        query_vec = query_vector.reshape(1, -1).astype(np.float32)
        total_items = len(self.id_to_notice_id)
        k = total_items  # search full pool of notices to guarantee best semantic ranking

        scores = []
        indices = []

        if FAISS_AVAILABLE and self.index is not None:
            D, I = self.index.search(query_vec, k)
            scores = D[0]
            indices = I[0]
        else:
            # Fallback cosine calculation
            sims = np.dot(self.vectors, query_vec.T).flatten()
            sorted_indices = np.argsort(-sims)[:k]
            indices = sorted_indices
            scores = sims[sorted_indices]

        results = []
        fallback_results = []

        for rank, (idx, score) in enumerate(zip(indices, scores)):
            if idx < 0 or idx >= len(self.id_to_notice_id):
                continue
            notice_id = self.id_to_notice_id[idx]
            notice = self.notices_cache.get(notice_id)
            if not notice:
                continue

            entry = {
                "notice": notice,
                "similarity_score": round(float(max(0.0, min(1.0, (score + 1.0) / 2.0 if score < 0 else score))), 4),
                "raw_score": float(score)
            }
            fallback_results.append(entry)

            # Filtering
            if category and category != "All" and notice.get("category") != category:
                continue
            if department and department != "All Departments" and notice.get("department") not in [department, "All Departments"]:
                continue
            if priority and priority != "All" and notice.get("priority") != priority:
                continue

            results.append(entry)
            if len(results) >= top_k:
                break

        # If filtering was too strict and returned 0 results, return top semantic matches
        if not results and fallback_results:
            results = fallback_results[:top_k]

        return results

    def search_by_text(
        self,
        query_text: str,
        top_k: int = 8,
        category: Optional[str] = None,
        department: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Encode query text and run semantic search in FAISS."""
        query_vec = embedding_service.get_embedding(query_text)
        return self.search_by_vector(query_vec, top_k, category, department, priority)

    def get_embedding_space_projection(self) -> List[Dict[str, Any]]:
        """
        Reduce 384-dimensional notice embeddings to 2D using PCA
        for interactive vector space visualization on the frontend.
        """
        if len(self.vectors) < 2:
            return []

        # Simple fast PCA via SVD on centered vectors
        X = self.vectors - np.mean(self.vectors, axis=0)
        try:
            # SVD decomposition
            u, s, vt = np.linalg.svd(X, full_matrices=False)
            coords_2d = u[:, :2] * s[:2]
            
            # Normalize to -100 to 100 range for pleasant rendering
            max_val = np.max(np.abs(coords_2d)) if np.max(np.abs(coords_2d)) > 0 else 1.0
            coords_2d = (coords_2d / max_val) * 80.0

            points = []
            for idx, notice_id in enumerate(self.id_to_notice_id):
                notice = self.notices_cache.get(notice_id, {})
                points.append({
                    "id": notice_id,
                    "title": notice.get("title", "Notice"),
                    "category": notice.get("category", "General"),
                    "department": notice.get("department", "All Departments"),
                    "priority": notice.get("priority", "Medium"),
                    "x": round(float(coords_2d[idx, 0]), 2),
                    "y": round(float(coords_2d[idx, 1]), 2)
                })
            return points
        except Exception as e:
            print(f"Error computing vector projection: {e}")
            return []

vector_search_service = VectorSearchService()
