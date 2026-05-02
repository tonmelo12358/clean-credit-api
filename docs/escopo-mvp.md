# Escopo Técnico — MVP CleanCredit API

## Objetivo Geral

Fornecer um Motor de Avaliação de Risco de Crédito resiliente para uso em ambiente de laboratório e POC acadêmico. O objetivo é permitir a avaliação automatizada de propostas de crédito combinando uma camada preditiva baseada em IA com um mecanismo de fallback determinístico local, garantindo disponibilidade, auditabilidade e rastreabilidade mínima necessária para avaliação técnica.

## Contexto

O sistema adota Clean Architecture e DDD para separar responsabilidades entre API, Application/Service, Domain e Repository. A implementação inicial utiliza FastAPI (ASGI) e SQLite para ambiente de desenvolvimento e prototipação.

## Funcionalidades Principais (Visão de Alto Nível)

- Receber propostas de crédito (payload do solicitante e parâmetros do empréstimo).
- Gerar score de risco usando um provedor de IA externo (camada Provider).  
- Calcular score de fallback local baseado em regras de negócio codificadas (políticas puras no domínio).  
- Fornecer endpoint de consulta de score e histórico mínimo (request id, source, timestamp).  
- Expor endpoint de saúde e métricas básicas para observabilidade.

## Requisitos Funcionais (RF)

- RF-01: Submissão de Proposta
  - Descrição: API que aceita POST /proposals com dados do candidato e do pedido de crédito.  
  - Entrada: identificador do solicitante, renda, idade, histórico resumido (campos mínimos definidos).  
  - Saída: `request_id` e status `received` (aceite para processamento assíncrono ou sincrono no MVP).

- RF-02: Processamento de Scoring (IA)
  - Descrição: Serviço orquestrador que envia os dados para o `AI Provider` e recebe um `score` e explicabilidade mínima (fatores).  
  - Comportamento: chamadas protegidas por timeout e retry; metadata do modelo armazenada no resultado.

- RF-03: Fallback Local (Rules Engine)
  - Descrição: Em caso de indisponibilidade do provider IA ou quando flag `ENABLE_AI=false`, calcular score local com regras determinísticas implementadas no `domain`.  
  - Requisitos: regras testáveis, com cobertura unitária; retorno com campo `source: fallback`.

- RF-04: Consulta de Score
  - Descrição: GET /scores/{request_id} retorna o score consolidado, `decision` (auto/decline/manual_review), `explainability` e `metadata` (source, model_version, timestamp).  

- RF-05: Health & Observability
  - Descrição: endpoint GET /health que verifica status da aplicação; métricas em /metrics (Prometheus) e logs estruturados para solicitações de scoring.

- RF-06: Persistência Mínima
  - Descrição: Persistir requests e resultados em DB (SQLite no MVP) com esquema que permita auditoria básica (request_id, payload hash, result, source, timestamp).

## Requisitos Não-Funcionais (RNF)

- RNF-01: Performance e Concurrency
  - O serviço deve ser executado com Uvicorn (ASGI) configurado para ambientes de desenvolvimento com `--reload` e para staging/produção com workers adequados.  
  - Metas iniciais: latência p95 do endpoint de consulta < 200ms para respostas em cache/local; chamadas à IA devem respeitar timeout configurável (ex.: 2s) e não bloquear worker principal.

- RNF-02: Integridade de Dados
  - Garantir persistência atômica das operações de gravação relevantes (requests e resultados).  
  - Manter esquema versionado (migration scripts via Alembic).  
  - Persistir metadados para auditoria (model_version, provider_response_id, request_id, timestamp).

- RNF-03: Tipagem Estática e Qualidade de Código
  - Código deve ser compatível com `mypy` em nível básico; seguir `black` e `ruff` como formatadores/linter.  
  - Modelos de domínio e DTOs devem ser fortemente tipados com Pydantic/SQLModel.

- RNF-04: Resiliência e Observabilidade
  - Implementar timeouts, retry com backoff e um padrão simples de circuit-breaker para o provider IA.  
  - Expor métricas (contadores de falhas, latências, percentage of fallback usage) e logs estruturados para correlação (request_id).

- RNF-05: Segurança Básica
  - Não incluir autenticação complexa neste MVP; porém garantir que segredos (API keys) sejam carregados via `.env` e não comitados.  
  - Não logar PII sensível em texto plano.

## Fora de Escopo (para esta versão MVP)

- Integrações complexas com bureaus de crédito externos (ex.: Serasa, SPC, outros) — essas integrações ficam para versões futuras e POCs dirigidas com dados reais.  
- Autenticação e autorização robusta (OAuth2/OIDC, RBAC) — não implementadas no MVP; será adicionada em iterações que envolvam produção.  
- Processamento e retenção de grandes volumes de dados (pipeline de Big Data).  
- Machine learning training pipelines; o MVP apenas consome modelos via provider ou regras estáticas locais.

## Critérios de Aceitação do MVP

- Endpoints documentados e testáveis: POST /proposals, GET /scores/{id}, GET /health.  
- Fluxo IA + fallback implementado e coberto por testes unitários que validem ambas as fontes (`source: ai` e `source: fallback`).  
- Persistência mínima funcionando com migrations e queries básicas suportadas.  
- Linter e type check passando em pipelines locais (black/ruff/mypy).  

## Entregáveis da Versão MVP

- Código-fonte com estrutura de pastas conforme Clean Architecture.  
- `README.md` técnico, `requirements.txt` e `Dockerfile` (opcional).  
- Testes unitários para domínio e endpoint `/health` e fluxo básico de scoring.  
- Documento de escopo (`docs/escopo-mvp.md`) e exemplos de requests.

## Riscos Principais

- Dependência de provider IA: latência ou custos inesperados — mitigado via fallback.  
- Inconsistência de formatos de dados entre provider e domínio — mitigado com adaptações e validações no Adapter.  
- SQLite limitado para carga; migrar para Postgres em próxima versão.

---

Documento preparado para stakeholders técnicos, equipe de desenvolvimento e avaliadores. Este escopo define fronteiras claras para entrega do MVP e prioriza resiliência operacional sobre integrações externas complexas.
