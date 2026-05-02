from decimal import Decimal
from uuid import uuid4
from typing import Tuple
import pytest
from pytest_mock import MockerFixture

from app.models.proposal import Proposal, ProposalStatus
from app.repositories.proposal_repository import InMemoryProposalRepository
from app.services.proposal_service import ProposalService
from tests.conftest import VALID_CPF

def make_proposal(**overrides) -> Proposal:
    data = {
        "cpf": VALID_CPF,
        "full_name": "Clean Code Architect",
        "monthly_income": Decimal("5000.00"),
        "amount_requested": Decimal("2000.00"),
    }
    data.update(overrides)
    return Proposal(**data)

@pytest.fixture
def repository():
    return InMemoryProposalRepository()

@pytest.fixture
def mock_ai(mocker: MockerFixture):
    return mocker.Mock()

@pytest.fixture
def mock_fallback(mocker: MockerFixture):
    return mocker.Mock()

@pytest.fixture
def service(repository, mock_ai, mock_fallback):
    return ProposalService(
        repository=repository,
        ai_provider=mock_ai,
        fallback=mock_fallback,
        approve_threshold=Decimal("0.7"),
        reject_threshold=Decimal("0.4")
    )

def test_should_successfully_process_proposal_with_high_ai_score(service, mock_ai) -> None:
    # Arrange
    proposal = make_proposal()
    mock_ai.request_score.return_value = (Decimal("0.85"), {"model": "gemini-1.5"})

    # Act
    result = service.process(proposal)

    # Assert
    assert result.status == ProposalStatus.aprovado
    assert result.score == Decimal("0.85")
    assert "source=ai" in result.decision_note
    mock_ai.request_score.assert_called_once()

def test_should_reject_proposal_with_low_ai_score(service, mock_ai) -> None:
    # Arrange
    proposal = make_proposal()
    mock_ai.request_score.return_value = (Decimal("0.20"), {"model": "gemini-1.5"})

    # Act
    result = service.process(proposal)

    # Assert
    assert result.status == ProposalStatus.negado
    assert result.score == Decimal("0.20")

def test_should_trigger_fallback_on_ai_provider_failure(service, mock_ai, mock_fallback) -> None:
    # Arrange
    proposal = make_proposal()
    mock_ai.request_score.side_effect = Exception("Service Unavailable")
    mock_fallback.compute.return_value = (Decimal("0.55"), {"rule": "income_check"})

    # Act
    result = service.process(proposal)

    # Assert
    assert result.status == ProposalStatus.pendente  # 0.55 is between 0.4 and 0.7
    assert result.score == Decimal("0.55")
    assert "source=fallback" in result.decision_note
    mock_fallback.compute.assert_called_once()

def test_should_retrieve_proposal_by_id(service, repository) -> None:
    # Arrange
    p = repository.save(make_proposal())
    
    # Act
    fetched = service.get_proposal(p.id)

    # Assert
    assert fetched is not None
    assert fetched.id == p.id

def test_should_list_all_proposals(service, repository) -> None:
    # Arrange
    repository.save(make_proposal(cpf="52998224725"))
    repository.save(make_proposal(cpf="01413813130"))

    # Act
    all_proposals = service.list_proposals()

    # Assert
    assert len(all_proposals) == 2

def test_should_update_proposal_status(service, repository) -> None:
    # Arrange
    p = repository.save(make_proposal())
    
    # Act
    updated = service.update_proposal_status(
        p.id, 
        ProposalStatus.aprovado, 
        note="Manual Review", 
        score=Decimal("0.99")
    )

    # Assert
    assert updated.status == ProposalStatus.aprovado
    assert updated.score == Decimal("0.99")
    assert updated.decision_note == "Manual Review"

def test_should_raise_error_when_updating_non_existent_proposal(service) -> None:
    # Act & Assert
    with pytest.raises(ValueError, match="Proposal not found"):
        service.update_proposal_status(uuid4(), ProposalStatus.negado)

def test_should_return_none_for_non_existent_id(service) -> None:
    # Act
    result = service.get_proposal(uuid4())

    # Assert
    assert result is None
