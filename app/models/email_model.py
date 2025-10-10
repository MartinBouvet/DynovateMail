#!/usr/bin/env python3
"""
Modèles de données pour les emails - CORRIGÉ
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class EmailAttachment:
    """Pièce jointe d'un email."""
    id: str
    filename: str
    mime_type: str
    size: int
    message_id: str

@dataclass
class AIAnalysis:
    """Résultat d'analyse IA d'un email."""
    category: str
    priority: int  # 1-5
    sentiment: str
    summary: str
    is_spam: bool
    confidence: float

@dataclass
class Email:
    """Modèle d'email."""
    id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    to: List[str] = field(default_factory=list)
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    body: Optional[str] = None
    snippet: Optional[str] = None  # AJOUT du snippet
    received_date: Optional[datetime] = None
    is_read: bool = False
    is_html: bool = False
    attachments: List[EmailAttachment] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    ai_analysis: Optional[AIAnalysis] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        # S'assurer que to, cc, bcc sont des listes
        if not isinstance(self.to, list):
            self.to = [self.to] if self.to else []
        if not isinstance(self.cc, list):
            self.cc = [self.cc] if self.cc else []
        if not isinstance(self.bcc, list):
            self.bcc = [self.bcc] if self.bcc else []