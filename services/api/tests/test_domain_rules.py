from app.domain.enums import Verdict
from app.domain.rules import can_publish_assessment
def test_publication_requires_editorial_approval_and_evidence():
    assert not can_publish_assessment(Verdict.SUPPORTED,1,False)
    assert not can_publish_assessment(Verdict.SUPPORTED,0,True)
    assert can_publish_assessment(Verdict.SUPPORTED,1,True)
def test_not_checkable_is_only_no_evidence_exception():
    assert can_publish_assessment(Verdict.NOT_CHECKABLE,0,True)
    assert not can_publish_assessment(Verdict.INCONCLUSIVE,0,True)
