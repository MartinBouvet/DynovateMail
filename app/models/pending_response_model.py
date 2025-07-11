"""
Modèle de données pour les réponses automatiques en attente de validation - VERSION CORRIGÉE.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum

class ResponseStatus(Enum):
    """Statuts possibles pour une réponse en attente."""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    SENT = "sent"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def from_string(cls, status_str: str):
        """Crée un ResponseStatus à partir d'une chaîne."""
        try:
            return cls(status_str.lower())
        except ValueError:
            return cls.PENDING

@dataclass
class PendingResponse:
    """Classe représentant une réponse automatique en attente de validation."""
    
    # Champs obligatoires
    email_id: str = ""
    original_subject: str = ""
    original_sender: str = ""
    original_sender_email: str = ""
    original_body: str = ""
    category: str = "general"
    proposed_response: str = ""
    
    # Champs optionnels avec valeurs par défaut
    id: Optional[int] = None
    reason: str = ""  # Pourquoi l'IA propose cette réponse
    confidence_score: float = 0.0
    status: ResponseStatus = ResponseStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_notes: str = ""  # Notes de l'utilisateur
    
    def __post_init__(self):
        """Initialisation après création de l'instance."""
        # Assurer que les dates sont définies
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        
        # Assurer que le statut est un ResponseStatus
        if isinstance(self.status, str):
            self.status = ResponseStatus.from_string(self.status)
        
        # Validation des champs requis
        if not self.email_id:
            raise ValueError("email_id est requis")
        if not self.original_sender_email:
            raise ValueError("original_sender_email est requis")
        if not self.proposed_response.strip():
            raise ValueError("proposed_response ne peut pas être vide")
    
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
    
    @property
    def age_in_minutes(self) -> int:
        """Retourne l'âge de la réponse en minutes."""
        if self.created_at:
            return int((datetime.now() - self.created_at).total_seconds() / 60)
        return 0
    
    @property
    def age_display(self) -> str:
        """Retourne l'âge formaté pour l'affichage."""
        age_minutes = self.age_in_minutes
        
        if age_minutes < 1:
            return "À l'instant"
        elif age_minutes < 60:
            return f"Il y a {age_minutes} min"
        elif age_minutes < 1440:  # 24 heures
            hours = age_minutes // 60
            return f"Il y a {hours}h"
        else:
            days = age_minutes // 1440
            return f"Il y a {days}j"
    
    @property
    def confidence_display(self) -> str:
        """Retourne le score de confiance formaté."""
        return f"{self.confidence_score:.1%}"
    
    @property
    def status_display(self) -> str:
        """Retourne le statut formaté pour l'affichage."""
        status_mapping = {
            ResponseStatus.PENDING: "En attente",
            ResponseStatus.APPROVED: "Approuvée", 
            ResponseStatus.REJECTED: "Rejetée",
            ResponseStatus.SENT: "Envoyée"
        }
        return status_mapping.get(self.status, "Inconnu")
    
    @property
    def status_icon(self) -> str:
        """Retourne l'icône correspondant au statut."""
        status_icons = {
            ResponseStatus.PENDING: "⏳",
            ResponseStatus.APPROVED: "✅",
            ResponseStatus.REJECTED: "❌", 
            ResponseStatus.SENT: "📤"
        }
        return status_icons.get(self.status, "❓")
    
    @property
    def category_display(self) -> str:
        """Retourne la catégorie formatée pour l'affichage."""
        category_mapping = {
            'cv': 'Candidature',
            'rdv': 'Rendez-vous',
            'spam': 'Spam',
            'facture': 'Facture',
            'support': 'Support',
            'partenariat': 'Partenariat',
            'newsletter': 'Newsletter',
            'important': 'Important',
            'general': 'Général'
        }
        return category_mapping.get(self.category.lower(), self.category.title())
    
    @property
    def category_icon(self) -> str:
        """Retourne l'icône correspondant à la catégorie."""
        category_icons = {
            'cv': '📄',
            'rdv': '🤝',
            'spam': '🛡️',
            'facture': '🧾',
            'support': '🔧',
            'partenariat': '🤝',
            'newsletter': '📰',
            'important': '⭐',
            'general': '📧'
        }
        return category_icons.get(self.category.lower(), '📧')
    
    def update_status(self, new_status: ResponseStatus, notes: str = ""):
        """
        Met à jour le statut de la réponse.
        
        Args:
            new_status: Nouveau statut.
            notes: Notes optionnelles.
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        if notes:
            if self.user_notes:
                self.user_notes += f"\n{notes}"
            else:
                self.user_notes = notes
        
        # Log du changement
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Statut de la réponse {self.id} changé: {old_status.value} -> {new_status.value}")
    
    def add_user_note(self, note: str):
        """
        Ajoute une note utilisateur.
        
        Args:
            note: Note à ajouter.
        """
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        formatted_note = f"[{timestamp}] {note}"
        
        if self.user_notes:
            self.user_notes += f"\n{formatted_note}"
        else:
            self.user_notes = formatted_note
        
        self.updated_at = datetime.now()
    
    def get_short_subject(self, max_length: int = 50) -> str:
        """
        Retourne le sujet tronqué si nécessaire.
        
        Args:
            max_length: Longueur maximale.
            
        Returns:
            Sujet tronqué.
        """
        if len(self.original_subject) <= max_length:
            return self.original_subject
        return self.original_subject[:max_length-3] + "..."
    
    def get_short_response(self, max_length: int = 100) -> str:
        """
        Retourne la réponse tronquée si nécessaire.
        
        Args:
            max_length: Longueur maximale.
            
        Returns:
            Réponse tronquée.
        """
        if len(self.proposed_response) <= max_length:
            return self.proposed_response
        return self.proposed_response[:max_length-3] + "..."
    
    def get_sender_display_name(self) -> str:
        """
        Retourne le nom d'affichage de l'expéditeur.
        
        Returns:
            Nom d'affichage de l'expéditeur.
        """
        if self.original_sender and self.original_sender.strip():
            return self.original_sender
        return self.original_sender_email
    
    def validate(self) -> list:
        """
        Valide les données de la réponse.
        
        Returns:
            Liste des erreurs de validation.
        """
        errors = []
        
        if not self.email_id or not self.email_id.strip():
            errors.append("ID de l'email requis")
        
        if not self.original_sender_email or not self.original_sender_email.strip():
            errors.append("Email de l'expéditeur requis")
        elif '@' not in self.original_sender_email:
            errors.append("Email de l'expéditeur invalide")
        
        if not self.proposed_response or not self.proposed_response.strip():
            errors.append("Réponse proposée requise")
        
        if self.confidence_score < 0 or self.confidence_score > 1:
            errors.append("Score de confiance doit être entre 0 et 1")
        
        if not isinstance(self.status, ResponseStatus):
            errors.append("Statut invalide")
        
        return errors
    
    def is_valid(self) -> bool:
        """
        Vérifie si la réponse est valide.
        
        Returns:
            True si valide, False sinon.
        """
        return len(self.validate()) == 0
    
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
            'user_notes': self.user_notes,
            # Propriétés calculées
            'status_display': self.status_display,
            'status_icon': self.status_icon,
            'category_display': self.category_display,
            'category_icon': self.category_icon,
            'age_display': self.age_display,
            'confidence_display': self.confidence_display
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PendingResponse':
        """
        Crée une PendingResponse à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire de données.
            
        Returns:
            Instance de PendingResponse.
        """
        # Convertir les dates si elles sont des chaînes
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        # Convertir le statut
        status = data.get('status', ResponseStatus.PENDING)
        if isinstance(status, str):
            status = ResponseStatus.from_string(status)
        
        return cls(
            id=data.get('id'),
            email_id=data.get('email_id', ''),
            original_subject=data.get('original_subject', ''),
            original_sender=data.get('original_sender', ''),
            original_sender_email=data.get('original_sender_email', ''),
            original_body=data.get('original_body', ''),
            category=data.get('category', 'general'),
            proposed_response=data.get('proposed_response', ''),
            reason=data.get('reason', ''),
            confidence_score=float(data.get('confidence_score', 0.0)),
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            user_notes=data.get('user_notes', '')
        )
    
    def __str__(self) -> str:
        """Représentation string de la réponse."""
        return f"PendingResponse(id={self.id}, email_id={self.email_id}, category={self.category}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """Représentation détaillée de la réponse."""
        return (f"PendingResponse("
                f"id={self.id}, "
                f"email_id='{self.email_id}', "
                f"sender='{self.original_sender_email}', "
                f"category='{self.category}', "
                f"status={self.status.value}, "
                f"confidence={self.confidence_score:.2f})")
    
    def __eq__(self, other) -> bool:
        """Comparaison d'égalité."""
        if not isinstance(other, PendingResponse):
            return False
        return self.id == other.id if self.id and other.id else False
    
    def __hash__(self) -> int:
        """Hash pour utilisation dans des sets/dicts."""
        return hash(self.id) if self.id else hash((self.email_id, self.original_sender_email))