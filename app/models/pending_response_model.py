#!/usr/bin/env python3
"""
Modèle pour les réponses en attente de validation.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class ResponseStatus(Enum):
    """Statut des réponses en attente."""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    SENT = "sent"
    EXPIRED = "expired"

@dataclass
class PendingResponse:
    """Modèle d'une réponse en attente."""
    id: str
    email_id: str
    suggested_response: str
    confidence: float
    status: ResponseStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    user_notes: str = ""
    modified_response: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Vérifie si la réponse a expiré."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def get_final_response(self) -> str:
        """Retourne la réponse finale à envoyer."""
        return self.modified_response or self.suggested_response