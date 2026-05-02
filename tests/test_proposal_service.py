from decimal import Decimal
from uuid import uuid4
import os
import sys

import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.proposal import Proposal, ProposalStatus
from app.repositories.proposal_repository import InMemoryProposalRepository
from app.services.proposal_service import ProposalService


VALID_CPF = "52998224725"


def make_proposal(**overrides) -> Proposal:
    data = {
        "cpf": VALID_CPF,
        "full_name": "Service Test",
        "monthly_income": Decimal("2000.00"),
        "amount_requested": Decimal("1000.00"),
    }
    data.update(overrides)
    return Proposal(**data)


class FakeAI:
    def __init__(self, score: Decimal = Decimal("0.8"), metadata: dict | None = None, raise_exc: bool = False):
        self.score = Decimal(score)
        self.metadata = metadata or {"model": "fake"}
        self.raise_exc = raise_exc

    def request_score(self, proposal: Proposal, timeout: float = 2.0):
        if self.raise_exc:
            raise RuntimeError("AI provider error")
        return self.score, self.metadata


class FakeFallback:
    def __init__(self, score: Decimal = Decimal("0.3"), metadata: dict | None = None):
        self.score = Decimal(score)
        self.metadata = metadata or {"rules": "simple"}

    def compute(self, proposal: Proposal):
        return self.score, self.metadata


def test_process_with_ai_success() -> None:
    repo = InMemoryProposalRepository()
    ai = FakeAI(score=Decimal("0.85"))
    fb = FakeFallback()
    svc = ProposalService(repo, ai, fb)

    p = make_proposal()
    updated = svc.process(p)

    assert updated.score == Decimal("0.85")
    assert updated.status == ProposalStatus.aprovado
    assert "source=ai" in (updated.decision_note or "")


def test_process_fallback_on_ai_failure() -> None:
    repo = InMemoryProposalRepository()
    ai = FakeAI(raise_exc=True)
    fb = FakeFallback(score=Decimal("0.35"))
    svc = ProposalService(repo, ai, fb)

    p = make_proposal()
    updated = svc.process(p)

    assert updated.score == Decimal("0.35")
    assert updated.status == ProposalStatus.negado
    assert "source=fallback" in (updated.decision_note or "")


def test_process_produces_pending_when_between_thresholds() -> None:
    repo = InMemoryProposalRepository()
    ai = FakeAI(score=Decimal("0.5"))
    fb = FakeFallback()
    svc = ProposalService(repo, ai, fb, approve_threshold=Decimal("0.7"), reject_threshold=Decimal("0.4"))

    p = make_proposal()
    updated = svc.process(p)

    assert updated.score == Decimal("0.5")
    assert updated.status == ProposalStatus.pendente
    assert "source=ai" in (updated.decision_note or "")
