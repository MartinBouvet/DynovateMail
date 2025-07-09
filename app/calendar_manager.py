"""
Gestionnaire de calendrier intégré à la solution email.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path

from models.calendar_model import CalendarEvent
from models.email_model import Email

logger = logging.getLogger(__name__)

class CalendarManager:
    """Gestionnaire de calendrier pour les événements extraits des emails."""
    
    def __init__(self, db_path: str = "calendar.db"):
        """
        Initialise le gestionnaire de calendrier.
        
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
                
                # Créer la table des événements
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        location TEXT,
                        attendees TEXT,
                        email_id TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        status TEXT DEFAULT 'pending'
                    )
                ''')
                
                conn.commit()
                logger.info("Base de données calendrier initialisée")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
    
    def add_event(self, event: CalendarEvent) -> bool:
        """
        Ajoute un événement au calendrier.
        
        Args:
            event: L'événement à ajouter.
            
        Returns:
            True si l'ajout a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT INTO events (
                        title, description, start_time, end_time, location,
                        attendees, email_id, created_at, updated_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.title,
                    event.description,
                    event.start_time.isoformat() if event.start_time else None,
                    event.end_time.isoformat() if event.end_time else None,
                    event.location,
                    json.dumps(event.attendees),
                    event.email_id,
                    now,
                    now,
                    event.status
                ))
                
                event.id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Événement ajouté: {event.title}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'événement: {e}")
            return False
    
    def get_events(self, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """
        Récupère les événements du calendrier.
        
        Args:
            start_date: Date de début (optionnel).
            end_date: Date de fin (optionnel).
            
        Returns:
            Liste des événements.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM events"
                params = []
                
                if start_date and end_date:
                    query += " WHERE start_time >= ? AND start_time <= ?"
                    params = [start_date.isoformat(), end_date.isoformat()]
                elif start_date:
                    query += " WHERE start_time >= ?"
                    params = [start_date.isoformat()]
                elif end_date:
                    query += " WHERE start_time <= ?"
                    params = [end_date.isoformat()]
                
                query += " ORDER BY start_time ASC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                events = []
                for row in rows:
                    event = CalendarEvent(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        start_time=datetime.fromisoformat(row[3]) if row[3] else None,
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        location=row[5],
                        attendees=json.loads(row[6]) if row[6] else [],
                        email_id=row[7],
                        status=row[10]
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des événements: {e}")
            return []
    
    def update_event(self, event: CalendarEvent) -> bool:
        """
        Met à jour un événement existant.
        
        Args:
            event: L'événement à mettre à jour.
            
        Returns:
            True si la mise à jour a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE events SET
                        title = ?, description = ?, start_time = ?, end_time = ?,
                        location = ?, attendees = ?, updated_at = ?, status = ?
                    WHERE id = ?
                ''', (
                    event.title,
                    event.description,
                    event.start_time.isoformat() if event.start_time else None,
                    event.end_time.isoformat() if event.end_time else None,
                    event.location,
                    json.dumps(event.attendees),
                    now,
                    event.status,
                    event.id
                ))
                
                conn.commit()
                
                logger.info(f"Événement mis à jour: {event.title}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'événement: {e}")
            return False
    
    def delete_event(self, event_id: int) -> bool:
        """
        Supprime un événement du calendrier.
        
        Args:
            event_id: ID de l'événement à supprimer.
            
        Returns:
            True si la suppression a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
                conn.commit()
                
                logger.info(f"Événement supprimé: {event_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'événement: {e}")
            return False
    
    def get_events_for_today(self) -> List[CalendarEvent]:
        """
        Récupère les événements d'aujourd'hui.
        
        Returns:
            Liste des événements du jour.
        """
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        return self.get_events(start_of_day, end_of_day)
    
    def get_events_for_week(self) -> List[CalendarEvent]:
        """
        Récupère les événements de la semaine.
        
        Returns:
            Liste des événements de la semaine.
        """
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        start_datetime = datetime.combine(start_of_week, datetime.min.time())
        end_datetime = datetime.combine(end_of_week, datetime.max.time())
        
        return self.get_events(start_datetime, end_datetime)
    
    def get_conflicting_events(self, new_event: CalendarEvent) -> List[CalendarEvent]:
        """
        Trouve les événements en conflit avec un nouvel événement.
        
        Args:
            new_event: Le nouvel événement à vérifier.
            
        Returns:
            Liste des événements en conflit.
        """
        if not new_event.start_time or not new_event.end_time:
            return []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM events 
                    WHERE start_time < ? AND end_time > ?
                ''', (
                    new_event.end_time.isoformat(),
                    new_event.start_time.isoformat()
                ))
                
                rows = cursor.fetchall()
                
                conflicts = []
                for row in rows:
                    if row[0] != new_event.id:  # Exclure l'événement lui-même
                        conflict = CalendarEvent(
                            id=row[0],
                            title=row[1],
                            description=row[2],
                            start_time=datetime.fromisoformat(row[3]) if row[3] else None,
                            end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                            location=row[5],
                            attendees=json.loads(row[6]) if row[6] else [],
                            email_id=row[7],
                            status=row[10]
                        )
                        conflicts.append(conflict)
                
                return conflicts
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des conflits: {e}")
            return []
    
    def confirm_event(self, event_id: int) -> bool:
        """
        Confirme un événement (change le statut de 'pending' à 'confirmed').
        
        Args:
            event_id: ID de l'événement à confirmer.
            
        Returns:
            True si la confirmation a réussi, False sinon.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE events SET status = 'confirmed', updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), event_id))
                
                conn.commit()
                
                logger.info(f"Événement confirmé: {event_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la confirmation de l'événement: {e}")
            return False
    
    def get_pending_events(self) -> List[CalendarEvent]:
        """
        Récupère les événements en attente de confirmation.
        
        Returns:
            Liste des événements en attente.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM events 
                    WHERE status = 'pending'
                    ORDER BY start_time ASC
                ''')
                
                rows = cursor.fetchall()
                
                events = []
                for row in rows:
                    event = CalendarEvent(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        start_time=datetime.fromisoformat(row[3]) if row[3] else None,
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        location=row[5],
                        attendees=json.loads(row[6]) if row[6] else [],
                        email_id=row[7],
                        status=row[10]
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des événements en attente: {e}")
            return []