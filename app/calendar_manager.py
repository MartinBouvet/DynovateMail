#!/usr/bin/env python3
"""
Gestionnaire de calendrier - VERSION CORRIGÉE
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """Représente un événement de calendrier."""
    id: str
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    participants: List[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    email_id: Optional[str] = None  # ID de l'email source
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = []

class CalendarManager:
    """Gestionnaire de calendrier avec extraction depuis emails."""
    
    def __init__(self):
        """Initialise le gestionnaire."""
        self.events = []
        logger.info("CalendarManager initialisé")
    
    def get_events(self, days_ahead: int = 30) -> List[CalendarEvent]:
        """
        Récupère les événements à venir.
        
        Args:
            days_ahead: Nombre de jours à l'avance
            
        Returns:
            Liste des événements
        """
        try:
            # Filtrer les événements futurs
            now = datetime.now()
            future_limit = now + timedelta(days=days_ahead)
            
            future_events = [
                event for event in self.events
                if event.start_time >= now and event.start_time <= future_limit
            ]
            
            # Trier par date
            future_events.sort(key=lambda e: e.start_time)
            
            logger.info(f"✅ {len(future_events)} événements à venir sur {days_ahead} jours")
            return future_events
        
        except Exception as e:
            logger.error(f"Erreur get_events: {e}")
            return []
    
    def extract_meeting_from_email(self, email) -> Optional[CalendarEvent]:
        """
        Extrait un rendez-vous depuis un email.
        
        Args:
            email: Email à analyser
            
        Returns:
            CalendarEvent si détecté, None sinon
        """
        try:
            import re
            
            # Mots-clés de réunion
            meeting_keywords = [
                'réunion', 'meeting', 'rdv', 'rendez-vous', 
                'zoom', 'teams', 'entretien', 'call', 'visio'
            ]
            
            subject_lower = (email.subject or '').lower()
            body_lower = (email.body or email.snippet or '').lower()
            
            # Vérifier si c'est un email de réunion
            is_meeting = any(keyword in subject_lower or keyword in body_lower 
                           for keyword in meeting_keywords)
            
            if not is_meeting:
                return None
            
            # Extraire la date/heure (patterns simples)
            text = f"{email.subject} {email.body or email.snippet or ''}"
            
            # Pattern pour dates françaises: "le 15/10/2025 à 14h30"
            date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:à|a)?\s*(\d{1,2})h?(\d{2})?'
            date_match = re.search(date_pattern, text)
            
            if date_match:
                date_str, hour, minute = date_match.groups()
                minute = minute or '00'
                
                # Parser la date
                try:
                    # Essayer différents formats
                    for date_format in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y']:
                        try:
                            date_obj = datetime.strptime(date_str, date_format)
                            break
                        except:
                            continue
                    else:
                        return None
                    
                    # Ajouter l'heure
                    event_time = date_obj.replace(hour=int(hour), minute=int(minute))
                    
                    # Créer l'événement
                    event = CalendarEvent(
                        id=f"email_{email.id}",
                        title=email.subject or "Réunion",
                        start_time=event_time,
                        end_time=event_time + timedelta(hours=1),  # 1h par défaut
                        participants=[email.sender],
                        email_id=email.id
                    )
                    
                    logger.info(f"✅ Réunion extraite: {event.title} le {event_time}")
                    return event
                
                except Exception as e:
                    logger.error(f"Erreur parsing date: {e}")
                    return None
            
            return None
        
        except Exception as e:
            logger.error(f"Erreur extraction réunion: {e}")
            return None
    
    def add_event(self, event: CalendarEvent):
        """Ajoute un événement au calendrier."""
        self.events.append(event)
        logger.info(f"✅ Événement ajouté: {event.title}")
    
    def remove_event(self, event_id: str):
        """Supprime un événement."""
        self.events = [e for e in self.events if e.id != event_id]
        logger.info(f"🗑️ Événement supprimé: {event_id}")
    
    def get_event_by_id(self, event_id: str) -> Optional[CalendarEvent]:
        """Récupère un événement par son ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        return None
    
    def get_events_for_date(self, date: datetime) -> List[CalendarEvent]:
        """Récupère tous les événements d'une date donnée."""
        target_date = date.date()
        
        events_on_date = [
            event for event in self.events
            if event.start_time.date() == target_date
        ]
        
        events_on_date.sort(key=lambda e: e.start_time)
        return events_on_date
    
    def has_conflict(self, new_event: CalendarEvent) -> bool:
        """Vérifie si un nouvel événement entre en conflit avec des existants."""
        for event in self.events:
            # Vérifier le chevauchement
            if new_event.start_time < event.end_time and new_event.end_time > event.start_time:
                return True
        
        return False
    
    def get_next_event(self) -> Optional[CalendarEvent]:
        """Récupère le prochain événement à venir."""
        now = datetime.now()
        future_events = [e for e in self.events if e.start_time > now]
        
        if future_events:
            future_events.sort(key=lambda e: e.start_time)
            return future_events[0]
        
        return None
    
    def get_today_events(self) -> List[CalendarEvent]:
        """Récupère les événements d'aujourd'hui."""
        return self.get_events_for_date(datetime.now())
    
    def clear_all_events(self):
        """Supprime tous les événements."""
        self.events.clear()
        logger.info("🗑️ Tous les événements supprimés")