import json
import pybreaker

from groq import Groq

from app.core.config import GROQ_API_KEY
from app.schemas.triage import TriageResult
from app.services.symptom_service import (
    map_symptoms_to_specialization
)

# =====================================================
# 🔥 GROQ CLIENT
# =====================================================

client = Groq(
    api_key=GROQ_API_KEY
)

# =====================================================
# 🔥 CIRCUIT BREAKER
# =====================================================

breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30
)

# =====================================================
# 🔥 SYSTEM PROMPT
# =====================================================

SYSTEM_PROMPT = """
You are a medical emergency triage assistant.

You must return ONLY valid JSON.

Schema:
{
  "specializations": ["cardiology"],
  "severity": "critical",
  "confidence": 0.95,
  "requires_icu": true,
  "rationale": "reason"
}
"""

# =====================================================
# 🔥 FALLBACK TRIAGE
# =====================================================

def fallback_triage(symptoms: str):

    specializations = (
        map_symptoms_to_specialization(
            symptoms
        )
    )

    return TriageResult(
        specializations=specializations,
        severity="moderate",
        confidence=0.5,
        requires_icu=False,
        rationale="Fallback rule-based triage",
        source="fallback"
    )

# =====================================================
# 🔥 LLM CALL
# =====================================================

@breaker
def call_llm(symptoms: str):

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": symptoms
            }
        ],
        temperature=0
    )

    return response

# =====================================================
# 🔥 ANALYZE SYMPTOMS
# =====================================================

def analyze_symptoms(symptoms: str):

    try:

        response = call_llm(
            symptoms
        )

        raw_output = (
            response
            .choices[0]
            .message
            .content
        )

        print(
            "[RAW LLM OUTPUT]",
            raw_output
        )

        # ==========================================
        # 🔥 CLEANUP
        # ==========================================

        raw_output = (
            raw_output
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        # ==========================================
        # 🔥 PARSE JSON
        # ==========================================

        data = json.loads(
            raw_output
        )

        # ==========================================
        # 🔥 STRUCTURED RESULT
        # ==========================================

        result = TriageResult(
            specializations=data["specializations"],
            severity=data["severity"],
            confidence=data["confidence"],
            requires_icu=data["requires_icu"],
            rationale=data["rationale"],
            source="llm"
        )

        return result

    # ==============================================
    # 🔥 CIRCUIT BREAKER OPEN
    # ==============================================

    except pybreaker.CircuitBreakerError:

        print(
            "[CIRCUIT OPEN] Groq temporarily disabled"
        )

        return fallback_triage(
            symptoms
        )

    # ==============================================
    # 🔥 GENERAL FAILURE
    # ==============================================

    except Exception as e:

        print(
            "[LLM ERROR]",
            str(e)
        )

        return fallback_triage(
            symptoms
        )