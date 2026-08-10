from .enums import Verdict

def can_publish_assessment(verdict: Verdict, evidence_count: int, editorial_approved: bool) -> bool:
    if not editorial_approved:
        return False
    return verdict == Verdict.NOT_CHECKABLE or evidence_count > 0
