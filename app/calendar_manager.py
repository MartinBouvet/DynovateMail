#!/usr/bin/env python3
"""
Gestionnaire de calendrier avec base de données SQLite.
"""
import logging
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from models.calendar_model import CalendarEvent

logger = logging.getLogger(__name__)

class CalendarManager:
    """Gestionnaire de calendrier avec persistance SQLite."""
    
    def __init__(self, db_path: str = "app/data/calendar.db"):
        self.db_path = Path(db_path)
        self.events = []
        
        # Créer le dossier de données si nécessaire
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self._load_events()
        
        logger.info("Base de données calendrier initialisée")
    
    def _init_database(self):
        """Initialise la base de données SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    start_time TEXT,
                    duration INTEGER DEFAULT 60,
                    location TEXT,
                    description TEXT,
                    attendees TEXT,
                    status TEXT DEFAULT 'confirmed',
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur initialisation base de données: {e}")
    
    def _load_events(self):
        """Charge les événements depuis la base de données."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM events ORDER BY start_time')
            rows = cursor.fetchall()
            
            self.events = []
            for row in rows:
                event = CalendarEvent(
                    id=row[0],
                    title=row[1],
                    start_time=datetime.fromisoformat(row[2]) if row[2] else None,
                    duration=row[3] or 60,
                    location=row[4],
                    description=row[5],
                    attendees=row[6].split(',') if row[6] else [],
                    status=row[7] or 'confirmed'
                )
                self.events.append(event)
            
            conn.close()
            logger.info(f"{len(self.events)} événements chargés")
            
        except Exception as e:
            logger.error(f"Erreur chargement événements: {e}")
            # Créer quelques événements de test
            self._create_sample_events()
    
    def _create_sample_events(self):
        """Crée quelques événements de test."""
        now = datetime.now()
        
        sample_events = [
            {
                'title': 'Réunion équipe',
                'start_time': now + timedelta(hours=2),
                'duration': 60,
                'location': 'Salle de conférence',
                'description': 'Point hebdomadaire avec l\'équipe',
                'status': 'confirmed'
            },
            {
                'title': 'Entretien candidat',
                'start_time': now + timedelta(days=1, hours=10),
                'duration': 45,
                'location': 'Bureau RH',
                'description': 'Entretien pour le poste de développeur',
                'status': 'confirmed'
            },
            {
                'title': 'Call client',
                'start_time': now + timedelta(days=2, hours=14),
                'duration': 30,
                'description': 'Point projet avec le client ABC',
                'status': 'pending'
            }
        ]
        
        for i, event_data in enumerate(sample_events):
            self.create_event(**event_data)
    
    def get_all_events(self) -> List[CalendarEvent]:
        """Retourne tous les événements."""
        return self.events.copy()
    
    def get_upcoming_events(self, days: int = 7) -> List[CalendarEvent]:
        """Retourne les événements à venir."""
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        upcoming = []
        for event in self.events:
            if event.start_time and now <= event.start_time <= end_date:
                upcoming.append(event)
        
        return sorted(upcoming, key=lambda e: e.start_time or datetime.min)
    
    def get_events_for_date(self, date: datetime) -> List[CalendarEvent]:
        """Retourne les événements pour une date donnée."""
        target_date = date.date()
        
        day_events = []
        for event in self.events:
            if event.start_time and event.start_time.date() == target_date:
                day_events.append(event)
        
        return sorted(day_events, key=lambda e: e.start_time or datetime.min)
    
    def create_event(self, **kwargs) -> CalendarEvent:
        """Crée un nouvel événement."""
        try:
            event_id = f"event_{int(datetime.now().timestamp())}_{len(self.events)}"
            
            event = CalendarEvent(
                id=event_id,
                title=kwargs.get('title', 'Nouvel événement'),
                start_time=kwargs.get('start_time'),
                duration=kwargs.get('duration', 60),
                location=kwargs.get('location'),
                description=kwargs.get('description'),
                attendees=kwargs.get('attendees', []),
                status=kwargs.get('status', 'confirmed')
            )
            
            # Sauvegarder en base
            self._save_event(event)
            
            # Ajouter à la liste
            self.events.append(event)
            
            logger.info(f"Événement créé: {event.title}")
            return event
            
        except Exception as e:
            logger.error(f"Erreur création événement: {e}")
            raise
    
    def update_event(self, event_id: str, **kwargs) -> CalendarEvent:
        """Met à jour un événement."""
        try:
            # Trouver l'événement
            event = None
            for e in self.events:
                if e.id == event_id:
                    event = e
                    break
            
            if not event:
                raise ValueError(f"Événement non trouvé: {event_id}")
            
            # Mettre à jour les propriétés
            for key, value in kwargs.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            
            # Sauvegarder en base
            self._save_event(event, update=True)
            
            logger.info(f"Événement mis à jour: {event.title}")
            return event
            
        except Exception as e:
            logger.error(f"Erreur mise à jour événement: {e}")
            raise
    
    def delete_event(self, event_id: str):
        """Supprime un événement."""
        try:
            # Supprimer de la base
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
            conn.close()
            
            # Supprimer de la liste
            self.events = [e for e in self.events if e.id != event_id]
            
            logger.info(f"Événement supprimé: {event_id}")
            
        except Exception as e:
            logger.error(f"Erreur suppression événement: {e}")
            raise
    
    def _save_event(self, event: CalendarEvent, update: bool = False):
        """Sauvegarde un événement en base de données."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            attendees_str = ','.join(event.attendees) if event.attendees else ''
            start_time_str = event.start_time.isoformat() if event.start_time else None
            now_str = datetime.now().isoformat()
            
            if update:
                cursor.execute('''
                    UPDATE events SET 
                    title=?, start_time=?, duration=?, location=?, 
                    description=?, attendees=?, status=?, updated_at=?
                    WHERE id=?
                ''', (
                    event.title, start_time_str, event.duration, event.location,
                    event.description, attendees_str, event.status, now_str, event.id
                ))
            else:
                cursor.execute('''
                    INSERT INTO events 
                    (id, title, start_time, duration, location, description, attendees, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.id, event.title, start_time_str, event.duration, event.location,
                    event.description, attendees_str, event.status, now_str, now_str
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde événement: {e}")
            raise
    
    def extract_event_from_email(self, email_text: str, email_sender: str = "") -> Optional[CalendarEvent]:
        """Extrait un événement potentiel depuis un email."""
        # TODO: Implémenter l'extraction IA d'événements
        return None
    
    def get_conflicts(self, start_time: datetime, duration: int) -> List[CalendarEvent]:
        """Trouve les conflits d'horaire pour un créneau donné."""
        if not start_time:
            return []
        
        end_time = start_time + timedelta(minutes=duration)
        conflicts = []
        
        for event in self.events:
            if not event.start_time:
                continue
            
            event_end = event.start_time + timedelta(minutes=event.duration)
            
            # Vérifier le chevauchement
            if (start_time < event_end and end_time > event.start_time):
                conflicts.append(event)
        
        return conflicts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du calendrier."""
        now = datetime.now()
        
        # Événements aujourd'hui
        today_events = self.get_events_for_date(now)
        
        # Événements cette semaine
        week_events = self.get_upcoming_events(7)
        
        # Événements par statut
        status_counts = {}
        for event in self.events:
            status = event.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_events': len(self.events),
            'today_events': len(today_events),
            'week_events': len(week_events),
            'status_breakdown': status_counts
        }