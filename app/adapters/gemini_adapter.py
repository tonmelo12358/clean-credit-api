import os
import json
import httpx
from decimal import Decimal
from typing import Tuple
from app.models.proposal import Proposal
from app.services.proposal_service import AIProvider

class GeminiProvider(AIProvider):
    """
    Adaptador para integração com a API do Google Gemini via REST.
    Utiliza o modelo gemini-1.5-flash para baixa latência.
    """

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self._url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def request_score(self, proposal: Proposal, timeout: float = 2.0) -> Tuple[Decimal, dict]:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY não configurada no ambiente.")

        prompt = self._build_prompt(proposal)
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
            }
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    f"{self._url}?key={self.api_key}",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(text_content)
                
                score = Decimal(str(data.get("score", "0.5")))
                metadata = {
                    "model": self.model,
                    "reason": data.get("reason", "No reason provided by AI"),
                    "source": "gemini"
                }
                return score, metadata
        except Exception as e:
            raise RuntimeError(f"Erro na chamada ao Gemini: {str(e)}") from e

    def _build_prompt(self, proposal: Proposal) -> str:
        return f"""
        Analise o risco de crédito para:
        Nome: {proposal.full_name}, Renda: {proposal.monthly_income}, Valor: {proposal.amount_requested}
        Retorne um JSON com: "score" (0.0 a 1.0) e "reason" (string).
        """
