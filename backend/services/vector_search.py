import numpy as np
import re
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

STOP_WORDS = {
    "what", "when", "where", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "can", "will", "just", "don", "should", "now",
    "notice", "notices", "circular", "circulars", "details", "information", "rules"
}

SYNONYMS = {
    "exam": ["examinations", "exam", "exams", "midterm", "hall ticket", "grades", "timetable", "syllabus", "supplementary", "sepm", "test", "quiz"],
    "placement": ["placements", "placement", "job", "jobs", "internship", "interview", "recruitment", "sde", "company", "career", "package", "google", "microsoft", "amazon"],
    "hackathon": ["hackathon", "hacknova", "coding", "competition", "hackathons"],
    "scholarship": ["scholarship", "scholarships", "financial aid", "grant", "merit", "fellowship", "waiver"],
    "fee": ["fees", "fee", "tuition", "payment", "fine", "penalty", "finance", "accounts", "dues"],
    "hostel": ["hostel", "hostels", "room", "mess", "allotment", "biometric", "campus & hostel", "warden"],
    "sports": ["sports", "athletics", "tournament", "games", "trials", "inter-collegiate", "cricket", "football"],
    "library": ["library", "books", "clearance", "repository", "digital library", "academics"]
}

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
        """Search nearest notices using a pre-computed query vector (used by Recommendation Engine)."""
        if len(self.id_to_notice_id) == 0:
            return []

        query_vec = query_vector.reshape(1, -1).astype(np.float32)
        k = len(self.id_to_notice_id)

        if FAISS_AVAILABLE and self.index is not None:
            D, I = self.index.search(query_vec, k)
            scores = D[0]
            indices = I[0]
        else:
            sims = np.dot(self.vectors, query_vec.T).flatten()
            sorted_indices = np.argsort(-sims)[:k]
            indices = sorted_indices
            scores = sims[sorted_indices]

        results = []
        for idx, score in zip(indices, scores):
            if idx < 0 or idx >= len(self.id_to_notice_id):
                continue
            notice_id = self.id_to_notice_id[idx]
            notice = self.notices_cache.get(notice_id)
            if not notice:
                continue

            # Filtering
            if category and category != "All" and notice.get("category") != category:
                continue
            if department and department != "All Departments" and notice.get("department") not in [department, "All Departments"]:
                continue
            if priority and priority != "All" and notice.get("priority") != priority:
                continue

            raw_sim = float(score)
            sim = max(0.0, raw_sim)

            results.append({
                "notice": notice,
                "similarity_score": round(sim, 4),
                "raw_score": raw_sim
            })
            if len(results) >= top_k:
                break

        return results

    def search_by_text(
        self,
        query_text: str,
        top_k: int = 8,
        category: Optional[str] = None,
        department: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        High-precision topic-aware hybrid search combining FAISS dense semantic embeddings
        and lexical keyword matching with strict relevance thresholding.
        """
        if not query_text or not query_text.strip() or len(self.id_to_notice_id) == 0:
            return []

        q_lower = query_text.lower().strip()
        q_tokens = [w for w in re.findall(r'\b\w+\b', q_lower) if len(w) > 2 and w not in STOP_WORDS]
        query_vec = embedding_service.get_embedding(query_text).reshape(1, -1).astype(np.float32)

        k = len(self.id_to_notice_id)
        if FAISS_AVAILABLE and self.index is not None:
            D, I = self.index.search(query_vec, k)
            faiss_scores = {self.id_to_notice_id[idx]: float(score) for idx, score in zip(I[0], D[0]) if 0 <= idx < k}
        else:
            sims = np.dot(self.vectors, query_vec.T).flatten()
            faiss_scores = {self.id_to_notice_id[idx]: float(sims[idx]) for idx in range(k)}

        candidates = []
        for notice_id in self.id_to_notice_id:
            notice = self.notices_cache.get(notice_id)
            if not notice:
                continue

            # Explicit dropdown/pill filters
            if category and category != "All" and notice.get("category") != category:
                continue
            if department and department != "All Departments" and notice.get("department") not in [department, "All Departments"]:
                continue
            if priority and priority != "All" and notice.get("priority") != priority:
                continue

            raw_sim = faiss_scores.get(notice_id, 0.0)
            sim = float(max(0.0, raw_sim))

            title_l = notice.get("title", "").lower()
            cat_l = notice.get("category", "").lower()
            content_l = notice.get("content", "").lower()
            tags_l = " ".join(notice.get("tags", [])).lower()
            dept_l = notice.get("department", "").lower()

            lex = 0.0

            # 1. Topic & Synonym matching (Exact category intent)
            for topic_key, syn_list in SYNONYMS.items():
                if any(syn in q_lower for syn in syn_list):
                    if any(syn in cat_l for syn in syn_list) or any(syn in title_l for syn in syn_list):
                        lex = max(lex, 0.85)
                        break

            # 2. Exact Title Tokens Match
            if q_tokens:
                matched_title = [w for w in q_tokens if w in title_l]
                if matched_title:
                    ratio = len(matched_title) / len(q_tokens)
                    lex = max(lex, 0.50 + 0.50 * ratio)

                # 3. Tag Tokens Match
                matched_tags = [w for w in q_tokens if w in tags_l]
                if matched_tags:
                    lex = max(lex, 0.65)

                # 4. Department match
                if any(w in dept_l for w in q_tokens):
                    lex = max(lex, 0.50)

                # 5. Content match
                matched_content = [w for w in q_tokens if w in content_l]
                if len(matched_content) >= max(1, len(q_tokens)):
                    lex = max(lex, 0.40)

            # Combined Score: balanced semantic + lexical
            if lex > 0:
                final_score = (0.40 * sim + 0.60 * lex)
            else:
                final_score = sim

            # Strict Relevance Threshold:
            # Only include notices that have genuine lexical or high semantic alignment
            if lex >= 0.45 or sim >= 0.35:
                candidates.append({
                    "notice": notice,
                    "similarity_score": round(float(final_score), 4),
                    "raw_score": raw_sim,
                    "lexical_score": lex
                })

        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Remove trailing irrelevant notices if top hit is strong
        if candidates and candidates[0]["similarity_score"] >= 0.50:
            top_s = candidates[0]["similarity_score"]
            threshold = max(0.40, top_s * 0.55)
            candidates = [c for c in candidates if c["similarity_score"] >= threshold]

        return candidates[:top_k]

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
