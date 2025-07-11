"""
Modèle de données pour les réponses automatiques en attente de validation.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum

class ResponseStatus(Enum):
    """Statuts possibles pour une réponse en attente."""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    SENT = "sent"

@dataclass
class PendingResponse:
    """Classe représentant une réponse automatique en attente de validation."""
    
    id: Optional[int] = None
    email_id: str = ""
    original_subject: str = ""
    original_sender: str = ""
    original_sender_email: str = ""
    original_body: str = ""
    category: str = "general"
    proposed_response: str = ""
    reason: str = ""  # Pourquoi l'IA propose cette réponse
    confidence_score: float = 0.0
    status: ResponseStatus = ResponseStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_notes: str = ""  # Notes de l'utilisateur
    
    @property
    def is_pending(self) -> bool:
        """Vérifie si la réponse est en attente."""
        return self.status == ResponseStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        """Vérifie si la réponse est approuvée."""
        return self.status == ResponseStatus.APPROVED
    
    @property
    def is_rejected(self) -> bool:
        """Vérifie si la réponse est rejetée."""
        return self.status == ResponseStatus.REJECTED
    
    @property
    def is_sent(self) -> bool:
        """Vérifie si la réponse a été envoyée."""
        return self.status == ResponseStatus.SENT
    
    def to_dict(self) -> dict:
        """Convertit la réponse en dictionnaire."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'original_subject': self.original_subject,
            'original_sender': self.original_sender,
            'original_sender_email': self.original_sender_email,
            'original_body': self.original_body,
            'category': self.category,
            'proposed_response': self.proposed_response,
            'reason': self.reason,
            'confidence_score': self.confidence_score,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_notes': self.user_notes
        }
    
    def __str__(self) -> str:
        """Représentation string de la réponse."""
        return f"PendingResponse(email_id={self.email_id}, category={self.category}, status={self.status.value})"