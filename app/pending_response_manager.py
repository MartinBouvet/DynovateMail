"""
Gestionnaire pour les réponses automatiques en attente de validation.
"""
import logging
import sqlite3
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from models.pending_response_model import PendingResponse, ResponseStatus

logger = logging.getLogger(__name__)

class PendingResponseManager:
    """Gestionnaire pour les réponses en attente de validation."""
    
    def __init__(self, db_path: str = "pending_responses.db"):
        """
        Initialise le gestionnaire.
        
        Args:
            db_path: Chemin vers la base de données SQLite.
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pending_responses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email_id TEXT NOT NULL,
                        original_subject TEXT NOT NULL,
                        original_sender TEXT NOT NULL,
                        original_sender_email TEXT NOT NULL,
                        original_body TEXT NOT NULL,
                        category TEXT NOT NULL,
                        proposed_response TEXT NOT NULL,
                        reason TEXT,
                        confidence_score REAL DEFAULT 0.0,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        user_notes TEXT DEFAULT ''
                    )
                ''')
                
                # Index pour améliorer les performances
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_status 
                    ON pending_responses(status)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_email_id 
                    ON pending_responses(email_id)
                ''')
                
                conn.commit()
                logger.info("Base de données des réponses en attente initialisée")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
    
    def add_pending_response(self, response: PendingResponse) -> bool:
        """
        Ajoute une réponse en attente.
        
        Args:
            response: La réponse à ajouter.
            
        Returns:
            True si l'ajout a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                response.created_at = datetime.now()
                response.updated_at = datetime.now()
                
                cursor.execute('''
                    INSERT INTO pending_responses (
                        email_id, original_subject, original_sender, original_sender_email,
                        original_body, category, proposed_response, reason, confidence_score,
                        status, created_at, updated_at, user_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    response.email_id,
                    response.original_subject,
                    response.original_sender,
                    response.original_sender_email,
                    response.original_body,
                    response.category,
                    response.proposed_response,
                    response.reason,
                    response.confidence_score,
                    response.status.value,
                    now,
                    now,
                    response.user_notes
                ))
                
                response.id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Réponse en attente ajoutée: {response.id}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la réponse en attente: {e}")
            return False
    
    def get_pending_responses(self, limit: int = 50) -> List[PendingResponse]:
        """
        Récupère les réponses en attente.
        
        Args:
            limit: Nombre maximum de réponses à récupérer.
            
        Returns:
            Liste des réponses en attente.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM pending_responses 
                    WHERE status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                responses = []
                for row in rows:
                    response = self._row_to_response(row)
                    responses.append(response)
                
                return responses
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réponses en attente: {e}")
            return []
    
    def get_response_by_id(self, response_id: int) -> Optional[PendingResponse]:
        """
        Récupère une réponse par son ID.
        
        Args:
            response_id: ID de la réponse.
            
        Returns:
            La réponse ou None si non trouvée.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM pending_responses 
                    WHERE id = ?
                ''', (response_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_response(row)
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la réponse {response_id}: {e}")
            return None
    
    def update_response_status(self, response_id: int, status: ResponseStatus, 
                             user_notes: str = "") -> bool:
        """
        Met à jour le statut d'une réponse.
        
        Args:
            response_id: ID de la réponse.
            status: Nouveau statut.
            user_notes: Notes de l'utilisateur.
            
        Returns:
            True si la mise à jour a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE pending_responses 
                    SET status = ?, user_notes = ?, updated_at = ?
                    WHERE id = ?
                ''', (status.value, user_notes, datetime.now().isoformat(), response_id))
                
                conn.commit()
                
                logger.info(f"Statut de la réponse {response_id} mis à jour: {status.value}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut: {e}")
            return False
    
    def update_response_content(self, response_id: int, new_response: str) -> bool:
        """
        Met à jour le contenu d'une réponse.
        
        Args:
            response_id: ID de la réponse.
            new_response: Nouveau contenu de la réponse.
            
        Returns:
            True si la mise à jour a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE pending_responses 
                    SET proposed_response = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_response, datetime.now().isoformat(), response_id))
                
                conn.commit()
                
                logger.info(f"Contenu de la réponse {response_id} mis à jour")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du contenu: {e}")
            return False
    
    def delete_response(self, response_id: int) -> bool:
        """
        Supprime une réponse.
        
        Args:
            response_id: ID de la réponse à supprimer.
            
        Returns:
            True si la suppression a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM pending_responses 
                    WHERE id = ?
                ''', (response_id,))
                
                conn.commit()
                
                logger.info(f"Réponse {response_id} supprimée")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la réponse: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Récupère les statistiques des réponses.
        
        Returns:
            Dictionnaire des statistiques.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Compter par statut
                cursor.execute('''
                    SELECT status, COUNT(*) 
                    FROM pending_responses 
                    GROUP BY status
                ''')
                
                status_counts = dict(cursor.fetchall())
                
                # Total
                cursor.execute('SELECT COUNT(*) FROM pending_responses')
                total = cursor.fetchone()[0]
                
                # Réponses d'aujourd'hui
                today = datetime.now().date().isoformat()
                cursor.execute('''
                    SELECT COUNT(*) FROM pending_responses 
                    WHERE DATE(created_at) = ?
                ''', (today,))
                today_count = cursor.fetchone()[0]
                
                return {
                    'total': total,
                    'pending': status_counts.get('pending', 0),
                    'approved': status_counts.get('approved', 0),
                    'rejected': status_counts.get('rejected', 0),
                    'sent': status_counts.get('sent', 0),
                    'today': today_count
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'total': 0,
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'sent': 0,
                'today': 0
            }
    
    def cleanup_old_responses(self, days: int = 30) -> int:
        """
        Supprime les anciennes réponses.
        
        Args:
            days: Nombre de jours à garder.
            
        Returns:
            Nombre de réponses supprimées.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM pending_responses 
                    WHERE created_at < ? AND status IN ('sent', 'rejected')
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Nettoyage: {deleted_count} anciennes réponses supprimées")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            return 0
    
    def _row_to_response(self, row) -> PendingResponse:
        """Convertit une ligne de base de données en objet PendingResponse."""
        return PendingResponse(
            id=row[0],
            email_id=row[1],
            original_subject=row[2],
            original_sender=row[3],
            original_sender_email=row[4],
            original_body=row[5],
            category=row[6],
            proposed_response=row[7],
            reason=row[8],
            confidence_score=row[9],
            status=ResponseStatus(row[10]),
            created_at=datetime.fromisoformat(row[11]) if row[11] else None,
            updated_at=datetime.fromisoformat(row[12]) if row[12] else None,
            user_notes=row[13]
        )