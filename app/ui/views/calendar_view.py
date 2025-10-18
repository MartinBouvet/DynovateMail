#!/usr/bin/env python3
"""
Vue Calendrier - VERSION CORRIGÉE
"""
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QCalendarWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QTextCharFormat, QColor

from app.calendar_manager import CalendarManager

logger = logging.getLogger(__name__)

class CalendarView(QWidget):
    """Vue calendrier."""
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        
        self.calendar_manager = calendar_manager
        self.current_date = datetime.now()
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # En-tête
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #e5e7eb;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)
        
        title = QLabel("📅 Calendrier")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        new_event_btn = QPushButton("+ Nouvel événement")
        new_event_btn.setFont(QFont("Arial", 12))
        new_event_btn.setFixedHeight(38)
        new_event_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 19px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        header_layout.addWidget(new_event_btn)
        
        layout.addWidget(header)
        
        # Contenu
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(30)
        
        # Calendrier
        self.calendar = QCalendarWidget()
        self.calendar.setFixedSize(450, 400)
        self.calendar.setFont(QFont("Arial", 11))
        self.calendar.setGridVisible(True)
        
        # Style du calendrier
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }
            QCalendarWidget QToolButton {
                color: #5b21b6;
                background-color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #ede9fe;
            }
            QCalendarWidget QMenu {
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                selection-background-color: #5b21b6;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #1f2937;
                background-color: white;
                selection-background-color: #5b21b6;
                selection-color: white;
            }
        """)
        
        # Marquer les jours avec événements
        self._highlight_event_days()
        
        content_layout.addWidget(self.calendar)
        
        # Liste des événements
        events_container = QWidget()
        events_layout = QVBoxLayout(events_container)
        events_layout.setContentsMargins(0, 0, 0, 0)
        events_layout.setSpacing(15)
        
        events_title = QLabel("📋 Événements")
        events_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        events_title.setStyleSheet("color: #000000;")
        events_layout.addWidget(events_title)
        
        # Scroll des événements
        self.events_scroll = QScrollArea()
        self.events_scroll.setWidgetResizable(True)
        self.events_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        
        self.events_container = QWidget()
        self.events_layout = QVBoxLayout(self.events_container)
        self.events_layout.setContentsMargins(15, 15, 15, 15)
        self.events_layout.setSpacing(12)
        self.events_layout.addStretch()
        
        self.events_scroll.setWidget(self.events_container)
        events_layout.addWidget(self.events_scroll)
        
        content_layout.addWidget(events_container, 1)
        
        layout.addLayout(content_layout)
    
    def _highlight_event_days(self):
        """Marque les jours avec événements."""
        try:
            # Récupérer les événements du mois
            events = self.calendar_manager.get_events()
            
            # Format pour les jours avec événements
            event_format = QTextCharFormat()
            event_format.setBackground(QColor("#ede9fe"))
            event_format.setForeground(QColor("#5b21b6"))
            
            for event in events:
                if hasattr(event, 'start_time') and event.start_time:
                    date = QDate(event.start_time.year, event.start_time.month, event.start_time.day)
                    self.calendar.setDateTextFormat(date, event_format)
        
        except Exception as e:
            logger.error(f"Erreur highlight: {e}")
    
    def refresh(self):
        """Rafraîchit les événements."""
        logger.info("Chargement calendrier")
        
        try:
            # Nettoyer
            while self.events_layout.count() > 1:
                item = self.events_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Récupérer les événements
            events = self.calendar_manager.get_events()
            
            # Filtrer les événements à venir
            now = datetime.now()
            upcoming_events = [e for e in events if getattr(e, 'start_time', now) >= now]
            upcoming_events.sort(key=lambda e: getattr(e, 'start_time', now))
            
            if not upcoming_events:
                empty = QLabel("📭 Aucun événement à venir")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty.setFont(QFont("Arial", 13))
                empty.setStyleSheet("color: #9ca3af; padding: 40px;")
                self.events_layout.insertWidget(0, empty)
            else:
                for event in upcoming_events[:10]:
                    event_card = self._create_event_card(event)
                    self.events_layout.insertWidget(self.events_layout.count() - 1, event_card)
            
            # Mettre à jour le calendrier
            self._highlight_event_days()
            
            logger.info(f"✅ {len(upcoming_events)} événements")
        
        except Exception as e:
            logger.error(f"Erreur refresh: {e}")
    
    def _create_event_card(self, event) -> QFrame:
        """Crée une carte événement."""
        card = QFrame()
        card.setFixedHeight(80)
        card.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-left: 4px solid #5b21b6;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #f3f4f6;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        card_layout.setSpacing(5)
        
        # Titre
        title = getattr(event, 'title', 'Événement')
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1f2937;")
        card_layout.addWidget(title_label)
        
        # Date/Heure
        if hasattr(event, 'start_time') and event.start_time:
            date_str = event.start_time.strftime("%d/%m/%Y à %H:%M")
            date_label = QLabel(f"🕐 {date_str}")
            date_label.setFont(QFont("Arial", 11))
            date_label.setStyleSheet("color: #6b7280;")
            card_layout.addWidget(date_label)
        
        # Participants
        if hasattr(event, 'participants') and event.participants:
            participants_str = ", ".join(event.participants[:3])
            if len(event.participants) > 3:
                participants_str += f" +{len(event.participants) - 3}"
            
            participants_label = QLabel(f"👥 {participants_str}")
            participants_label.setFont(QFont("Arial", 10))
            participants_label.setStyleSheet("color: #6b7280;")
            card_layout.addWidget(participants_label)
        
        return card