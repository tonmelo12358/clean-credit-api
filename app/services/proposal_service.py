from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, List, Optional, Protocol, Tuple
from uuid import UUID

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
        saved = self._repo.save(proposal)

        score, metadata, source = self._get_score_from_providers(saved)
        status = self._decide(score)
        
        return self._repo.update_status(
            id=saved.id,
            status=status,
            decision_note=self._build_decision_note(source, metadata),
            score=score
        )

    def _get_score_from_providers(self, proposal: Proposal) -> Tuple[Decimal, dict, str]:
        """Handles AI provider call with safe fallback logic."""
        try:
            logger.debug("Requesting AI score for proposal %s", proposal.id)
            score, metadata = self._ai.request_score(proposal, timeout=self._ai_timeout)
            logger.debug("AI score received: %s", score)
            return score, metadata, "ai"
        except Exception as exc:
            logger.warning("AI provider failed for %s, triggering fallback: %s", proposal.id, exc)
            score, metadata = self._fallback.compute(proposal)
            return score, metadata, "fallback"

    def get_proposal(self, proposal_id: UUID) -> Optional[Proposal]:
        """Retrieve a single proposal by ID."""
        return self._repo.get_by_id(proposal_id)

    def list_proposals(self) -> List[Proposal]:
        """List all proposals."""
        return self._repo.list_all()

    def update_proposal_status(
        self,
        proposal_id: UUID,
        status: ProposalStatus,
        note: Optional[str] = None,
        score: Optional[Decimal] = None
    ) -> Proposal:
        """Manually update a proposal status."""
        return self._repo.update_status(proposal_id, status, decision_note=note, score=score)

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
