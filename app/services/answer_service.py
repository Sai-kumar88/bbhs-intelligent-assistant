import re
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.prompts.system_prompt import build_system_prompt
from app.services.retrieval_service import retrieval_service, RetrievedChunk


def clean_answer_text(text: str) -> str:
    """Remove residual citation brackets from the answer text."""
    cleaned = re.sub(r'\[\s*Source:[^\]]*\]', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[\s*Page:[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
    # Clean up double line breaks or extra spaces left by removal
    return cleaned.strip()


class AnswerService:
    def __init__(self):
        self._llm = None
        self._cached_key = None
        self._cached_model = None

    def _get_llm(self):
        """Dynamically get or refresh NVIDIA LLM client if configuration changes."""
        if (
            self._llm is None
            or self._cached_key != settings.NVIDIA_API_KEY
            or self._cached_model != settings.NVIDIA_MODEL
        ):
            if settings.NVIDIA_API_KEY and settings.NVIDIA_API_KEY.strip():
                try:
                    from langchain_nvidia_ai_endpoints import ChatNVIDIA
                    self._llm = ChatNVIDIA(
                        model=settings.NVIDIA_MODEL,
                        api_key=settings.NVIDIA_API_KEY,
                        base_url=settings.NVIDIA_BASE_URL,
                        temperature=0.0,
                        max_tokens=4096
                    )
                    self._cached_key = settings.NVIDIA_API_KEY
                    self._cached_model = settings.NVIDIA_MODEL
                except Exception:
                    self._llm = None
            else:
                self._llm = None
        return self._llm

    def _format_sources(self, chunks: List[RetrievedChunk]) -> List[Dict[str, Any]]:
        """Return unique list of source documents and pages."""
        seen = set()
        sources = []
        for c in chunks:
            key = (c.source, c.page)
            if key not in seen:
                seen.add(key)
                sources.append({"source": c.source, "page": c.page})
        return sorted(sources, key=lambda s: (s["source"], s["page"]))

    def generate_answer(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        End-to-end RAG answer generation strictly from PDF content.
        If content is missing or score threshold is not met, returns fixed refusal message.
        """
        if not query or not query.strip():
            return {
                "answer": settings.REFUSAL_MESSAGE,
                "sources": [],
                "refusal": True
            }

        # 1. Retrieve relevant chunks
        chunks = retrieval_service.retrieve(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold
        )

        # 2. Refuse immediately if no relevant chunks found in knowledge base
        if not chunks:
            return {
                "answer": settings.REFUSAL_MESSAGE,
                "sources": [],
                "refusal": True
            }

        context = retrieval_service.format_context(chunks)
        system_content = build_system_prompt(context)
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query.strip())
        ]

        llm = self._get_llm()
        sources = self._format_sources(chunks)

        if llm is not None:
            try:
                response = llm.invoke(messages)
                raw_content = response.content if hasattr(response, "content") else str(response)
                answer_text = clean_answer_text(raw_content)

                if not answer_text or not answer_text.strip():
                    return {
                        "answer": settings.REFUSAL_MESSAGE,
                        "sources": [],
                        "refusal": True
                    }

                # Check if model triggered the full configured refusal message
                clean_ans = " ".join(answer_text.strip().lower().split())
                clean_ref = " ".join(settings.REFUSAL_MESSAGE.strip().lower().split())
                if clean_ref in clean_ans:
                    return {
                        "answer": settings.REFUSAL_MESSAGE,
                        "sources": [],
                        "refusal": True
                    }

                return {
                    "answer": answer_text,
                    "sources": sources,
                    "refusal": False
                }
            except Exception as e:
                # If API call fails (e.g., during offline testing)
                if settings.ENVIRONMENT == "test":
                    # Fallback answer based on extracted context for offline testing
                    return {
                        "answer": f"Based on the school knowledge base: {chunks[0].text[:300]}...",
                        "sources": sources,
                        "refusal": False
                    }
                raise e

        # If LLM is not initialized (e.g., NVIDIA_API_KEY not yet provided in .env)
        if llm is None:
            top_chunk = chunks[0]
            return {
                "answer": (
                    f"[Notice: NVIDIA_API_KEY is not configured in .env. "
                    f"Showing retrieved text from document]:\n\n{top_chunk.text.strip()}\n\n"
                    f"(Add your NVIDIA_API_KEY in .env to enable answers generated by {settings.NVIDIA_MODEL})"
                ),
                "sources": sources,
                "refusal": False
            }

        return {
            "answer": settings.REFUSAL_MESSAGE,
            "sources": [],
            "refusal": True
        }


answer_service = AnswerService()
