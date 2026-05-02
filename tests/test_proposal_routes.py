from decimal import Decimal
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.proposal_routes import get_proposal_service, get_repository
from app.models.proposal import ProposalStatus
from app.repositories.proposal_repository import InMemoryProposalRepository
from app.services.proposal_service import ProposalService
from app.adapters.stubs import SimpleAIStub, SimpleFallbackStub


@pytest.fixture
def client():
    """
    Fixture setting up the FastAPI TestClient with dependency overrides.
    Ensures total test isolation by resetting the repository and service state.
    """
    # Initialize clean infrastructure for each test
    repo = InMemoryProposalRepository()
    service = ProposalService(
        repository=repo,
        ai_provider=SimpleAIStub(),
        fallback=SimpleFallbackStub()
    )

    # Apply overrides to the FastAPI app instance
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_proposal_service] = lambda: service

    with TestClient(app) as c:
        yield c

    # Clean up overrides after test execution
    app.dependency_overrides.clear()


def test_should_create_proposal_successfully(client: TestClient) -> None:
    payload = {
        "cpf": "52998224725",  # Valid CPF according to domain logic
        "full_name": "Integration Test User",
        "monthly_income": 5000.0,
        "amount_requested": 1500.0
    }
    
    response = client.post("/proposals/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["cpf"] == "52998224725"
    # SimpleAIStub returns 0.75, which is >= 0.7 threshold (Approved)
    assert data["status"] == ProposalStatus.aprovado.value
    assert "id" in data


def test_should_return_404_for_non_existent_proposal(client: TestClient) -> None:
    response = client.get(f"/proposals/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Proposal not found"


def test_should_retrieve_existing_proposal(client: TestClient) -> None:
    # Arrange: Create a proposal via API
    payload = {"cpf": "52998224725", "full_name": "Get Test", "monthly_income": 3000, "amount_requested": 1000}
    created = client.post("/proposals/", json=payload).json()
    proposal_id = created["id"]

    # Act
    response = client.get(f"/proposals/{proposal_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == proposal_id


def test_should_list_multiple_proposals(client: TestClient) -> None:
    # Arrange
    payload = {"cpf": "52998224725", "full_name": "List Test", "monthly_income": 3000, "amount_requested": 1000}
    client.post("/proposals/", json=payload)
    client.post("/proposals/", json=payload)

    # Act
    response = client.get("/proposals/")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_should_delete_proposal_successfully(client: TestClient) -> None:
    # Arrange
    payload = {"cpf": "52998224725", "full_name": "Delete Test", "monthly_income": 3000, "amount_requested": 1000}
    created = client.post("/proposals/", json=payload).json()
    proposal_id = created["id"]

    # Act: Delete
    del_response = client.delete(f"/proposals/{proposal_id}")
    assert del_response.status_code == 204

    # Assert: Verify retrieval fails
    get_response = client.get(f"/proposals/{proposal_id}")
    assert get_response.status_code == 404


def test_should_return_404_when_deleting_non_existent_proposal(client: TestClient) -> None:
    response = client.delete(f"/proposals/{uuid4()}")
    assert response.status_code == 404