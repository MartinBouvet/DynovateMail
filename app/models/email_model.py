"""
Modèle de données pour représenter un email.
"""
from typing import List
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

@dataclass
class Email:
    """Classe représentant un email."""
    
    id: str
    subject: str
    sender: str
    recipient: str
    date: str
    body: str
    labels: List[str]
    thread_id: str
    snippet: str
    
    @property
    def is_unread(self) -> bool:
        """Vérifie si l'email est non lu."""
        return 'UNREAD' in self.labels
    
    @property
    def is_important(self) -> bool:
        """Vérifie si l'email est marqué comme important."""
        return 'IMPORTANT' in self.labels
    
    @property
    def is_sent(self) -> bool:
        """Vérifie si l'email a été envoyé par l'utilisateur."""
        return 'SENT' in self.labels
    
    @property
    def datetime(self) -> datetime:
        """Convertit la date de l'email en objet datetime."""
        try:
            return parsedate_to_datetime(self.date)
        except (TypeError, ValueError):
            # Retourner la date actuelle en cas d'erreur
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
            'date': self.date,
            'body': self.body,
            'labels': self.labels,
            'thread_id': self.thread_id,
            'snippet': self.snippet,
            'is_unread': self.is_unread,
            'is_important': self.is_important,
            'is_sent': self.is_sent
        }