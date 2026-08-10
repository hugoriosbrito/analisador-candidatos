# Clareza — Especificação de Produto e Arquitetura

## 1. Objetivo

Construir uma plataforma pública, apartidária e auditável para analisar debates, entrevistas e declarações de candidatos nas eleições brasileiras de 2026. O sistema deve transformar falas em afirmações verificáveis, pesquisar evidências em fontes primárias e secundárias, produzir uma avaliação estruturada, permitir revisão editorial humana e publicar uma cadeia de evidências reproduzível para o cidadão.

A plataforma não recomenda candidato, não produz ranking de honestidade e não personaliza conteúdo por ideologia política.

## 2. Princípios

1. **Evidência antes do veredito**: nenhuma avaliação é publicada sem evidências persistidas e citáveis.
2. **Auditabilidade**: toda avaliação registra fontes, trechos, datas de consulta, modelo/prompt utilizado, revisão e histórico de alteração.
3. **Mesmos critérios para todos**: seleção e avaliação de claims não usam identidade partidária como sinal de qualidade ou prioridade.
4. **Separação de fato e opinião**: opiniões, promessas, projeções e retórica são classificadas separadamente de fatos verificáveis.
5. **Human-in-the-loop**: avaliações geradas por IA ficam em estado editorial até aprovação humana.
6. **KISS/YAGNI**: o MVP não inclui contas públicas de usuário, feed personalizado, comentários, ranking de candidatos ou aplicativo móvel.
7. **Privacidade**: não inferir intenção de voto, ideologia ou perfil político.

## 3. Escopo funcional

### 3.1 Site público

- Página inicial com debates/entrevistas recentes, checagens recentes e busca.
- Página de evento com participantes, origem do vídeo, transcrição segmentada, timestamps e claims associadas.
- Página individual de claim com fala original, contexto, status, conclusão, resumo, explicação, confiança, evidências favoráveis/contrárias/contextuais e fontes.
- Página de metodologia.
- Página de candidato com declarações e eventos associados, sem score agregado.
- Busca por texto em claims, candidatos, eventos e tópicos.
- Histórico público de correções para avaliações publicadas.

### 3.2 Painel editorial

- CRUD básico de candidatos e eventos.
- Importação manual de transcrição em texto segmentado.
- Detecção automática de claims a partir de texto.
- Criação manual de claim.
- Pesquisa automática de uma claim.
- Visualização de evidências encontradas.
- Aprovação/rejeição editorial de uma avaliação.
- Publicação e correção de avaliações.

### 3.3 Research Engine

Fluxo obrigatório:

1. Receber uma claim atômica.
2. Construir plano de pesquisa estruturado.
3. Consultar provedor de busca configurável.
4. Baixar páginas por HTTP com limites de tamanho/tempo e proteção SSRF.
5. Persistir fonte e snapshot textual com hash SHA-256.
6. Extrair evidências relevantes.
7. Classificar postura da evidência: `SUPPORT`, `REFUTE`, `CONTEXT`, `NEUTRAL`.
8. Produzir avaliação sugerida com uma das classificações públicas.
9. Manter a avaliação como `AI_REVIEWED` até revisão humana.

O sistema deve funcionar sem credenciais externas em **modo demo/local**, usando dataset seed e heurísticas determinísticas. Com credenciais, usa um endpoint OpenAI-compatible e um provedor de busca HTTP configurável.

## 4. Taxonomia

### 4.1 Tipos de claim

- `FACTUAL_CLAIM`
- `PROJECTION`
- `PROMISE`
- `OPINION`
- `VALUE_JUDGMENT`
- `RHETORICAL`
- `ANECDOTAL`
- `ATTRIBUTION`
- `QUOTE`
- `NOT_CHECKABLE`

### 4.2 Vereditos públicos

- `SUPPORTED` — Sustentada
- `MOSTLY_SUPPORTED` — Majoritariamente sustentada
- `NEEDS_CONTEXT` — Requer contexto
- `UNSUPPORTED` — Não sustentada
- `FALSE` — Falsa
- `INCONCLUSIVE` — Inconclusiva
- `NOT_CHECKABLE` — Não verificável

### 4.3 Estados editoriais

- `DETECTED`
- `RESEARCHING`
- `AI_REVIEWED`
- `EDITORIAL_REVIEW`
- `PUBLISHED`
- `CORRECTED`
- `RETRACTED`

## 5. Arquitetura

Monorepo simples:

```text
apps/web          Next.js 15 + TypeScript
services/api      FastAPI + SQLAlchemy + Pydantic
workers/research  worker Python reutilizando domínio da API
infra             Docker Compose
```

Infraestrutura local:

- PostgreSQL 16 para dados transacionais.
- Redis 7 para fila.
- API FastAPI.
- Worker Celery.
- Next.js para site público e painel editorial.

