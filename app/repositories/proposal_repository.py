from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from typing import Dict, List, Optional
from uuid import UUID

from app.models.proposal import Proposal, ProposalStatus


class ProposalRepository:
    """Interface leve do repositório de Proposals.

    Implementações concretas devem respeitar estas assinaturas para permitir
    troca por implementações persistentes (SQLModel/SQLite/Postgres).
    """

    def save(self, proposal: Proposal) -> Proposal:
        """Persist a proposal instance.

        Args:
            proposal: Proposal instance to persist.

        Returns:
            The persisted Proposal (may be the same instance or a new one depending on implementation).
        """
        raise NotImplementedError

    def get_by_id(self, id: UUID) -> Optional[Proposal]:
        """Retrieve a proposal by its UUID.

        Args:
            id: UUID of the proposal to fetch.

        Returns:
            The Proposal if found, otherwise `None`.
        """
        raise NotImplementedError

    def list_all(self) -> List[Proposal]:
        """Return a list with all proposals stored.

        Returns:
            A list of `Proposal` instances (possibly empty).
        """
        raise NotImplementedError

    def delete(self, id: UUID) -> bool:
        """Remove a proposal from storage.

        Returns:
            True if removed, False if not found.
        """
        raise NotImplementedError

    def update_status(
        self,
        id: UUID,
        status: ProposalStatus,
        decision_note: Optional[str] = None,
        score: Optional[Decimal] = None,
    ) -> Proposal:
        """Update the status (and optional metadata) of an existing proposal.

        Args:
            id: UUID of the proposal to update.
            status: New `ProposalStatus` value.
            decision_note: Optional textual note explaining the decision.
            score: Optional new score value to persist.

        Returns:
            The updated `Proposal` instance.

        Raises:
            ValueError: if the proposal does not exist.
        """
        raise NotImplementedError


class InMemoryProposalRepository(ProposalRepository):
    """Repositório em memória para desenvolvimento e testes locais.

    Usa um dicionário interno protegido por lock para concorrência simples.
    """

    def __init__(self) -> None:
        self._store: Dict[UUID, Proposal] = {}
        self._lock = Lock()

    def save(self, proposal: Proposal) -> Proposal:
        """Save a proposal in the in-memory store."""
        with self._lock:
            stored_proposal = deepcopy(proposal)
            self._store[stored_proposal.id] = stored_proposal
            return deepcopy(stored_proposal)

    def get_by_id(self, id: UUID) -> Optional[Proposal]:
        """Fetch a proposal by id from the in-memory store.

        Returns a deep copy of the stored object to preserve repository encapsulation.
        """
        with self._lock:
            item = self._store.get(id)
            return deepcopy(item) if item else None

    def list_all(self) -> List[Proposal]:
        """List all proposals currently stored in memory.

        The returned list contains deep copies of stored proposals.
        """
        with self._lock:
            return [deepcopy(p) for p in self._store.values()]

    def delete(self, id: UUID) -> bool:
        """Remove the proposal from memory."""
        with self._lock:
            if id in self._store:
                self._store.pop(id)
                return True
            return False

    def update_status(
        self,
        id: UUID,
        status: ProposalStatus,
        decision_note: Optional[str] = None,
        score: Optional[Decimal] = None,
    ) -> Proposal:
        """Update status and metadata for a proposal."""
        with self._lock:
            existing = self._store.get(id)
            if existing is None:
                raise ValueError("Proposal not found")

            existing.status = status
            if decision_note is not None:
                existing.decision_note = decision_note
            if score is not None:
                existing.score = score
            
            existing.updated_at = datetime.now(timezone.utc)
            return deepcopy(existing)
