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
        """Save a proposal in the in-memory store.

        Stores a deep copy to avoid external mutation of repository state.
        """
        with self._lock:
            # Armazenar uma cópia para evitar efeitos colaterais fora do repositório
            self._store[proposal.id] = deepcopy(proposal)
            return deepcopy(self._store[proposal.id])

    def get_by_id(self, id: UUID) -> Optional[Proposal]:
        """Fetch a proposal by id from the in-memory store.

        Returns a deep copy of the stored object to preserve repository encapsulation.
        """
        with self._lock:
            item = self._store.get(id)
            return deepcopy(item) if item is not None else None

    def list_all(self) -> List[Proposal]:
        """List all proposals currently stored in memory.

        The returned list contains deep copies of stored proposals.
        """
        with self._lock:
            return [deepcopy(p) for p in self._store.values()]

    def update_status(
        self,
        id: UUID,
        status: ProposalStatus,
        decision_note: Optional[str] = None,
        score: Optional[Decimal] = None,
    ) -> Proposal:
        """Update status, optional decision note and score for a proposal.

        Performs an in-place update of the stored entity and returns a deep copy
        of the updated object.

        Raises ValueError if the proposal does not exist.
        """
        with self._lock:
            existing = self._store.get(id)
            if existing is None:
                raise ValueError("Proposal not found")

            # Atualizar campos permitidos
            existing.status = status
            if decision_note is not None:
                existing.decision_note = decision_note
            if score is not None:
                existing.score = score
            existing.updated_at = datetime.now(timezone.utc)

            # Persistir e retornar cópia
            self._store[id] = deepcopy(existing)
            return deepcopy(existing)
