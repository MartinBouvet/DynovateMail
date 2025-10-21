#!/usr/bin/env python3
"""
Vue Calendrier - DIALOGUE VISIBLE CORRIGÉ
"""
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QCalendarWidget, QDialog, QLineEdit,
    QTextEdit, QDateTimeEdit, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtGui import QFont, QTextCharFormat, QColor

from app.calendar_manager import CalendarManager, CalendarEvent

logger = logging.getLogger(__name__)


class NewEventDialog(QDialog):
    """Dialogue pour créer un événement - TEXTE VISIBLE."""
    
    def __init__(self, parent=None, default_date: datetime = None):
        super().__init__(parent)
        
        self.event_data = None
        self.default_date = default_date or datetime.now()
        
        self.setWindowTitle("📅 Nouvel événement")
        self.setFixedSize(550, 650)
        
        # IMPORTANT: Fond blanc avec texte noir
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
                background-color: transparent;
            }
            QLineEdit, QTextEdit, QDateTimeEdit, QComboBox {
                color: #000000;
                background-color: #ffffff;
                border: 2px solid #d1d5db;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #5b21b6;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus, QComboBox:focus {
                border-color: #5b21b6;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #000000;
                width: 0;
                height: 0;
            }
            QCalendarWidget {
                background-color: #ffffff;
            }
            QCalendarWidget QAbstractItemView {
                color: #000000;
                background-color: #ffffff;
                selection-background-color: #5b21b6;
                selection-color: #ffffff;
            }
            QCalendarWidget QWidget {
                color: #000000;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface du dialogue."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("Créer un nouvel événement")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        layout.addWidget(title)
        
        # Titre de l'événement
        title_label = QLabel("Titre de l'événement *")
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000;")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ex: Réunion d'équipe")
        self.title_input.setFont(QFont("Arial", 13))
        self.title_input.setFixedHeight(45)
        layout.addWidget(self.title_input)
        
        # Date et heure de début
        start_label = QLabel("Date et heure de début *")
        start_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        start_label.setStyleSheet("color: #000000;")
        layout.addWidget(start_label)
        
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setDateTime(QDateTime(self.default_date))
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.start_datetime.setFont(QFont("Arial", 13))
        self.start_datetime.setFixedHeight(45)
        layout.addWidget(self.start_datetime)
        
        # Durée
        duration_label = QLabel("Durée")
        duration_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        duration_label.setStyleSheet("color: #000000;")
        layout.addWidget(duration_label)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "15 minutes",
            "30 minutes",
            "45 minutes",
            "1 heure",
            "1h30",
            "2 heures",
            "3 heures",
            "Toute la journée"
        ])
        self.duration_combo.setCurrentText("1 heure")
        self.duration_combo.setFont(QFont("Arial", 13))
        self.duration_combo.setFixedHeight(45)
        layout.addWidget(self.duration_combo)
        
        # Lieu
        location_label = QLabel("Lieu")
        location_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        location_label.setStyleSheet("color: #000000;")
        layout.addWidget(location_label)
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ex: Salle de réunion A")
        self.location_input.setFont(QFont("Arial", 13))
        self.location_input.setFixedHeight(45)
        layout.addWidget(self.location_input)
        
        # Description
        description_label = QLabel("Description")
        description_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        description_label.setStyleSheet("color: #000000;")
        layout.addWidget(description_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Détails supplémentaires...")
        self.description_input.setFont(QFont("Arial", 13))
        self.description_input.setFixedHeight(90)
        layout.addWidget(self.description_input)
        
        layout.addStretch()
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setFont(QFont("Arial", 13))
        cancel_btn.setFixedHeight(45)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #000000;
                border: 1px solid #d1d5db;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        buttons_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("✅ Créer l'événement")
        create_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        create_btn.setFixedHeight(45)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._create_event)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_event(self):
        """Crée l'événement."""
        title = self.title_input.text().strip()
        
        if not title:
            QMessageBox.warning(self, "⚠️ Champ requis", "Veuillez entrer un titre pour l'événement.")
            return
        
        # Calculer la date de fin
        start_time = self.start_datetime.dateTime().toPyDateTime()
        
        duration_text = self.duration_combo.currentText()
        if "15 minutes" in duration_text:
            duration = timedelta(minutes=15)
        elif "30 minutes" in duration_text:
            duration = timedelta(minutes=30)
        elif "45 minutes" in duration_text:
            duration = timedelta(minutes=45)
        elif "1 heure" in duration_text:
            duration = timedelta(hours=1)
        elif "1h30" in duration_text:
            duration = timedelta(hours=1, minutes=30)
        elif "2 heures" in duration_text:
            duration = timedelta(hours=2)
        elif "3 heures" in duration_text:
            duration = timedelta(hours=3)
        else:
            duration = timedelta(hours=24)
        
        end_time = start_time + duration
        
        self.event_data = {
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'location': self.location_input.text().strip(),
            'description': self.description_input.toPlainText().strip()
        }
        
        self.accept()


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
        
        # Bouton nouvel événement
        self.new_event_btn = QPushButton("+ Nouvel événement")
        self.new_event_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.new_event_btn.setFixedHeight(42)
        self.new_event_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_event_btn.clicked.connect(self._open_new_event_dialog)
        self.new_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 21px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        header_layout.addWidget(self.new_event_btn)
        
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
        self.calendar.clicked.connect(self._on_date_selected)
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
                font-weight: bold;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #ede9fe;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #1f2937;
                background-color: white;
                selection-background-color: #5b21b6;
                selection-color: white;
            }
        """)
        
        self._highlight_event_days()
        content_layout.addWidget(self.calendar)
        
        # Liste des événements
        events_container = QWidget()
        events_layout = QVBoxLayout(events_container)
        events_layout.setContentsMargins(0, 0, 0, 0)
        events_layout.setSpacing(15)
        
        events_title = QLabel("📋 Événements à venir")
        events_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        events_title.setStyleSheet("color: #000000;")
        events_layout.addWidget(events_title)
        
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
    
    def _open_new_event_dialog(self):
        """Ouvre le dialogue."""
        logger.info("🆕 Ouverture dialogue nouvel événement")
        
        selected_date = self.calendar.selectedDate()
        default_datetime = datetime(
            selected_date.year(),
            selected_date.month(),
            selected_date.day(),
            9, 0
        )
        
        dialog = NewEventDialog(self, default_datetime)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.event_data
            
            if event_data:
                try:
                    import uuid
                    event = CalendarEvent(
                        id=f"manual_{uuid.uuid4().hex[:8]}",
                        title=event_data['title'],
                        start_time=event_data['start_time'],
                        end_time=event_data['end_time'],
                        location=event_data.get('location'),
                        description=event_data.get('description'),
                        participants=[]
                    )
                    
                    self.calendar_manager.add_event(event)
                    self.refresh()
                    
                    QMessageBox.information(
                        self,
                        "✅ Événement créé",
                        f"L'événement '{event_data['title']}' a été créé avec succès !"
                    )
                    
                    logger.info(f"✅ Événement créé: {event_data['title']}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur: {e}")
                    QMessageBox.critical(self, "❌ Erreur", f"Impossible de créer l'événement:\n{str(e)}")
    
    def _on_date_selected(self, date: QDate):
        """Date sélectionnée."""
        logger.info(f"📅 Date: {date.toString('dd/MM/yyyy')}")
        
        selected_datetime = datetime(date.year(), date.month(), date.day())
        events_on_date = self.calendar_manager.get_events_for_date(selected_datetime)
        
        while self.events_layout.count() > 1:
            item = self.events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if events_on_date:
            for event in events_on_date:
                card = self._create_event_card(event)
                self.events_layout.insertWidget(self.events_layout.count() - 1, card)
        else:
            empty = QLabel(f"📭 Aucun événement le {date.toString('dd/MM/yyyy')}")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(QFont("Arial", 12))
            empty.setStyleSheet("color: #9ca3af; padding: 30px;")
            self.events_layout.insertWidget(0, empty)
    
    def _highlight_event_days(self):
        """Marque les jours avec événements."""
        try:
            events = self.calendar_manager.get_events(days_ahead=60)
            
            event_format = QTextCharFormat()
            event_format.setBackground(QColor("#ede9fe"))
            event_format.setForeground(QColor("#5b21b6"))
            event_format.setFontWeight(QFont.Weight.Bold)
            
            for event in events:
                if hasattr(event, 'start_time') and event.start_time:
                    date = QDate(
                        event.start_time.year,
                        event.start_time.month,
                        event.start_time.day
                    )
                    self.calendar.setDateTextFormat(date, event_format)
        
        except Exception as e:
            logger.error(f"Erreur: {e}")
    
    def refresh(self):
        """Rafraîchit."""
        logger.info("🔄 Rafraîchissement calendrier")
        
        try:
            while self.events_layout.count() > 1:
                item = self.events_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            events = self.calendar_manager.get_events(days_ahead=30)
            
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
            
            self._highlight_event_days()
            
            logger.info(f"✅ {len(upcoming_events)} événements affichés")
        
        except Exception as e:
            logger.error(f"Erreur: {e}")
    
    def _create_event_card(self, event: CalendarEvent) -> QFrame:
        """Crée une carte événement."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                background-color: #ede9fe;
                border-color: #5b21b6;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        
        title = QLabel(event.title)
        title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937;")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        if event.start_time:
            time_str = event.start_time.strftime("%d/%m/%Y à %H:%M")
            if event.end_time:
                time_str += f" - {event.end_time.strftime('%H:%M')}"
            
            time_label = QLabel(f"🕐 {time_str}")
            time_label.setFont(QFont("Arial", 11))
            time_label.setStyleSheet("color: #6b7280;")
            layout.addWidget(time_label)
        
        if event.location:
            location_label = QLabel(f"📍 {event.location}")
            location_label.setFont(QFont("Arial", 11))
            location_label.setStyleSheet("color: #6b7280;")
            layout.addWidget(location_label)
        
        if event.description:
            desc = event.description[:100] + "..." if len(event.description) > 100 else event.description
            desc_label = QLabel(desc)
            desc_label.setFont(QFont("Arial", 10))
            desc_label.setStyleSheet("color: #9ca3af;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        delete_btn = QPushButton("🗑️ Supprimer")
        delete_btn.setFont(QFont("Arial", 10))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self._delete_event(event))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #dc2626;
                border: none;
                text-align: left;
                padding: 5px 0;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        layout.addWidget(delete_btn)
        
        return card
    
    def _delete_event(self, event: CalendarEvent):
        """Supprime un événement."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer '{event.title}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.calendar_manager.remove_event(event.id)
                self.refresh()
                QMessageBox.information(self, "✅ Succès", "Événement supprimé !")
                logger.info(f"✅ Supprimé: {event.title}")
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")
                QMessageBox.critical(self, "❌ Erreur", f"Impossible de supprimer:\n{str(e)}")