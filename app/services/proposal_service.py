from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional, Protocol, Tuple

from app.models.proposal import Proposal, ProposalStatus
from app.repositories.proposal_repository import ProposalRepository

logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    def request_score(self, proposal: Proposal, timeout: float = 2.0) -> Tuple[Decimal, dict]:
        """Request a score from an external AI provider.

        Returns a tuple (score, explainability_metadata).
        """


class LocalFallback(Protocol):
    def compute(self, proposal: Proposal) -> Tuple[Decimal, dict]:
        """Compute a deterministic fallback score and metadata from domain rules."""


class ProposalService:
    """Service layer orchestrating proposal processing.

    This class depends only on abstractions: a `ProposalRepository`, an `AIProvider`
    and a `LocalFallback`. It attempts to obtain a score from the AI provider
    and falls back to the local rules engine on error or timeout. The final
    decision and score are persisted via the repository.
    """

    def __init__(
        self,
        repository: ProposalRepository,
        ai_provider: AIProvider,
        fallback: LocalFallback,
        approve_threshold: Decimal = Decimal("0.7"),
        reject_threshold: Decimal = Decimal("0.4"),
        ai_timeout: float = 2.0,
    ) -> None:
        self._repo = repository
        self._ai = ai_provider
        self._fallback = fallback
        self._approve_threshold = approve_threshold
        self._reject_threshold = reject_threshold
        self._ai_timeout = ai_timeout

    def process(self, proposal: Proposal) -> Proposal:
        """Process a proposal end-to-end.

        Steps:
        - persist initial proposal (status pending)
        - attempt AI scoring
        - on AI failure, compute local fallback score
        - determine decision (aprovado/negado/pendente)
        - persist final status, score and decision note

        Returns the updated Proposal instance as stored in the repository.
        """
        # Persist initial proposal (ensure it has an id and created_at)
        saved = self._repo.save(proposal)

        score: Decimal
        metadata: dict
        source: str

        # Try AI Provider
        try:
            logger.debug("Requesting score from AI provider for proposal %s", saved.id)
            score, metadata = self._ai.request_score(saved, timeout=self._ai_timeout)
            source = "ai"
            logger.debug("AI score=%s metadata=%s", score, metadata)
        except Exception as exc:  # pragma: no cover - provider failures are expected
            logger.warning("AI provider failed for proposal %s: %s", saved.id, exc)
            score, metadata = self._fallback.compute(saved)
            source = "fallback"
            logger.debug("Fallback score=%s metadata=%s", score, metadata)

        # Determine decision
        decision = self._decide(score)

        # Compose decision note
        decision_note = self._build_decision_note(source, metadata)

        # Persist final result
        updated = self._repo.update_status(
            saved.id, decision, decision_note=decision_note, score=score
        )

        return updated

    def _decide(self, score: Decimal) -> ProposalStatus:
        """Map a numerical score to a `ProposalStatus`.

        Decision thresholds are configurable via constructor.
        """
        if score >= self._approve_threshold:
            return ProposalStatus.aprovado
        if score < self._reject_threshold:
            return ProposalStatus.negado
        return ProposalStatus.pendente

    def _build_decision_note(self, source: str, metadata: Optional[dict]) -> str:
        """Create a compact decision note for auditability.

        The note includes the source (ai|fallback) and a short metadata summary.
        """
        meta_summary = ""
        try:
            if metadata:
                # prefer an explain key if available
                if isinstance(metadata, dict):
                    explain = metadata.get("explain") or metadata.get("explainability") or metadata
                    meta_summary = str(explain)
                else:
                    meta_summary = str(metadata)
        except Exception:  # defensive
            meta_summary = "(metadata-unavailable)"

        return f"source={source}; meta={meta_summary}"
