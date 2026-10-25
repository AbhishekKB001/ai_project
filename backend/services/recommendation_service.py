import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

from .embedding_service import embedding_service
from .vector_search import vector_search_service
from ..database import db

class RecommendationService:
    def __init__(self):
        pass

    def get_user_vector(self, user_profile: dict) -> np.ndarray:
        """
        Build a high-dimensional preference vector for a user combining:
        1. Explicit interests, department, and academic year
        2. Bookmarked notices embeddings
        3. Recently viewed notices embeddings
        """
        interests = ", ".join(user_profile.get("interests", []))
        dept = user_profile.get("department", "All Departments")
        year = user_profile.get("year", "All Students")
        profile_text = f"Student in {dept}, {year}. Interested in {interests}."
        base_vec = embedding_service.get_embedding(profile_text)

        # Bookmarks vector
        bookmark_vecs = []
        for nid in user_profile.get("bookmarked_notice_ids", []):
            notice = db.get_notice_by_id(nid)
            if notice:
                text = embedding_service.notice_to_embedding_text(notice)
                bookmark_vecs.append(embedding_service.get_embedding(text))

        # History vector
        history_vecs = []
        for nid in user_profile.get("history_notice_ids", [])[:5]:
            notice = db.get_notice_by_id(nid)
            if notice:
                text = embedding_service.notice_to_embedding_text(notice)
                history_vecs.append(embedding_service.get_embedding(text))

        # Blend vectors
        final_vec = base_vec * 0.5
        if bookmark_vecs:
            final_vec += np.mean(bookmark_vecs, axis=0) * 0.35
        if history_vecs:
            final_vec += np.mean(history_vecs, axis=0) * 0.15

        norm = np.linalg.norm(final_vec)
        if norm > 1e-6:
            final_vec = final_vec / norm
        return final_vec

    def calculate_audience_match(self, notice: dict, user_profile: dict) -> float:
        """Calculate eligibility / audience alignment score (0.0 to 1.0)."""
        score = 0.5
        target_audience = notice.get("target_audience", [])
        user_year = user_profile.get("year", "3rd Year")
        user_dept = user_profile.get("department", "Computer Science")

        if "All Students" in target_audience or user_year in target_audience:
            score += 0.3

        notice_dept = notice.get("department", "All Departments")
        if notice_dept in ["All Departments", user_dept]:
            score += 0.2

        return min(1.0, score)

    def calculate_urgency_boost(self, notice: dict) -> float:
        """Boost score if notice has an urgent deadline or critical priority."""
        priority = notice.get("priority", "Medium")
        boost = 0.0
        if priority == "Critical":
            boost += 0.25
        elif priority == "High":
            boost += 0.15

        deadline = notice.get("deadline")
        if deadline:
            try:
                d_date = datetime.strptime(deadline[:10], "%Y-%m-%d")
                days_left = (d_date - datetime.now()).days
                if 0 <= days_left <= 3:
                    boost += 0.2
                elif 0 <= days_left <= 7:
                    boost += 0.1
            except Exception:
                pass

        return boost

    def get_personalized_recommendations(
        self,
        user_profile: dict,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Generate hybrid recommendations using FAISS semantic search + rule-based re-ranking.
        """
        user_vec = self.get_user_vector(user_profile)
        all_notices = db.get_all_notices()
        
        # Get semantic candidates via FAISS
        candidates = vector_search_service.search_by_vector(user_vec, top_k=limit * 2)

        scored_notices = []
        seen_ids = set()

        for item in candidates:
            notice = item["notice"]
            nid = notice["id"]
            if nid in seen_ids:
                continue
            seen_ids.add(nid)

            vector_sim = item["similarity_score"]
            aud_score = self.calculate_audience_match(notice, user_profile)
            urg_boost = self.calculate_urgency_boost(notice)

            # Check if user already read or bookmarked
            is_bookmarked = nid in user_profile.get("bookmarked_notice_ids", [])
            already_viewed = nid in user_profile.get("history_notice_ids", [])

            # Compute final hybrid score
            hybrid_score = (0.50 * vector_sim) + (0.30 * aud_score) + (0.20 * urg_boost)
            if is_bookmarked:
                hybrid_score *= 0.9  # slightly de-prioritize already bookmarked items to surface novel notices

            match_reasons = []
            if vector_sim > 0.7:
                match_reasons.append("Matches your interests")
            if aud_score >= 0.8:
                match_reasons.append(f"For {user_profile.get('department')} ({user_profile.get('year')})")
            if urg_boost > 0.15:
                match_reasons.append("Approaching deadline")
            if not match_reasons:
                match_reasons.append("Campus announcement")

            scored_notices.append({
                "notice": notice,
                "score": round(float(hybrid_score), 3),
                "similarity_score": vector_sim,
                "match_reason": " • ".join(match_reasons),
                "is_bookmarked": is_bookmarked,
                "already_viewed": already_viewed
            })

        # Fallback if candidates were insufficient
        if len(scored_notices) < limit:
            for notice in all_notices:
                if notice["id"] not in seen_ids:
                    seen_ids.add(notice["id"])
                    scored_notices.append({
                        "notice": notice,
                        "score": 0.5,
                        "similarity_score": 0.5,
                        "match_reason": "General announcement",
                        "is_bookmarked": notice["id"] in user_profile.get("bookmarked_notice_ids", []),
                        "already_viewed": notice["id"] in user_profile.get("history_notice_ids", [])
                    })
                if len(scored_notices) >= limit:
                    break

        scored_notices.sort(key=lambda x: x["score"], reverse=True)
        return scored_notices[:limit]

    def get_feed_categories(self, user_profile: dict) -> Dict[str, Any]:
        """Returns structured feed sections for the modern home dashboard."""
        all_notices = db.get_all_notices()
        
        # 1. Personalized recommendations
        personalized = self.get_personalized_recommendations(user_profile, limit=6)

        # 2. Trending / Most engaging notices
        trending = sorted(all_notices, key=lambda x: (x.get("views_count", 0) + x.get("bookmarks_count", 0) * 3), reverse=True)[:5]

        # 3. Urgent deadlines (due in next 7 days or Critical)
        critical_deadlines = []
        for n in all_notices:
            if n.get("priority") in ["Critical", "High"] and n.get("deadline"):
                critical_deadlines.append(n)
        critical_deadlines.sort(key=lambda x: x.get("deadline", "9999-99-99"))

        # 4. Department specific
        dept = user_profile.get("department", "Computer Science")
        dept_notices = [n for n in all_notices if n.get("department") == dept][:4]

        return {
            "personalized": personalized,
            "trending": trending,
            "critical_deadlines": critical_deadlines[:5],
            "department_notices": dept_notices
        }

recommendation_service = RecommendationService()