O MVP não exige Kubernetes, Kafka, Elasticsearch nem serviço vetorial externo.

## 6. Modelo de dados

Entidades mínimas:

- `Candidate`
- `Event`
- `TranscriptSegment`
- `Claim`
- `Source`
- `Evidence`
- `Assessment`
- `EditorialReview`
- `Correction`
- `ModelRun`
- `AuditLog`

Regras:

- `Source` representa uma URL/documento real recuperado.
- `Evidence` sempre aponta para `Source`.
- `Assessment` nunca é publicada sem ao menos uma `Evidence`, exceto `NOT_CHECKABLE`.
- `Correction` preserva motivo e versão anterior.
- `ModelRun` registra provedor, modelo, prompt version e hashes de entrada/saída.

## 7. API

Prefixo `/api/v1`.

Endpoints públicos mínimos:

- `GET /health`
- `GET /candidates`
- `GET /candidates/{slug}`
- `GET /events`
- `GET /events/{slug}`
- `GET /claims`
- `GET /claims/{id}`
- `GET /search?q=`
- `GET /methodology`

Endpoints editoriais mínimos protegidos por `X-Admin-Key` no MVP:

- `POST /admin/candidates`
- `POST /admin/events`
- `POST /admin/events/{id}/transcript`
- `POST /admin/claims`
- `POST /admin/claims/detect`
- `POST /admin/claims/{id}/research`
- `POST /admin/claims/{id}/review`
- `POST /admin/claims/{id}/publish`
- `POST /admin/claims/{id}/corrections`

## 8. Segurança

- Todas as configurações por variáveis de ambiente.
- Nenhum segredo commitado.
- Proteção SSRF no fetcher: apenas `http/https`, bloquear hosts locais, loopback, link-local e redes privadas após resolução DNS.
- Limite de download e timeout por request.
- HTML de fontes tratado como dado não confiável; nunca como instrução de sistema.
- Admin protegido por chave no MVP e pronto para migração futura a OIDC/RBAC.
- CORS configurável.
- Logs sem chaves/segredos.

## 9. IA e provedores

Interface de LLM OpenAI-compatible, configurada por:

- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`

Quando ausentes, usar `DemoLLM`, determinístico.

Interface de busca:

- `SEARCH_PROVIDER=demo|brave`
- `BRAVE_SEARCH_API_KEY`

Quando não houver chave, usar `DemoSearchProvider` com fontes seed auditáveis.

Toda saída de LLM que altera domínio deve ser validada por schema Pydantic; texto livre do modelo nunca escreve diretamente no banco.

## 10. Frontend

Diretrizes:

- Design editorial sóbrio e responsivo.
- Sem cores partidárias como linguagem primária.
- Veredito exposto por texto e badge, não apenas cor.
- Fonte e timestamp sempre visíveis na página da claim.
- Painel editorial em `/admin`.
- Client público lê a API por `NEXT_PUBLIC_API_URL`.

Páginas do MVP:

- `/`
- `/debates`
- `/debates/[slug]`
- `/checagens`
- `/checagens/[id]`
- `/candidatos`
- `/candidatos/[slug]`
- `/metodologia`
- `/admin`

## 11. Testes e qualidade

Backend:

- Pytest para domínio, API e segurança do fetcher.
- Testes de regra de publicação e detecção de claims.
- Teste do modo demo fim a fim no nível da API.

Frontend:

- Vitest para utilitários/componentes críticos.
- Build do Next.js obrigatório no CI.

CI:

- `ruff check`
- `pytest`
- `npm ci`
- `npm run lint`
- `npm run test`
- `npm run build`

## 12. Seed/demo

O repositório deve subir com dados fictícios claramente identificados como demonstração, sem atribuir declarações falsas a candidatos reais.

O seed deve incluir:

- 2 candidatos fictícios;
- 1 debate fictício;
- segmentos de transcrição;
- 3 claims;
- evidências seed;
- ao menos uma avaliação publicada.

## 13. Execução local

Comandos-alvo:

```bash
cp .env.example .env
docker compose up --build
```

Serviços:

- Web: `http://localhost:3000`
- API/OpenAPI: `http://localhost:8000/docs`
- PostgreSQL: interno + porta configurável
- Redis: interno + porta configurável

O projeto deve possuir `Makefile` com comandos `up`, `down`, `test`, `lint`, `seed`.

## 14. Critério de conclusão do MVP

Considerar o repositório funcional quando uma instalação limpa consegue:

1. subir todos os serviços via Docker Compose;
2. carregar dados seed;
3. navegar pelo site público;
4. criar evento e claim via API editorial;
5. executar pesquisa em modo demo;
6. revisar e publicar uma avaliação;
7. recuperar a claim publicada com evidências pela API e pela UI;
8. executar testes automatizados e build em CI.
