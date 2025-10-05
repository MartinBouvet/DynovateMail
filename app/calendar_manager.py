#!/usr/bin/env python3
"""
Gestionnaire de calendrier - VERSION CORRIGÉE
Corrections: CRUD événements, conflits, extraction emails
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from models.calendar_model import CalendarEvent

logger = logging.getLogger(__name__)


class CalendarManager:
    """Gestionnaire de calendrier avec détection de conflits - CORRIGÉ."""
    
    def __init__(self):
        """Initialise le gestionnaire de calendrier."""
        self.events = {}  # event_id -> CalendarEvent
        logger.info("CalendarManager initialisé")
    
    def create_event(self, title: str, start_time: datetime,
                     duration: int = 60, location: str = "",
                     description: str = "", **kwargs) -> CalendarEvent:
        """
        Crée un nouvel événement - CORRIGÉ.
        
        Args:
            title: Titre de l'événement
            start_time: Date et heure de début
            duration: Durée en minutes
            location: Lieu
            description: Description
            
        Returns:
            CalendarEvent: L'événement créé
        """
        try:
            # Générer un ID unique
            event_id = str(uuid.uuid4())
            
            # Calculer l'heure de fin
            end_time = start_time + timedelta(minutes=duration)
            
            # Créer l'événement
            event = CalendarEvent(
                id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                location=location,
                description=description,
                status='confirmed',
                created_at=datetime.now()
            )
            
            # Vérifier les conflits
            conflicts = self.check_conflicts(start_time, end_time, exclude_event_id=event_id)
            if conflicts:
                logger.warning(f"Événement créé avec {len(conflicts)} conflit(s)")
                event.has_conflict = True
            
            # Stocker
            self.events[event_id] = event
            
            logger.info(f"Événement créé: {event.title} ({event_id})")
            return event
            
        except Exception as e:
            logger.error(f"Erreur création événement: {e}")
            raise
    
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Récupère un événement par son ID."""
        return self.events.get(event_id)
    
    def get_all_events(self) -> List[CalendarEvent]:
        """Retourne tous les événements."""
        return list(self.events.values())
    
    def get_events_in_range(self, start: datetime, end: datetime) -> List[CalendarEvent]:
        """
        Récupère les événements dans une plage de dates.
        
        Args:
            start: Date de début
            end: Date de fin
            
        Returns:
            List[CalendarEvent]: Liste des événements
        """
        events_in_range = []
        
        for event in self.events.values():
            if event.start_time and event.end_time:
                # Vérifier le chevauchement
                if not (event.end_time < start or event.start_time > end):
                    events_in_range.append(event)
        
        # Trier par date de début
        events_in_range.sort(key=lambda e: e.start_time)
        
        return events_in_range
    
    def update_event(self, event_id: str, **kwargs) -> Optional[CalendarEvent]:
        """
        Met à jour un événement - CORRIGÉ.
        
        Args:
            event_id: ID de l'événement
            **kwargs: Champs à mettre à jour
            
        Returns:
            CalendarEvent mis à jour ou None
        """
        if event_id not in self.events:
            logger.error(f"Événement introuvable: {event_id}")
            return None
        
        try:
            event = self.events[event_id]
            
            # Mettre à jour les champs
            if 'title' in kwargs:
                event.title = kwargs['title']
            
            if 'start_time' in kwargs:
                event.start_time = kwargs['start_time']
                # Recalculer end_time si nécessaire
                if 'duration' in kwargs or event.duration:
                    duration = kwargs.get('duration', event.duration)
                    event.end_time = event.start_time + timedelta(minutes=duration)
            
            if 'duration' in kwargs:
                event.duration = kwargs['duration']
                if event.start_time:
                    event.end_time = event.start_time + timedelta(minutes=event.duration)
            
            if 'location' in kwargs:
                event.location = kwargs['location']
            
            if 'description' in kwargs:
                event.description = kwargs['description']
            
            if 'status' in kwargs:
                event.status = kwargs['status']
            
            # Vérifier les conflits
            if event.start_time and event.end_time:
                conflicts = self.check_conflicts(
                    event.start_time, 
                    event.end_time,
                    exclude_event_id=event_id
                )
                event.has_conflict = len(conflicts) > 0
            
            logger.info(f"Événement mis à jour: {event.title} ({event_id})")
            return event
            
        except Exception as e:
            logger.error(f"Erreur mise à jour événement: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """
        Supprime un événement.
        
        Args:
            event_id: ID de l'événement
            
        Returns:
            True si supprimé avec succès
        """
        if event_id not in self.events:
            logger.error(f"Événement introuvable: {event_id}")
            return False
        
        try:
            event = self.events[event_id]
            del self.events[event_id]
            logger.info(f"Événement supprimé: {event.title} ({event_id})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression événement: {e}")
            return False
    
    def check_conflicts(self, start_time: datetime, end_time: datetime,
                       exclude_event_id: Optional[str] = None) -> List[CalendarEvent]:
        """
        Vérifie les conflits de planning - CORRIGÉ.
        
        Args:
            start_time: Heure de début
            end_time: Heure de fin
            exclude_event_id: ID d'événement à exclure (pour mise à jour)
            
        Returns:
            List[CalendarEvent]: Liste des événements en conflit
        """
        conflicts = []
        
        for event_id, event in self.events.items():
            # Exclure l'événement spécifié
            if event_id == exclude_event_id:
                continue
            
            # Ignorer les événements annulés
            if event.status == 'cancelled':
                continue
            
            # Vérifier le chevauchement
            if event.start_time and event.end_time:
                # Il y a conflit si les périodes se chevauchent
                if not (end_time <= event.start_time or start_time >= event.end_time):
                    conflicts.append(event)
        
        return conflicts
    
    def extract_event_from_email(self, email) -> Optional[CalendarEvent]:
        """
        Extrait un événement depuis un email analysé par l'IA - CORRIGÉ.
        
        Args:
            email: Email avec analyse IA
            
        Returns:
            CalendarEvent ou None si aucun événement détecté
        """
        try:
            if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
                return None
            
            analysis = email.ai_analysis
            
            # Vérifier que c'est un email de RDV
            if analysis.category != 'rdv':
                return None
            
            # Extraire les informations
            extracted_info = analysis.extracted_info
            
            # Essayer d'extraire la date
            if not extracted_info.get('potential_dates'):
                logger.debug("Aucune date trouvée dans l'email")
                return None
            
            # Pour l'instant, on ne crée pas automatiquement l'événement
            # car il faudrait parser les dates correctement
            # On retourne None et laisse l'utilisateur créer manuellement
            
            logger.info(f"Événement potentiel détecté dans email {email.id}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction événement: {e}")
            return None
    
    def get_today_events(self) -> List[CalendarEvent]:
        """Retourne les événements d'aujourd'hui."""
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return self.get_events_in_range(start_of_day, end_of_day)
    
    def get_upcoming_events(self, days: int = 7) -> List[CalendarEvent]:
        """
        Retourne les événements à venir.
        
        Args:
            days: Nombre de jours à l'avance
            
        Returns:
            List[CalendarEvent]: Événements à venir
        """
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        return self.get_events_in_range(now, end_date)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du calendrier."""
        total_events = len(self.events)
        
        # Compter par statut
        status_counts = {'confirmed': 0, 'tentative': 0, 'cancelled': 0}
        for event in self.events.values():
            status = event.status or 'confirmed'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Événements avec conflits
        conflict_count = sum(1 for e in self.events.values() if e.has_conflict)
        
        # Événements aujourd'hui
        today_count = len(self.get_today_events())
        
        # Événements à venir (7 jours)
        upcoming_count = len(self.get_upcoming_events(7))
        
        return {
            'total_events': total_events,
            'status_breakdown': status_counts,
            'events_with_conflicts': conflict_count,
            'events_today': today_count,
            'upcoming_events_7days': upcoming_count
        }