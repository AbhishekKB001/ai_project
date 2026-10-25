import os
import json
from typing import Dict, Any, List, Optional
from ..config import load_settings

class LLMService:
    def __init__(self):
        pass

    def _get_api_keys(self):
        settings = load_settings()
        gemini_key = settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        claude_key = settings.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY") or ""
        return gemini_key.strip(), claude_key.strip()

    def _generate_with_gemini(self, client, contents: str):
        """Try gemini-3.8-flash, gemini-2.5-flash, then gemini-1.5-flash."""
        candidate_models = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
        last_err = None
        for mod in candidate_models:
            try:
                response = client.models.generate_content(
                    model=mod,
                    contents=contents
                )
                if response and response.text:
                    return response.text.strip(), mod
            except Exception as e:
                last_err = e
        if last_err:
            raise last_err
        return None, None

    def summarize_notice(self, notice: dict, preferred_model: str = "gemini") -> Dict[str, Any]:
        """
        Summarize a lengthy notice into 3 clear, actionable bullet points.
        Uses Gemini or Claude based on preferred_model.
        """
        gemini_key, claude_key = self._get_api_keys()
        prompt = (
            f"You are an AI assistant for a university/college smart notice board.\n"
            f"Analyze the following notice and generate a concise 3-bullet-point summary.\n"
            f"Bullet 1: Main objective/announcement.\n"
            f"Bullet 2: Key eligibility or requirements.\n"
            f"Bullet 3: Strict deadlines and action items.\n\n"
            f"Notice Title: {notice.get('title')}\n"
            f"Department: {notice.get('department')}\n"
            f"Category: {notice.get('category')}\n"
            f"Deadline: {notice.get('deadline')}\n"
            f"Full Content: {notice.get('content')}\n\n"
            f"Output only the 3 bullet points, clean and clear for students."
        )

        # Try Gemini if selected or available
        if preferred_model == "gemini" and gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                text, mod = self._generate_with_gemini(client, prompt)
                if text:
                    return {
                        "summary": text,
                        "engine": mod,
                        "status": "success"
                    }
            except Exception as e:
                print(f"Gemini API summarization error: {e}")

        # Try Claude if selected or available
        if (preferred_model == "claude" or not gemini_key) and claude_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=claude_key)
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = message.content[0].text
                return {
                    "summary": text.strip(),
                    "engine": "claude-3-5-sonnet",
                    "status": "success"
                }
            except Exception as e:
                print(f"Claude API summarization error: {e}")

        # Intelligent NLP Fallback (offline mode)
        title = notice.get("title", "")
        content = notice.get("content", "")
        deadline = notice.get("deadline", "Check notice details")
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 10]
        first_sentence = sentences[0] if sentences else content[:120]
        second_sentence = sentences[1] if len(sentences) > 1 else "Review all listed prerequisites before applying."

        fallback_summary = (
            f"• Announcement: {title} ({first_sentence.rstrip('.')}).\n"
            f"• Requirements: {second_sentence.rstrip('.')}.\n"
            f"• Action Required: Comply with mandatory guidelines by {deadline}."
        )
        return {
            "summary": fallback_summary,
            "engine": "rule-based-nlp-offline",
            "status": "offline_fallback",
            "note": "Connect Gemini or Claude API key in Settings for real-time generative summaries."
        }

    def chat_with_notice(
        self,
        notice: Optional[dict],
        user_message: str,
        history: List[dict] = None,
        model: str = "gemini"
    ) -> Dict[str, Any]:
        """
        Interactive Q&A assistant for notices.
        Allows users to ask specific questions about deadlines, eligibility, forms, etc.
        """
        gemini_key, claude_key = self._get_api_keys()
        
        notice_context = ""
        if notice:
            notice_context = (
                f"--- NOTICE DETAILS ---\n"
                f"ID: {notice.get('id')}\n"
                f"Title: {notice.get('title')}\n"
                f"Category: {notice.get('category')}\n"
                f"Department: {notice.get('department')}\n"
                f"Target Audience: {', '.join(notice.get('target_audience', []))}\n"
                f"Priority: {notice.get('priority')}\n"
                f"Deadline: {notice.get('deadline')}\n"
                f"Content: {notice.get('content')}\n"
                f"Tags: {', '.join(notice.get('tags', []))}\n"
                f"----------------------\n"
            )

        system_instruction = (
            "You are 'NoticeBot', a friendly and intelligent campus notice assistant. "
            "You answer student and faculty questions accurately using the provided notice context. "
            "If asked about dates, eligibility, or penalties, provide exact, highlighted answers. "
            "Keep answers concise, polite, and student-focused."
        )

        full_prompt = f"{system_instruction}\n\n{notice_context}\nStudent Question: {user_message}"

        # 1. Try Gemini
        if model == "gemini" and gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                text, mod = self._generate_with_gemini(client, full_prompt)
                if text:
                    return {
                        "reply": text,
                        "engine": mod,
                        "status": "success"
                    }
            except Exception as e:
                print(f"Gemini Chat Error: {e}")

        # 2. Try Claude
        if (model == "claude" or not gemini_key) and claude_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=claude_key)
                system_text = system_instruction
                messages = []
                if history:
                    for h in history[-4:]:
                        role = "user" if h.get("role") == "user" else "assistant"
                        messages.append({"role": role, "content": h.get("content", "")})
                messages.append({"role": "user", "content": f"{notice_context}\n\n{user_message}"})

                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=400,
                    system=system_text,
                    messages=messages
                )
                return {
                    "reply": msg.content[0].text.strip(),
                    "engine": "claude-3-5-sonnet",
                    "status": "success"
                }
            except Exception as e:
                print(f"Claude Chat Error: {e}")

        # 3. Intelligent fallback Q&A logic
        q_lower = user_message.lower()
        reply = ""
        if not notice:
            reply = (
                "Hello! I am your AI NoticeBot. You can select any notice to ask me specific questions "
                "about deadlines, required documents, eligibility, or exam schedules!"
            )
        else:
            title = notice.get("title", "")
            deadline = notice.get("deadline", "No fixed deadline specified")
            content = notice.get("content", "")
            audience = ", ".join(notice.get("target_audience", ["All Students"]))

            if any(k in q_lower for k in ["deadline", "last date", "when", "due date", "time"]):
                reply = f"📅 **Deadline Information**: For **{title}**, the deadline is **{deadline}**. Please ensure all submissions or registrations are completed before this date."
            elif any(k in q_lower for k in ["eligible", "who can", "eligibility", "allowed", "branch", "year"]):
                reply = f"🎓 **Eligibility**: This notice applies to **{audience}** in **{notice.get('department', 'All Departments')}**. Details from notice: '{content[:180]}...'"
            elif any(k in q_lower for k in ["fee", "fine", "penalty", "cost", "money", "pay"]):
                if "fee" in content.lower() or "fine" in content.lower():
                    reply = f"💰 **Fee/Penalty Details**: According to the circular: '{content}'"
                else:
                    reply = f"No special fee or monetary surcharge is mentioned in this notice ({title})."
            elif any(k in q_lower for k in ["where", "how to apply", "registration", "portal", "link", "submit"]):
                reply = f"📝 **Application / Next Steps**: {content}"
            else:
                reply = f"Regarding **{title}**:\n\n{content}\n\n*Deadline*: **{deadline}**\n*Department*: **{notice.get('department')}**"

        return {
            "reply": reply,
            "engine": "intelligent-offline-agent",
            "status": "offline_fallback",
            "note": "For dynamic multi-turn reasoning, enter your Gemini or Claude API key in settings."
        }

    def draft_notice(self, prompt: str, category: str = "General", department: str = "All Departments", urgency: str = "Medium", model: str = "gemini") -> Dict[str, Any]:
        """
        Draft an official notice from a rough prompt using Gemini or Claude.
        """
        gemini_key, claude_key = self._get_api_keys()

        system_prompt = (
            "You are an administrative director at an academic/corporate institution. "
            "Write a formal, comprehensive, professional official notice circular based on the user's brief. "
            "Include: Circular Header, Reference Number, Date, Clear Subject Line, Formal Opening, "
            "Detailed Guidelines/Rules in bullet points, Eligibility/Audience, Mandatory Deadlines, "
            "Penalties for non-compliance (if applicable), and Issuing Authority Signoff."
        )

        user_content = (
            f"Draft a notice with the following parameters:\n"
            f"- Prompt/Topic: {prompt}\n"
            f"- Category: {category}\n"
            f"- Department: {department}\n"
            f"- Urgency: {urgency}\n"
            f"Provide clean text formatting."
        )

        if model == "gemini" and gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                text, mod = self._generate_with_gemini(client, f"{system_prompt}\n\n{user_content}")
                if text:
                    return {
                        "draft": text,
                        "engine": mod,
                        "status": "success"
                    }
            except Exception as e:
                print(f"Gemini Draft Error: {e}")

        if (model == "claude" or not gemini_key) and claude_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=claude_key)
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=600,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}]
                )
                return {
                    "draft": msg.content[0].text.strip(),
                    "engine": "claude-3-5-sonnet",
                    "status": "success"
                }
            except Exception as e:
                print(f"Claude Draft Error: {e}")

        # Intelligent Fallback Draft Generator
        import datetime
        today_str = datetime.date.today().strftime("%B %d, %Y")
        draft_text = (
            f"COLLEGE OF ENGINEERING & TECHNOLOGY\n"
            f"OFFICE OF ACADEMIC & ADMINISTRATIVE AFFAIRS\n\n"
            f"REF NO: CET/ADMIN/2026/{urgency.upper()[:3]}-891\n"
            f"DATE: {today_str}\n\n"
            f"CIRCULAR: {prompt.upper()}\n\n"
            f"This is to bring to the notice of all concerned students and faculty members "
            f"belonging to {department} that the administration has issued the following directives:\n\n"
            f"1. {prompt}.\n"
            f"2. All affected individuals are requested to strictly adhere to the guidelines and schedule.\n"
            f"3. Respective departments will coordinate verification and document processing through the official portal.\n"
            f"4. Failure to comply within the stipulated time frame may attract administrative actions or penalties.\n\n"
            f"For further queries, reach out to the Department Helpdesk during official working hours.\n\n"
            f"By Order,\n"
            f"Dean of Academic Affairs"
        )
        return {
            "draft": draft_text,
            "engine": "intelligent-template-drafter",
            "status": "offline_fallback"
        }

llm_service = LLMService()
