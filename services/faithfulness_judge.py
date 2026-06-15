"""Real-time faithfulness scoring using Gemini Flash."""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

_JUDGE_PROMPT = """You are an impartial faithfulness evaluator. Given an ANSWER and the SOURCE CONTEXT it was generated from, score how well the answer is supported by the context.

Rules:
- 1.0 = every claim in the answer is directly supported by the context
- 0.5 = some claims are supported, others are not
- 0.0 = the answer is not supported by the context at all

Respond with ONLY a single decimal number between 0.0 and 1.0. No explanation.

CONTEXT:
{context}

ANSWER:
{answer}

SCORE:"""


class FaithfulnessJudge:
    """Score answer faithfulness using Gemini Flash."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set.")

        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def score(self, answer: str, context: str) -> float | None:
        """Return a faithfulness score between 0.0 and 1.0, or None on failure."""
        try:
            prompt = _JUDGE_PROMPT.format(context=context[:4000], answer=answer[:1000])
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            text = response.text.strip()
            match = re.search(r"(\d+\.?\d*)", text)
            if match:
                score = float(match.group(1))
                return round(min(max(score, 0.0), 1.0), 2)
            return None
        except Exception as e:
            logger.warning("Faithfulness scoring failed: %s", e)
            return None
