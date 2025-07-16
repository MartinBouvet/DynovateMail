#!/usr/bin/env python3
"""
Gestionnaire des réponses en attente de validation.
"""
import logging
import json
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path

from models.pending_response_model import PendingResponse, ResponseStatus
from models.email_model import Email

logger = logging.getLogger(__name__)

class PendingResponseManager:
    """Gestionnaire des réponses en attente."""
    
    def __init__(self, data_file: str = "app/data/pending_responses.json"):
        self.data_file = Path(data_file)
        self.pending_responses: Dict[str, PendingResponse] = {}
        
        # Créer le dossier de données si nécessaire
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._load_pending_responses()
    
    def add_pending_response(self, email: Email, suggested_response: str, confidence: float) -> PendingResponse:
        """Ajoute une réponse en attente."""
        response_id = f"resp_{email.id}_{int(datetime.now().timestamp())}"
        
        pending_response = PendingResponse(
            id=response_id,
            email_id=email.id,
            suggested_response=suggested_response,
            confidence=confidence,
            status=ResponseStatus.PENDING,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)  # Expire dans 24h
        )
        
        self.pending_responses[response_id] = pending_response
        self._save_pending_responses()
        
        logger.info(f"Réponse en attente ajoutée: {response_id}")
        return pending_response
    
    def get_pending_responses(self) -> List[PendingResponse]:
        """Retourne toutes les réponses en attente."""
        return [r for r in self.pending_responses.values() if r.status == ResponseStatus.PENDING]
    
    def approve_response(self, response_id: str, modified_response: Optional[str] = None) -> bool:
        """Approuve une réponse."""
        if response_id in self.pending_responses:
            response = self.pending_responses[response_id]
            response.status = ResponseStatus.APPROVED
            if modified_response:
                response.modified_response = modified_response
            
            self._save_pending_responses()
            logger.info(f"Réponse approuvée: {response_id}")
            return True
        
        return False
    
    def reject_response(self, response_id: str) -> bool:
        """Rejette une réponse."""
        if response_id in self.pending_responses:
            self.pending_responses[response_id].status = ResponseStatus.REJECTED
            self._save_pending_responses()
            logger.info(f"Réponse rejetée: {response_id}")
            return True
        
        return False
    
    def mark_as_sent(self, response_id: str) -> bool:
        """Marque une réponse comme envoyée."""
        if response_id in self.pending_responses:
            self.pending_responses[response_id].status = ResponseStatus.SENT
            self._save_pending_responses()
            logger.info(f"Réponse marquée comme envoyée: {response_id}")
            return True
        
        return False
    
    def cleanup_expired(self):
        """Nettoie les réponses expirées."""
        expired_count = 0
        for response in list(self.pending_responses.values()):
            if response.is_expired() and response.status == ResponseStatus.PENDING:
                response.status = ResponseStatus.EXPIRED
                expired_count += 1
        
        if expired_count > 0:
            self._save_pending_responses()
            logger.info(f"{expired_count} réponses expirées nettoyées")
    
    def _load_pending_responses(self):
        """Charge les réponses depuis le fichier."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    response = PendingResponse(
                        id=item['id'],
                        email_id=item['email_id'],
                        suggested_response=item['suggested_response'],
                        confidence=item['confidence'],
                        status=ResponseStatus(item['status']),
                        created_at=datetime.fromisoformat(item['created_at']),
                        expires_at=datetime.fromisoformat(item['expires_at']) if item.get('expires_at') else None,
                        user_notes=item.get('user_notes', ''),
                        modified_response=item.get('modified_response')
                    )
                    self.pending_responses[response.id] = response
                
                logger.info(f"{len(self.pending_responses)} réponses en attente chargées")
        
        except Exception as e:
            logger.error(f"Erreur chargement réponses en attente: {e}")
    
    def _save_pending_responses(self):
        """Sauvegarde les réponses dans le fichier."""
        try:
            data = []
            for response in self.pending_responses.values():
                data.append({
                    'id': response.id,
                    'email_id': response.email_id,
                    'suggested_response': response.suggested_response,
                    'confidence': response.confidence,
                    'status': response.status.value,
                    'created_at': response.created_at.isoformat(),
                    'expires_at': response.expires_at.isoformat() if response.expires_at else None,
                    'user_notes': response.user_notes,
                    'modified_response': response.modified_response
                })
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde réponses en attente: {e}")