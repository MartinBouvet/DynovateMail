#!/usr/bin/env python3
"""
Modèle de données pour représenter un email.
"""
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime

@dataclass
class Email:
    """Classe représentant un email."""
    
    id: str
    subject: Optional[str] = ""
    sender: str = ""
    recipient: str = ""
    received_date: Optional[datetime] = None
    body: str = ""
    labels: List[str] = field(default_factory=list)
    thread_id: str = ""
    snippet: str = ""
    is_read: bool = False
    is_sent: bool = False
    attachments: List[dict] = field(default_factory=list)
    
    @property
    def is_unread(self) -> bool:
        """Vérifie si l'email est non lu."""
        return not self.is_read
    
    @property
    def is_important(self) -> bool:
        """Vérifie si l'email est marqué comme important."""
        return 'IMPORTANT' in self.labels
    
    @property
    def date(self) -> Optional[datetime]:
        """Alias pour received_date pour compatibilité."""
        return self.received_date
    
    @property
    def datetime(self) -> datetime:
        """Convertit la date de l'email en objet datetime."""
        try:
            if isinstance(self.received_date, datetime):
                return self.received_date
            elif isinstance(self.received_date, str):
                return parsedate_to_datetime(self.received_date)
            else:
                return datetime.now()
        except (TypeError, ValueError):
            return datetime.now()
    
    def get_sender_name(self) -> str:
        """Extrait le nom de l'expéditeur de l'adresse email."""
        if '<' in self.sender:
            parts = self.sender.split('<')
            return parts[0].strip(' "\'')
        return self.sender
    
    def get_sender_email(self) -> str:
        """Extrait l'adresse email de l'expéditeur."""
        if '<' in self.sender and '>' in self.sender:
            start = self.sender.find('<') + 1
            end = self.sender.find('>')
            return self.sender[start:end]
        return self.sender
    
    def to_dict(self) -> dict:
        """Convertit l'email en dictionnaire."""
        return {
            'id': self.id,
            'subject': self.subject,
            'sender': self.sender,
            'recipient': self.recipient,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'body': self.body,
            'labels': self.labels,
            'thread_id': self.thread_id,
            'snippet': self.snippet,
            'is_unread': self.is_unread,
            'is_important': self.is_important,
            'is_sent': self.is_sent,
            'is_read': self.is_read,
            'attachments': self.attachments
        }