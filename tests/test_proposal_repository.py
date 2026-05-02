from decimal import Decimal
from uuid import uuid4
import pytest

from app.models.proposal import Proposal, ProposalStatus
from app.repositories.proposal_repository import InMemoryProposalRepository
from tests.conftest import VALID_CPF


def make_proposal(**overrides) -> Proposal:
    data = {
        "cpf": VALID_CPF,
        "full_name": "Test User",
        "monthly_income": Decimal("1000.00"),
        "amount_requested": Decimal("500.00"),
    }
    data.update(overrides)
    return Proposal(**data)


def test_save_and_get_by_id() -> None:
    repo = InMemoryProposalRepository()
    p = make_proposal()
    saved = repo.save(p)
    fetched = repo.get_by_id(saved.id)
    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.cpf == VALID_CPF


def test_list_all() -> None:
    repo = InMemoryProposalRepository()
    repo.save(make_proposal())
    repo.save(make_proposal(full_name="Other"))
    items = repo.list_all()
    assert len(items) == 2


def test_update_status() -> None:
    repo = InMemoryProposalRepository()
    p = repo.save(make_proposal())
    updated = repo.update_status(p.id, ProposalStatus.aprovado, decision_note="OK", score=Decimal("0.85"))
    assert updated.status == ProposalStatus.aprovado
    assert updated.decision_note == "OK"
    assert updated.score == Decimal("0.85")
    assert updated.updated_at is not None


def test_update_nonexistent_raises() -> None:
    repo = InMemoryProposalRepository()
    with pytest.raises(ValueError):
        repo.update_status(uuid4(), ProposalStatus.negado)

def test_delete_proposal() -> None:
    repo = InMemoryProposalRepository()
    p = repo.save(make_proposal())
    assert repo.delete(p.id) is True
    assert repo.get_by_id(p.id) is None
    # Delete non-existent
    assert repo.delete(uuid4()) is False
