#!/usr/bin/env python3
"""
Modèle Email - VERSION COMPLÈTE CORRIGÉE
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class Email:
    """
    Modèle représentant un email.
    
    Attributes:
        id: Identifiant unique de l'email
        sender: Adresse de l'expéditeur
        to: Adresse du destinataire
        subject: Sujet de l'email
        snippet: Aperçu court du contenu
        body: Contenu complet de l'email
        received_date: Date de réception
        read: Statut lu/non lu
        thread_id: Identifiant du thread de conversation
        attachments: Liste des pièces jointes
        labels: Labels Gmail associés
        ai_analysis: Résultat de l'analyse IA
    """
    
    id: str
    sender: str
    to: str
    subject: str
    snippet: str = ""
    body: str = ""
    received_date: Optional[datetime] = None
    read: bool = False
    thread_id: Optional[str] = None
    attachments: List[Dict] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    ai_analysis: Optional[Dict] = None
    
    def __str__(self) -> str:
        """Représentation textuelle de l'email."""
        return f"Email(from={self.sender}, subject={self.subject})"
    
    def __repr__(self) -> str:
        """Représentation détaillée de l'email."""
        return (
            f"Email(id={self.id}, sender={self.sender}, "
            f"subject={self.subject}, read={self.read})"
        )
    
    @property
    def is_unread(self) -> bool:
        """Vérifie si l'email est non lu."""
        return not self.read
    
    @property
    def has_attachments(self) -> bool:
        """Vérifie si l'email a des pièces jointes."""
        return len(self.attachments) > 0
    
    @property
    def attachment_count(self) -> int:
        """Retourne le nombre de pièces jointes."""
        return len(self.attachments)