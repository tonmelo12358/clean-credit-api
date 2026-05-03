from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator

from app.models.proposal import Proposal, ProposalStatus, is_valid_cpf, clean_cpf
from app.repositories.proposal_repository import InMemoryProposalRepository, ProposalRepository
from app.adapters.stubs import SimpleFallbackStub
from app.adapters.gemini_adapter import GeminiProvider # Importa o GeminiProvider
from app.services.proposal_service import ProposalService


router = APIRouter(prefix="/proposals", tags=["proposals"])


# Simple DTO for creation payload
class ProposalCreate(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=14, description="CPF do solicitante")
    full_name: str = Field(..., min_length=3, description="Nome completo do solicitante")
    monthly_income: Decimal = Field(..., gt=0, description="Renda mensal")
    amount_requested: Decimal = Field(..., gt=0, description="Valor solicitado")

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not is_valid_cpf(v):
            raise ValueError("CPF inválido")
        return clean_cpf(v)


class ProposalStatusUpdate(BaseModel):
    status: ProposalStatus
    note: Optional[str] = Field(None, max_length=1024, description="Nota descritiva da decisão manual")
    score: Optional[Decimal] = Field(None, ge=0, le=1, description="Score revisado manualmente")


# Module-level singletons used as default dependencies. In a production app
# you should provide concrete implementations via dependency overrides in
# `app/main.py` (or a DI container).
_REPO: ProposalRepository = InMemoryProposalRepository()
# Instanciamos o serviço com o GeminiProvider
_SERVICE = ProposalService(_REPO, GeminiProvider(), SimpleFallbackStub())


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


@router.patch("/{proposal_id}/status", response_model=Proposal)
def update_proposal_status(
    proposal_id: UUID,
    payload: ProposalStatusUpdate,
    service: ProposalService = Depends(get_proposal_service)
) -> Proposal:
    """Atualizar manualmente o status de uma proposta (ex: revisão humana)."""
    try:
        return service.update_proposal_status(
            proposal_id=proposal_id,
            status=payload.status,
            note=payload.note,
            score=payload.score
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal(proposal_id: UUID, repo: ProposalRepository = Depends(get_repository)) -> Response:
    success = repo.delete(proposal_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
