# Backlog Mínimo — Releases e Itens

## Release: Core

- [ ] RF-01: Submissão de Proposta — Aceite: `POST /proposals` valida payload, retorna `request_id` e 202/200; testes unitários de validação (schema) e integração básica.
- [ ] RF-02: Processamento de Scoring (IA) — Aceite: orquestrador envia para provider com timeout configurável; resultado armazena `score`, `source` e `model_version`; mock tests cobrindo sucesso AI.
- [ ] RF-03: Fallback Local (Rules Engine) — Aceite: quando provider indisponível, calcular score determinístico com resultado `source: fallback`; regras cobertas por testes unitários.
- [ ] RT-01: Persistência Mínima (SQLite) — Aceite: migrations aplicáveis (Alembic), tabelas para requests/results, consultas por `request_id` funcionais.
- [ ] RT-02: Endpoint /health — Aceite: `GET /health` retorna 200 com `status: ok` e `timestamp`; teste automatizado.
- [ ] RT-03: Estrutura de projeto (Clean Architecture) — Aceite: pastas `api/`, `services/`, `domain/`, `repositories/` existentes com arquivos iniciadores e exemplos mínimos.

## Release: Qualidade

- [ ] RF-04: Consulta de Score — Aceite: `GET /scores/{request_id}` retorna `score`, `decision`, `explainability` e `metadata`; contrato testado por integrações.
- [ ] RT-04: Observabilidade e Logs Estruturados — Aceite: logs com `request_id`; exposição básica de métricas em `/metrics` (Prometheus) e testes manuais de scraping.
- [ ] RT-05: Testes e CI local — Aceite: `pytest` com cobertura mínima para domínio e endpoints; workflow local de CI que roda lint, mypy e testes.
- [ ] RT-06: Timeouts e Retry — Aceite: chamadas ao provider com timeout e retry/backoff testados via mocks; circuit-breaker simples implementado.

## Release: Entrega Final

- [ ] RF-05: Histórico e Auditoria — Aceite: endpoints/queries que retornam histórico de requests e metadados (model_version, provider_response_id), com paginação básica.
- [ ] RT-07: Migração para Postgres (opcional) — Aceite: configuração de conexão, migrations aplicadas e testes de integração com Postgres (CI ou local via Docker).
- [ ] RT-08: Segurança Básica e Configuração de Segredos — Aceite: uso de `.env` para segredos, documentação de como configurar secrets/vars em produção; não comitar chaves.
- [ ] RT-09: Dockerização e README de deploy — Aceite: `Dockerfile` e `docker-compose.yml` com serviços mínimos (app + db) e instruções de execução.

---

Cada item deve ter critérios de aceite claros e testes automatizados quando aplicável. Priorizar Core → Qualidade → Entrega Final.
