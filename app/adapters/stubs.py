from decimal import Decimal
from typing import Tuple
from app.models.proposal import Proposal

class SimpleAIStub:
    """Implementação temporária para testes de integração."""
    def request_score(self, proposal: Proposal, timeout: float = 2.0) -> Tuple[Decimal, dict]:
        # Heurística simples para o MVP
        score = Decimal("0.75")
        return score, {"source": "stub-ai", "model": "mock-v1"}

class SimpleFallbackStub:
    """Regras de negócio locais simplificadas."""
    def compute(self, proposal: Proposal) -> Tuple[Decimal, dict]:
        # Regra básica: se renda > valor pedido, score favorável
        if proposal.monthly_income > proposal.amount_requested:
            return Decimal("0.60"), {"source": "stub-fallback", "rule": "income_gt_amount"}
        return Decimal("0.30"), {"source": "stub-fallback", "rule": "low_income"}
