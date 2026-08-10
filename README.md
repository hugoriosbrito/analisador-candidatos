# Clareza

Plataforma aberta para análise auditável de debates, entrevistas e declarações políticas. O Clareza organiza **afirmação → pesquisa → evidências → avaliação → revisão editorial → publicação**, sem recomendar candidatos ou criar ranking de honestidade.

> O seed incluído no repositório usa exclusivamente nomes, instituições e dados fictícios.

## Stack

- Next.js 15 + TypeScript
- FastAPI + SQLAlchemy + Pydantic
- PostgreSQL 16
- Redis 7 + Celery
- Pesquisa demo local e integração opcional com Brave Search
- LLM via endpoint OpenAI-compatible, com fallback demo determinístico
- Docker Compose + GitHub Actions

## Rodar localmente

```bash
cp .env.example .env
# troque ADMIN_KEY antes de expor o ambiente
docker compose up --build
```

Em outro terminal:

```bash
docker compose run --rm api python seed.py
```

Acesse:

- Site: http://localhost:3000
- API/OpenAPI: http://localhost:8000/docs
- Painel editorial: http://localhost:3000/admin

## Modo demo

`SEARCH_PROVIDER=demo` permite executar o pipeline sem credenciais externas. Ele demonstra o fluxo técnico com fontes e conteúdo fictícios; **não deve ser interpretado como pesquisa factual real**.

## Pesquisa real

Para habilitar busca web via Brave Search:

```env
SEARCH_PROVIDER=brave
BRAVE_SEARCH_API_KEY=...
```

Para habilitar análise por qualquer endpoint compatível com Chat Completions da OpenAI:

```env
LLM_BASE_URL=https://seu-endpoint.example/v1
LLM_API_KEY=...
LLM_MODEL=seu-modelo
```

O LLM recebe apenas as fontes recuperadas e devolve índices dessas fontes; URLs inventadas pelo modelo não entram no `Evidence Store`. Cada execução registra `provider`, modelo, versão do prompt e hashes de entrada/saída em `ModelRun`.

## Fluxo editorial

1. `POST /api/v1/admin/claims`
2. `POST /api/v1/admin/claims/{id}/research`
3. `POST /api/v1/admin/claims/{id}/review`
4. `POST /api/v1/admin/claims/{id}/publish`
5. `POST /api/v1/admin/claims/{id}/corrections` quando necessário

O painel `/admin` executa criação, pesquisa, aprovação/rejeição e publicação. Endpoints admin exigem `X-Admin-Key`.

## Regras de publicação

- `NOT_CHECKABLE` pode ser publicado sem evidência, após revisão editorial.
- Todo outro veredito exige ao menos uma evidência persistida.
- Toda publicação exige aprovação editorial humana.
- Correções são registradas em entidade própria e a claim muda para `CORRECTED`.

## Segurança

O projeto inclui validação de URL contra SSRF (loopback, RFC1918, link-local, multicast, reserved e esquemas não HTTP), CORS configurável, segredo administrativo via ambiente e nenhuma credencial no repositório. Conteúdo recuperado da web é tratado como dado não confiável.

## Desenvolvimento

```bash
make test
make lint
```

Backend isolado:

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Frontend isolado:

```bash
cd apps/web
npm install
npm test
npm run lint
npm run build
```

## Documentação de arquitetura

- `docs/superpowers/specs/2026-08-10-clareza-design.md`
- `docs/superpowers/plans/2026-08-10-clareza-mvp.md`

## Gates antes de uso eleitoral real

O MVP já executa o fluxo funcional, mas uma operação eleitoral real ainda exige: corpus/conectores estruturados de fontes públicas brasileiras, evals editoriais do modelo escolhido, autenticação OIDC/RBAC para editores, observabilidade, backups/PITR, revisão jurídica eleitoral e política editorial pública completa.
