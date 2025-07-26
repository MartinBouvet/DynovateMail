#!/usr/bin/env python3
"""
Modèle de données AMÉLIORÉ pour représenter un email avec pièces jointes.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime

@dataclass
class EmailAttachment:
    """Classe représentant une pièce jointe d'email."""
    
    filename: str
    mime_type: str
    size: str  # Taille formatée (ex: "1.2 MB")
    size_bytes: int  # Taille en octets
    attachment_id: Optional[str] = None
    part_id: Optional[str] = None
    downloadable: bool = True
    
    @property
    def is_image(self) -> bool:
        """Vérifie si c'est une image."""
        return self.mime_type.startswith('image/')
    
    @property
    def is_document(self) -> bool:
        """Vérifie si c'est un document."""
        doc_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain'
        ]
        return self.mime_type in doc_types
    
    @property
    def icon(self) -> str:
        """Retourne une icône selon le type de fichier."""
        if self.is_image:
            return "🖼️"
        elif self.mime_type == 'application/pdf':
            return "📄"
        elif 'word' in self.mime_type:
            return "📝"
        elif 'excel' in self.mime_type or 'sheet' in self.mime_type:
            return "📊"
        elif self.mime_type.startswith('text/'):
            return "📃"
        elif self.mime_type.startswith('video/'):
            return "🎥"
        elif self.mime_type.startswith('audio/'):
            return "🎵"
        else:
            return "📎"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la pièce jointe en dictionnaire."""
        return {
            'filename': self.filename,
            'mime_type': self.mime_type,
            'size': self.size,
            'size_bytes': self.size_bytes,
            'attachment_id': self.attachment_id,
            'part_id': self.part_id,
            'downloadable': self.downloadable,
            'is_image': self.is_image,
            'is_document': self.is_document,
            'icon': self.icon
        }

@dataclass
class Email:
    """Classe AMÉLIORÉE représentant un email avec pièces jointes."""
    
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
    attachments: List[EmailAttachment] = field(default_factory=list)
    
    @property
    def is_unread(self) -> bool:
        """Vérifie si l'email est non lu."""
        return not self.is_read
    
    @property
    def is_important(self) -> bool:
        """Vérifie si l'email est marqué comme important."""
        return 'IMPORTANT' in self.labels
    
    @property
    def has_attachments(self) -> bool:
        """Vérifie si l'email a des pièces jointes."""
        return len(self.attachments) > 0
    
    @property
    def attachments_count(self) -> int:
        """Nombre de pièces jointes."""
        return len(self.attachments)
    
    @property
    def total_attachments_size(self) -> int:
        """Taille totale des pièces jointes en octets."""
        return sum(att.size_bytes for att in self.attachments)
    
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
    
    def get_attachments_by_type(self, attachment_type: str) -> List[EmailAttachment]:
        """Retourne les pièces jointes d'un type donné."""
        if attachment_type == 'images':
            return [att for att in self.attachments if att.is_image]
        elif attachment_type == 'documents':
            return [att for att in self.attachments if att.is_document]
        else:
            return [att for att in self.attachments if att.mime_type.startswith(attachment_type)]
    
    def get_attachment_by_filename(self, filename: str) -> Optional[EmailAttachment]:
        """Trouve une pièce jointe par son nom."""
        for attachment in self.attachments:
            if attachment.filename == filename:
                return attachment
        return None
    
    def format_attachments_summary(self) -> str:
        """Retourne un résumé formaté des pièces jointes."""
        if not self.has_attachments:
            return "Aucune pièce jointe"
        
        if self.attachments_count == 1:
            att = self.attachments[0]
            return f"{att.icon} {att.filename} ({att.size})"
        else:
            total_size = self._format_total_size()
            return f"📎 {self.attachments_count} pièces jointes ({total_size})"
    
    def _format_total_size(self) -> str:
        """Formate la taille totale des pièces jointes."""
        total_bytes = self.total_attachments_size
        if total_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(total_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def to_dict(self) -> dict:
        """Convertit l'email en dictionnaire avec pièces jointes."""
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
            'has_attachments': self.has_attachments,
            'attachments_count': self.attachments_count,
            'attachments': [att.to_dict() for att in self.attachments],
            'attachments_summary': self.format_attachments_summary()
        }