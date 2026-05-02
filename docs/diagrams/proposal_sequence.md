```mermaid
sequenceDiagram
  participant Client
  participant API as "API (Controller)"
  participant Service as "Service (Usecase)"
  participant Domain as "Domain (Rules / Fallback)"
  participant Repo as "Repository (Persistence)"
  participant AI as "AI Provider"

  Client->>API: POST /proposals {payload}
  API->>Service: validate payload & create request
  Service->>Repo: INSERT request (status: pending)
  Note right of Repo: persist request_id, payload_hash, timestamp

  Service->>AI: requestScore(payload) [timeout=2s]
  loop retry (up to N attempts)
    AI-->>Service: score + explainability
  end

  alt AI responds within timeout
    Service->>Domain: apply domain rules + combine AI score
    Domain-->>Service: decision, explainability_enhanced
    Service->>Repo: UPDATE result (score, decision, source: ai, model_version, metadata)
    Service-->>API: respond {request_id, score, decision, source: ai}
    API-->>Client: 200 OK
  else AI fails / timeout / circuit-breaker open
    Note over Service,Domain: fallback to deterministic rules engine
    Service->>Domain: computeFallbackScore(payload)
    Domain-->>Service: fallback_score, decision, explainability
    Service->>Repo: UPDATE result (score, decision, source: fallback, metadata)
    Service-->>API: respond {request_id, score, decision, source: fallback}
    API-->>Client: 200 OK
  end

  Note over AI: retry/backoff, timeout and circuit-breaker policies<br/>(e.g. exponential backoff, open after X failures)