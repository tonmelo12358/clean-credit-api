import os
import logging
import json
import httpx
from decimal import Decimal
from typing import Tuple
from app.models.proposal import Proposal
from app.services.proposal_service import AIProvider

logger = logging.getLogger(__name__)

class GeminiProvider(AIProvider):
    """
    Adaptador para integração com a API do Google Gemini via REST.
    Utiliza o modelo gemini-1.5-flash para baixa latência.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Sincroniza com as variáveis do .env.example ou usa defaults seguros
        self.model = model or os.getenv("AI_MODEL_NAME", "gemini-1.5-flash")
        
        # Alterado de v1beta para v1 (versão estável) para evitar 404 em modelos GA
        base_url = os.getenv("AI_PROVIDER_URL", "https://generativelanguage.googleapis.com/v1beta")
        
        self._url = f"{base_url}/models/{self.model}:generateContent"

    def request_score(self, proposal: Proposal, timeout: float = 2.0) -> Tuple[Decimal, dict]:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY não configurada no ambiente.")

        prompt = self._build_prompt(proposal)
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
            }
        }

        try:
            logger.info(f"Conectando à API do Gemini ({self.model})...")
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
                logger.info(f"Sucesso: Gemini retornou score {score}")
                return score, metadata
        except Exception as e:
            raise RuntimeError(f"Erro na chamada ao Gemini: {str(e)}") from e

    def _build_prompt(self, proposal: Proposal) -> str:
        return f"""
        Analise o risco de crédito para:
        Nome: {proposal.full_name}, Renda: {proposal.monthly_income}, Valor: {proposal.amount_requested}
        Retorne um JSON com: "score" (0.0 a 1.0) e "reason" (string).
        """
