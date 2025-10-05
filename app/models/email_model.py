#!/usr/bin/env python3
"""
Modèles de données pour les emails - CORRIGÉ
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any
from datetime import datetime


@dataclass
class EmailAttachment:
    """Représente une pièce jointe."""
    id: str
    filename: str
    mime_type: str
    size: int
    message_id: str
    data: Optional[bytes] = None


@dataclass
class Email:
    """Représente un email - CORRIGÉ."""
    id: str
    sender: str
    subject: str
    body: str
    snippet: str
    received_date: datetime
    is_read: bool = False
    is_html: bool = False
    to: str = ""  # AJOUTÉ
    cc: Optional[List[str]] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    has_attachments: bool = False
    labels: List[str] = field(default_factory=list)
    ai_analysis: Optional[Any] = None
    
    def get_sender_name(self) -> str:
        """Extrait le nom de l'expéditeur."""
        if '<' in self.sender:
            return self.sender.split('<')[0].strip().strip('"')
        return self.sender.split('@')[0]
    
    def get_sender_email(self) -> str:
        """Extrait l'email de l'expéditeur."""
        if '<' in self.sender:
            return self.sender.split('<')[1].split('>')[0]
        return self.sender