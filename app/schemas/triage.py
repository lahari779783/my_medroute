from pydantic import BaseModel
from typing import List


class TriageResult(BaseModel):
    specializations: List[str]
    severity: str
    confidence: float
    requires_icu: bool
    rationale: str
    source: str