from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Assessment, Candidate, Claim, Event, Evidence, Source, TranscriptSegment
from app.domain.enums import ClaimStatus, EvidenceStance, SourceType, Verdict


def seed_database(session: Session) -> None:
    if session.scalar(select(Candidate.id).limit(1)):
        return
    a = Candidate(name="Marina Horizonte", slug="marina-horizonte", party="FICTÍCIO")
    b = Candidate(name="Rafael Aurora", slug="rafael-aurora", party="FICTÍCIO")
    event = Event(
        title="Debate Demonstrativo",
        slug="debate-demonstrativo",
        event_type="DEBATE",
        source_url="https://example.org/debate-demo",
    )
    session.add_all([a, b, event])
    session.flush()
    session.add(
        TranscriptSegment(
            event_id=event.id,
            candidate_id=a.id,
            start_ms=12000,
            end_ms=20000,
            text="No cenário demonstrativo, o indicador Alfa cresceu 10% em 2025.",
        )
    )
    c1 = Claim(
        text="O indicador Alfa cresceu 10% em 2025.",
        candidate_id=a.id,
        event_id=event.id,
        topic="economia",
        status=ClaimStatus.PUBLISHED.value,
        start_ms=12000,
    )
    c2 = Claim(
        text="Vamos criar o Programa Horizonte.",
        candidate_id=b.id,
        event_id=event.id,
        topic="políticas públicas",
    )
    c3 = Claim(
        text="O indicador Beta caiu no período demonstrativo.",
        candidate_id=b.id,
        event_id=event.id,
        topic="economia",
    )
    session.add_all([c1, c2, c3])
    session.flush()
    source = Source(
        url="https://example.org/dados-demo",
        title="Base estatística demonstrativa",
        publisher="Instituto Fictício de Estatística",
        source_type=SourceType.PRIMARY_OFFICIAL.value,
        snapshot_text="Indicador Alfa: crescimento de 10% em 2025 no conjunto fictício.",
    )
    session.add(source)
    session.flush()
    session.add(
        Evidence(
            claim_id=c1.id,
            source_id=source.id,
            excerpt="Indicador Alfa: crescimento de 10% em 2025 no conjunto fictício.",
            stance=EvidenceStance.SUPPORT.value,
        )
    )
    session.add(
        Assessment(
            claim_id=c1.id,
            verdict=Verdict.SUPPORTED.value,
            summary="Os dados fictícios do ambiente de demonstração sustentam a afirmação.",
            explanation=(
                "Esta checagem existe apenas para demonstrar o fluxo técnico do Clareza e não representa uma "
                "declaração política real."
            ),
            confidence="HIGH",
            editorial_approved=True,
            published_at=datetime.now(timezone.utc),
        )
    )
    session.commit()
