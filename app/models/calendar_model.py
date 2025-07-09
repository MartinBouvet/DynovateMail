"""
Modèle de données pour les événements de calendrier.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class CalendarEvent:
    """Classe représentant un événement de calendrier."""
    
    title: str
    description: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: str = ""
    attendees: List[str] = field(default_factory=list)
    email_id: Optional[str] = None
    id: Optional[int] = None
    status: str = "pending"  # pending, confirmed, cancelled
    
    @property
    def duration(self) -> Optional[int]:
        """Retourne la durée en minutes."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return None
    
    @property
    def is_all_day(self) -> bool:
        """Vérifie si l'événement dure toute la journée."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).days >= 1
        return False
    
    @property
    def is_past(self) -> bool:
        """Vérifie si l'événement est passé."""
        if self.end_time:
            return self.end_time < datetime.now()
        elif self.start_time:
            return self.start_time < datetime.now()
        return False
    
    @property
    def is_upcoming(self) -> bool:
        """Vérifie si l'événement est à venir."""
        if self.start_time:
            return self.start_time > datetime.now()
        return False
    
    @property
    def is_today(self) -> bool:
        """Vérifie si l'événement a lieu aujourd'hui."""
        if self.start_time:
            return self.start_time.date() == datetime.now().date()
        return False
    
    def to_dict(self) -> dict:
        """Convertit l'événement en dictionnaire."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'attendees': self.attendees,
            'email_id': self.email_id,
            'status': self.status,
            'duration': self.duration,
            'is_all_day': self.is_all_day,
            'is_past': self.is_past,
            'is_upcoming': self.is_upcoming,
            'is_today': self.is_today
        }
    
    def __str__(self) -> str:
        """Représentation string de l'événement."""
        if self.start_time:
            time_str = self.start_time.strftime("%d/%m/%Y %H:%M")
            if self.end_time:
                time_str += f" - {self.end_time.strftime('%H:%M')}"
            return f"{self.title} ({time_str})"
        return self.title