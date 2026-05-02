from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.models.proposal import Proposal
from app.repositories.proposal_repository import InMemoryProposalRepository, ProposalRepository
from app.services.proposal_service import ProposalService


router = APIRouter(prefix="/proposals", tags=["proposals"])


# Simple DTO for creation payload
class ProposalCreate(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=14, description="CPF do solicitante")
    full_name: str = Field(..., min_length=3, description="Nome completo do solicitante")
    monthly_income: Decimal = Field(..., gt=0, description="Renda mensal")
    amount_requested: Decimal = Field(..., gt=0, description="Valor solicitado")


# Module-level singletons used as default dependencies. In a production app
# you should provide concrete implementations via dependency overrides in
# `app/main.py` (or a DI container).
_REPO: ProposalRepository = InMemoryProposalRepository()


class _SimpleAI:
    def request_score(self, proposal: Proposal, timeout: float = 2.0):
        # Deterministic stub: simple heuristic to allow the service to run.
        from decimal import Decimal

        score = Decimal("0.75")
        return score, {"source": "stub-ai"}


class _SimpleFallback:
    def compute(self, proposal: Proposal):
        from decimal import Decimal

        score = Decimal("0.45")
        return score, {"source": "stub-fallback"}


_SERVICE = ProposalService(_REPO, _SimpleAI(), _SimpleFallback())


def get_proposal_service() -> ProposalService:
    return _SERVICE


def get_repository() -> ProposalRepository:
    return _REPO


@router.post("/", response_model=Proposal, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: ProposalCreate, service: ProposalService = Depends(get_proposal_service)
) -> Proposal:
    """Criar e processar uma nova proposta de crédito.

    - Persiste a proposta como `pendente`
    - Solicita score ao provedor de IA (com fallback)
    - Persiste decisão final e retorna o recurso completo
    """
    proposal = Proposal(
        cpf=payload.cpf,
        full_name=payload.full_name,
        monthly_income=payload.monthly_income,
        amount_requested=payload.amount_requested,
    )

    result = service.process(proposal)

    return result


@router.get("/{proposal_id}", response_model=Proposal)
def get_proposal(proposal_id: UUID, repo: ProposalRepository = Depends(get_repository)) -> Proposal:
    item = repo.get_by_id(proposal_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return item


@router.get("/", response_model=List[Proposal])
def list_proposals(repo: ProposalRepository = Depends(get_repository)) -> List[Proposal]:
    return repo.list_all()


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal(proposal_id: UUID, repo: ProposalRepository = Depends(get_repository)) -> Response:
    # The repository interface currently does not expose a delete method.
    # For the in-memory implementation we remove the item directly.
    if hasattr(repo, "_lock") and hasattr(repo, "_store"):
        lock = getattr(repo, "_lock")
        store = getattr(repo, "_store")
        with lock:
            if proposal_id not in store:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
            store.pop(proposal_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # If repository provides an explicit delete method, prefer calling it.
    delete_fn = getattr(repo, "delete", None)
    if callable(delete_fn):
        try:
            delete_fn(proposal_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Delete not supported by repository")
