from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Annotated
from uuid import UUID, uuid4
import re

from pydantic import field_validator, ConfigDict
from sqlmodel import SQLModel, Field, Column, Numeric


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


class Proposal(SQLModel, table=True):
    """
    Representa a Entidade de Domínio e o Model de Persistência para Propostas de Crédito.
    Focado em resiliência e integridade de dados (Clean Architecture).
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        description="Identificador único da proposta (PK)"
    )
    
    cpf: str = Field(index=True, description="CPF do solicitante (apenas dígitos)")
    full_name: str = Field(min_length=3, description="Nome completo do solicitante")
    
    # Uso de Numeric para garantir precisão decimal no SQLite/Postgres
    monthly_income: Decimal = Field(
        sa_column=Column(Numeric(precision=10, scale=2)),
        description="Renda mensal informada"
    )
    
    amount_requested: Decimal = Field(
        sa_column=Column(Numeric(precision=10, scale=2)),
        description="Valor total do empréstimo solicitado"
    )
    
    status: ProposalStatus = Field(
        default=ProposalStatus.pendente,
        description="Status atual no motor de decisão"
    )
    
    score: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=5, scale=4)),
        description="Score calculado (0.0000 a 1.0000)"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de criação (UTC)"
    )
    
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp da última alteração de status"
    )
    
    decision_note: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Justificativa da decisão (IA ou Fallback)"
    )

    # Validações de Domínio (Pydantic v2)
    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not _is_valid_cpf(v):
            raise ValueError("CPF inválido")
        return _clean_cpf(v)

    @field_validator("monthly_income", "amount_requested")
    @classmethod
    def validate_positive_values(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero")
        return v