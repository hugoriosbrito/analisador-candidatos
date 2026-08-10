# Clareza MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um MVP funcional do Clareza com site público, painel editorial, API, pesquisa em modo demo, persistência, filas, Docker e CI.

**Architecture:** Monorepo com Next.js no frontend, FastAPI no backend, PostgreSQL como banco, Redis/Celery para jobs e um domínio explícito de claims/evidências/avaliações. Provedores de LLM e busca ficam atrás de interfaces e possuem implementações demo determinísticas para o sistema funcionar sem credenciais.

**Tech Stack:** Next.js 15, React 19, TypeScript, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL 16, Redis 7, Celery 5, Pytest, Ruff, Vitest, Docker Compose, GitHub Actions.

## Global Constraints

- Não recomendar candidato nem criar ranking de honestidade.
- Nenhuma avaliação publicada sem evidência persistida, exceto `NOT_CHECKABLE`.
- Human-in-the-loop obrigatório antes de `PUBLISHED`.
- Saídas de LLM validadas por Pydantic antes de afetar domínio.
- Dados seed são integralmente fictícios.
- Admin protegido por `X-Admin-Key` no MVP.
- Fetcher bloqueia SSRF para redes locais/privadas/link-local/loopback.
- O sistema deve operar sem chaves externas em modo demo.

---

### Task 1: Backend domain and publication rules

**Files:**
- Create: `services/api/pyproject.toml`
- Create: `services/api/app/domain/enums.py`
- Create: `services/api/app/domain/schemas.py`
- Create: `services/api/app/domain/rules.py`
- Create: `services/api/tests/test_domain_rules.py`

**Interfaces:**
- Produces `can_publish_assessment(verdict: Verdict, evidence_count: int, editorial_approved: bool) -> bool`.
- Produces enums `ClaimType`, `ClaimStatus`, `Verdict`, `EvidenceStance`, `SourceType`.

- [ ] Write tests proving evidence + editorial approval are required and `NOT_CHECKABLE` is the only no-evidence exception.
- [ ] Run `pytest services/api/tests/test_domain_rules.py -v` and confirm failure before implementation.
- [ ] Implement minimal enums/schemas/rules.
- [ ] Re-run test and confirm pass.

### Task 2: Persistence and seed

**Files:**
- Create: `services/api/app/core/config.py`
- Create: `services/api/app/db/base.py`
- Create: `services/api/app/db/models.py`
- Create: `services/api/app/db/session.py`
- Create: `services/api/app/db/seed.py`
- Create: `services/api/tests/test_seed.py`

**Interfaces:**
- Produces SQLAlchemy models `Candidate`, `Event`, `TranscriptSegment`, `Claim`, `Source`, `Evidence`, `Assessment`, `EditorialReview`, `Correction`, `ModelRun`, `AuditLog`.
- Produces `seed_database(session) -> None`.

- [ ] Write SQLite-backed test asserting fictitious seed entities and one published assessment exist.
- [ ] Confirm test fails.
- [ ] Implement models and deterministic seed.
- [ ] Confirm test passes.

### Task 3: Demo research engine

**Files:**
- Create: `services/api/app/research/providers.py`
- Create: `services/api/app/research/schemas.py`
- Create: `services/api/app/research/service.py`
- Create: `services/api/tests/test_research.py`

**Interfaces:**
- `SearchProvider.search(query: str) -> list[SearchResult]`.
- `LLMProvider.analyze(claim: str, sources: list[SearchResult]) -> ResearchAnalysis`.
- `research_claim(claim_text: str, search: SearchProvider, llm: LLMProvider) -> ResearchAnalysis`.

- [ ] Write deterministic research test using demo providers.
- [ ] Confirm RED.
- [ ] Implement providers and service.
- [ ] Confirm GREEN.

### Task 4: SSRF-safe source fetcher

**Files:**
- Create: `services/api/app/research/fetcher.py`
- Create: `services/api/tests/test_fetcher_security.py`

**Interfaces:**
- `validate_public_url(url: str) -> str` rejects unsupported schemes and private/local addresses.

- [ ] Write tests for localhost, 127.0.0.1, RFC1918, link-local and valid public HTTPS URL.
- [ ] Confirm RED.
- [ ] Implement URL validation with DNS resolution and `ipaddress` checks.
- [ ] Confirm GREEN.

### Task 5: FastAPI public/editorial API

**Files:**
- Create: `services/api/app/main.py`
- Create: `services/api/app/api/deps.py`
- Create: `services/api/app/api/public.py`
- Create: `services/api/app/api/admin.py`
- Create: `services/api/tests/test_api.py`

**Interfaces:**
- Public endpoints listed in the design spec.
- Admin mutation endpoints protected by `X-Admin-Key`.

- [ ] Write API tests for health, list claims, reject missing admin key, create/research/review/publish claim.
- [ ] Confirm RED.
- [ ] Implement API and workflow.
- [ ] Confirm GREEN.

### Task 6: Celery worker

**Files:**
- Create: `workers/research/worker.py`
- Create: `workers/research/Dockerfile`

**Interfaces:**
- Celery task `research_claim_task(claim_id: int)` calling backend research service against shared DB.

- [ ] Implement after API workflow is green; task reuses service and contains no duplicated domain rules.

### Task 7: Public/admin web application

**Files:**
- Create Next.js app under `apps/web/` including `package.json`, config, global styles, API client and pages `/`, `/debates`, `/debates/[slug]`, `/checagens`, `/checagens/[id]`, `/candidatos`, `/candidatos/[slug]`, `/metodologia`, `/admin`.
- Create: `apps/web/src/lib/verdict.ts`
- Create: `apps/web/src/lib/verdict.test.ts`

**Interfaces:**
- Reads `NEXT_PUBLIC_API_URL`.
- Admin sends `X-Admin-Key` only from explicit editor input/local session; no secret embedded in build.

- [ ] Write Vitest tests for verdict labels before implementation.
- [ ] Build reusable editorial cards/tables.
- [ ] Implement public pages and simple admin workflow.
- [ ] Run lint, test and production build.

### Task 8: Containers, operations and CI

**Files:**
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `services/api/Dockerfile`
- Create: `apps/web/Dockerfile`
- Create: `Makefile`
- Create: `.github/workflows/ci.yml`
- Create: `.gitignore`
- Create/Update: `README.md`

**Interfaces:**
- `docker compose up --build` starts postgres, redis, api, worker and web.
- `make test`, `make lint`, `make seed`, `make up`, `make down`.

- [ ] Add container/config files.
- [ ] Add CI backend and frontend jobs.
- [ ] Document setup, architecture, demo credentials and production integrations.

### Task 9: Verification

- [ ] Run backend tests.
- [ ] Run Ruff.
- [ ] Run frontend tests/lint/build.
- [ ] Inspect Docker Compose config.
- [ ] Verify no credential-like strings are committed.
- [ ] Verify repository tree and README instructions match actual commands.
