"""
Gestionnaire pour les réponses automatiques en attente de validation - VERSION CORRIGÉE.
"""
import logging
import sqlite3
from typing import List, Optional
from datetime import datetime, timedelta
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
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON pending_responses(created_at)
                ''')
                
                conn.commit()
                logger.info("Base de données des réponses en attente initialisée")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise
    
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
                if not response.created_at:
                    response.created_at = datetime.now()
                if not response.updated_at:
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
                    response.reason or "",
                    response.confidence_score,
                    response.status.value,
                    response.created_at.isoformat(),
                    response.updated_at.isoformat(),
                    response.user_notes or ""
                ))
                
                response.id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Réponse en attente ajoutée: {response.id} pour {response.original_sender_email}")
                return True
                
        except sqlite3.IntegrityError as e:
            logger.error(f"Erreur d'intégrité lors de l'ajout de la réponse: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la réponse en attente: {e}")
            return False
    
    def get_pending_responses(self, limit: int = 100) -> List[PendingResponse]:
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
                    try:
                        response = self._row_to_response(row)
                        responses.append(response)
                    except Exception as e:
                        logger.error(f"Erreur lors de la conversion de la ligne {row[0]}: {e}")
                        continue
                
                logger.debug(f"Récupéré {len(responses)} réponses en attente")
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
                ''', (status.value, user_notes or "", datetime.now().isoformat(), response_id))
                
                if cursor.rowcount == 0:
                    logger.warning(f"Aucune réponse trouvée avec l'ID {response_id}")
                    return False
                
                conn.commit()
                
                logger.info(f"Statut de la réponse {response_id} mis à jour: {status.value}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut de la réponse {response_id}: {e}")
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
                
                if cursor.rowcount == 0:
                    logger.warning(f"Aucune réponse trouvée avec l'ID {response_id}")
                    return False
                
                conn.commit()
                
                logger.info(f"Contenu de la réponse {response_id} mis à jour")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du contenu de la réponse {response_id}: {e}")
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
                
                if cursor.rowcount == 0:
                    logger.warning(f"Aucune réponse trouvée avec l'ID {response_id}")
                    return False
                
                conn.commit()
                
                logger.info(f"Réponse {response_id} supprimée")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la réponse {response_id}: {e}")
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
                
                # Réponses de cette semaine
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute('''
                    SELECT COUNT(*) FROM pending_responses 
                    WHERE created_at >= ?
                ''', (week_ago,))
                week_count = cursor.fetchone()[0]
                
                return {
                    'total': total,
                    'pending': status_counts.get('pending', 0),
                    'approved': status_counts.get('approved', 0),
                    'rejected': status_counts.get('rejected', 0),
                    'sent': status_counts.get('sent', 0),
                    'today': today_count,
                    'week': week_count
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'total': 0,
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'sent': 0,
                'today': 0,
                'week': 0
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
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Supprimer seulement les réponses envoyées et rejetées anciennes
                cursor.execute('''
                    DELETE FROM pending_responses 
                    WHERE created_at < ? AND status IN ('sent', 'rejected')
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Nettoyage: {deleted_count} anciennes réponses supprimées")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            return 0
    
    def get_responses_by_status(self, status: ResponseStatus, limit: int = 50) -> List[PendingResponse]:
        """
        Récupère les réponses par statut.
        
        Args:
            status: Statut des réponses à récupérer.
            limit: Nombre maximum de réponses.
            
        Returns:
            Liste des réponses avec le statut spécifié.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM pending_responses 
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (status.value, limit))
                
                rows = cursor.fetchall()
                
                responses = []
                for row in rows:
                    try:
                        response = self._row_to_response(row)
                        responses.append(response)
                    except Exception as e:
                        logger.error(f"Erreur lors de la conversion de la ligne {row[0]}: {e}")
                        continue
                
                return responses
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réponses par statut {status.value}: {e}")
            return []
    
    def get_responses_by_category(self, category: str, limit: int = 50) -> List[PendingResponse]:
        """
        Récupère les réponses par catégorie.
        
        Args:
            category: Catégorie des réponses.
            limit: Nombre maximum de réponses.
            
        Returns:
            Liste des réponses de la catégorie spécifiée.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM pending_responses 
                    WHERE category = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (category, limit))
                
                rows = cursor.fetchall()
                
                responses = []
                for row in rows:
                    try:
                        response = self._row_to_response(row)
                        responses.append(response)
                    except Exception as e:
                        logger.error(f"Erreur lors de la conversion de la ligne {row[0]}: {e}")
                        continue
                
                return responses
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réponses par catégorie {category}: {e}")
            return []
    
    def _row_to_response(self, row) -> PendingResponse:
        """Convertit une ligne de base de données en objet PendingResponse."""
        try:
            # Vérifier que la ligne a le bon nombre de colonnes
            if len(row) < 14:
                raise ValueError(f"Ligne incomplète: {len(row)} colonnes au lieu de 14")
            
            # Convertir les dates
            created_at = None
            updated_at = None
            
            try:
                if row[11]:  # created_at
                    created_at = datetime.fromisoformat(row[11])
            except (ValueError, TypeError):
                created_at = datetime.now()
                logger.warning(f"Date de création invalide pour la réponse {row[0]}")
            
            try:
                if row[12]:  # updated_at
                    updated_at = datetime.fromisoformat(row[12])
            except (ValueError, TypeError):
                updated_at = datetime.now()
                logger.warning(f"Date de mise à jour invalide pour la réponse {row[0]}")
            
            # Convertir le statut
            try:
                status = ResponseStatus(row[10])
            except (ValueError, TypeError):
                status = ResponseStatus.PENDING
                logger.warning(f"Statut invalide pour la réponse {row[0]}: {row[10]}")
            
            return PendingResponse(
                id=row[0],
                email_id=row[1] or "",
                original_subject=row[2] or "",
                original_sender=row[3] or "",
                original_sender_email=row[4] or "",
                original_body=row[5] or "",
                category=row[6] or "general",
                proposed_response=row[7] or "",
                reason=row[8] or "",
                confidence_score=float(row[9]) if row[9] is not None else 0.0,
                status=status,
                created_at=created_at,
                updated_at=updated_at,
                user_notes=row[13] or ""
            )
        except Exception as e:
            logger.error(f"Erreur lors de la conversion de ligne en PendingResponse: {e}")
            raise
    
    def get_database_info(self) -> dict:
        """
        Récupère des informations sur la base de données.
        
        Returns:
            Dictionnaire avec les informations de la base de données.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Taille de la base de données
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                # Nombre total d'enregistrements
                cursor.execute("SELECT COUNT(*) FROM pending_responses")
                total_records = cursor.fetchone()[0]
                
                # Date du plus ancien enregistrement
                cursor.execute("SELECT MIN(created_at) FROM pending_responses")
                oldest_record = cursor.fetchone()[0]
                
                # Date du plus récent enregistrement
                cursor.execute("SELECT MAX(created_at) FROM pending_responses")
                newest_record = cursor.fetchone()[0]
                
                return {
                    'database_size_bytes': db_size,
                    'total_records': total_records,
                    'oldest_record': oldest_record,
                    'newest_record': newest_record,
                    'database_path': str(Path(self.db_path).absolute())
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations de base de données: {e}")
            return {
                'database_size_bytes': 0,
                'total_records': 0,
                'oldest_record': None,
                'newest_record': None,
                'database_path': str(Path(self.db_path).absolute())
            }
    
    def vacuum_database(self) -> bool:
        """
        Optimise la base de données en récupérant l'espace libre.
        
        Returns:
            True si l'optimisation a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.commit()
                
            logger.info("Base de données optimisée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation de la base de données: {e}")
            return False
    
    def close(self):
        """Ferme les connexions à la base de données."""
        try:
            # Rien à fermer explicitement avec sqlite3 et l'usage du context manager
            logger.debug("Gestionnaire de réponses en attente fermé")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture du gestionnaire: {e}")
    
    def __enter__(self):
        """Support du context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager."""
        self.close()