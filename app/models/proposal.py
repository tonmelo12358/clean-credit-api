from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Annotated
from uuid import UUID, uuid4
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator


def _clean_cpf(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _is_valid_cpf(raw: str) -> bool:
    s = _clean_cpf(raw)
    if len(s) != 11:
        return False
    if s == s[0] * 11:
        return False

    def _calc_digit(digs: str) -> str:
        weights = list(range(len(digs) + 1, 1, -1))
        total = sum(int(d) * w for d, w in zip(digs, weights))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    d1 = _calc_digit(s[:9])
    d2 = _calc_digit(s[:9] + d1)
    return s[-2:] == f"{d1}{d2}"


class ProposalStatus(str, Enum):
    pendente = "pendente"
    aprovado = "aprovado"
    negado = "negado"


class ProposalCreate(BaseModel):
    """Dados para criação de proposta de crédito."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)

    cpf: Annotated[str, Field(..., description="CPF do solicitante (formatado ou somente dígitos)")]
    full_name: Annotated[str, Field(..., min_length=3, description="Nome completo do solicitante")]
    monthly_income: Annotated[Decimal, Field(..., gt=0, description="Renda mensal (decimal, > 0)")]
    amount_requested: Annotated[Decimal, Field(..., gt=0, description="Valor solicitado (decimal, > 0)")]

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not _is_valid_cpf(v):
            raise ValueError("CPF inválido")
        return _clean_cpf(v)


class ProposalUpdate(BaseModel):
    """Atualizações parciais permitidas na proposta."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)

    status: Optional[ProposalStatus] = Field(None, description="Novo status da proposta")
    decision_note: Optional[Annotated[str, Field(max_length=1024, description="Observação/nota da decisão")]] = None


class ProposalOut(BaseModel):
    """Representação pública da proposta retornada pela API."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4, description="Identificador único (UUID)")
    cpf: Annotated[str, Field(..., description="CPF somente dígitos (para auditoria)")]
    full_name: str
    monthly_income: Decimal
    amount_requested: Decimal
    status: ProposalStatus = Field(..., description="Status atual da proposta")
    score: Annotated[Decimal, Field(..., ge=0, le=1, description="Score normalizado entre 0 e 1")]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    decision_note: Optional[str] = None

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, v: str) -> str:
        return _clean_cpf(v)
