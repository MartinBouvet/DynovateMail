#!/usr/bin/env python3
"""
Vue calendrier - VERSION CORRIGÉE COMPLÈTE
Corrections: Affichage événements, navigation, création
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QListWidget, QListWidgetItem, QFrame,
    QSplitter, QScrollArea, QDialog, QDialogButtonBox, QTextEdit,
    QLineEdit, QTimeEdit, QDateEdit, QComboBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QTimer, QDateTime
from PyQt6.QtGui import QFont, QColor, QTextCharFormat

from calendar_manager import CalendarManager
from models.calendar_model import CalendarEvent

logger = logging.getLogger(__name__)


class ModernCalendarWidget(QCalendarWidget):
    """Widget calendrier avec style moderne - CORRIGÉ."""
    
    def __init__(self):
        super().__init__()
        self.events_by_date = {}  # Dict[QDate, List[CalendarEvent]]
        self._setup_style()
    
    def _setup_style(self):
        """Configure le style moderne."""
        # Style général
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        
        # Format pour les dates avec événements
        self.event_format = QTextCharFormat()
        self.event_format.setBackground(QColor("#e7f3ff"))
        self.event_format.setForeground(QColor("#007bff"))
        self.event_format.setFontWeight(QFont.Weight.Bold)
        
        # Format pour aujourd'hui
        self.today_format = QTextCharFormat()
        self.today_format.setBackground(QColor("#28a745"))
        self.today_format.setForeground(QColor("#ffffff"))
        self.today_format.setFontWeight(QFont.Weight.Bold)
    
    def set_events(self, events: List[CalendarEvent]):
        """Définit les événements à afficher - CORRIGÉ."""
        self.events_by_date.clear()
        
        for event in events:
            if event.start_time:
                qdate = QDate(
                    event.start_time.year,
                    event.start_time.month,
                    event.start_time.day
                )
                if qdate not in self.events_by_date:
                    self.events_by_date[qdate] = []
                self.events_by_date[qdate].append(event)
        
        self._update_calendar_display()
    
    def _update_calendar_display(self):
        """Met à jour l'affichage du calendrier."""
        # Réinitialiser tous les formats
        for qdate in self.events_by_date.keys():
            self.setDateTextFormat(qdate, self.event_format)
        
        # Format pour aujourd'hui
        today = QDate.currentDate()
        self.setDateTextFormat(today, self.today_format)


class EventDialog(QDialog):
    """Dialogue pour créer/éditer un événement - CORRIGÉ."""
    
    def __init__(self, event: Optional[CalendarEvent] = None, parent=None):
        super().__init__(parent)
        self.event = event
        self.setWindowTitle("Nouvel événement" if not event else "Modifier l'événement")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        
        if event:
            self._populate_fields()
    
    def _setup_ui(self):
        """Configure l'interface du dialogue."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Grille de formulaire
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        
        # Titre
        form_layout.addWidget(QLabel("Titre:"), 0, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Réunion importante...")
        form_layout.addWidget(self.title_input, 0, 1)
        
        # Date
        form_layout.addWidget(QLabel("Date:"), 1, 0)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.date_input, 1, 1)
        
        # Heure de début
        form_layout.addWidget(QLabel("Heure de début:"), 2, 0)
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime(9, 0))
        form_layout.addWidget(self.start_time_input, 2, 1)
        
        # Durée
        form_layout.addWidget(QLabel("Durée (minutes):"), 3, 0)
        self.duration_input = QComboBox()
        self.duration_input.addItems(["15", "30", "45", "60", "90", "120"])
        self.duration_input.setCurrentText("60")
        self.duration_input.setEditable(True)
        form_layout.addWidget(self.duration_input, 3, 1)
        
        # Lieu
        form_layout.addWidget(QLabel("Lieu:"), 4, 0)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Salle de réunion...")
        form_layout.addWidget(self.location_input, 4, 1)
        
        layout.addLayout(form_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Détails de l'événement...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self._apply_dialog_style()
    
    def _populate_fields(self):
        """Remplit les champs avec les données de l'événement."""
        if not self.event:
            return
        
        self.title_input.setText(self.event.title or "")
        
        if self.event.start_time:
            qdate = QDate(
                self.event.start_time.year,
                self.event.start_time.month,
                self.event.start_time.day
            )
            qtime = QTime(
                self.event.start_time.hour,
                self.event.start_time.minute
            )
            self.date_input.setDate(qdate)
            self.start_time_input.setTime(qtime)
        
        if hasattr(self.event, 'duration'):
            self.duration_input.setCurrentText(str(self.event.duration))
        
        if hasattr(self.event, 'location'):
            self.location_input.setText(self.event.location or "")
        
        if hasattr(self.event, 'description'):
            self.description_input.setPlainText(self.event.description or "")
    
    def get_event_data(self) -> Dict:
        """Retourne les données de l'événement."""
        qdate = self.date_input.date()
        qtime = self.start_time_input.time()
        
        start_datetime = datetime(
            qdate.year(), qdate.month(), qdate.day(),
            qtime.hour(), qtime.minute()
        )
        
        return {
            'title': self.title_input.text().strip(),
            'start_time': start_datetime,
            'duration': int(self.duration_input.currentText()),
            'location': self.location_input.text().strip(),
            'description': self.description_input.toPlainText().strip()
        }
    
    def _apply_dialog_style(self):
        """Applique le style au dialogue."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QLabel {
                color: #495057;
                font-weight: 500;
                font-size: 13px;
            }
            
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QComboBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border-color: #007bff;
            }
            
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
        """)


class CalendarView(QWidget):
    """Vue calendrier moderne - CORRIGÉE."""
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        self.calendar_manager = calendar_manager
        self.current_events = []
        self._setup_ui()
        self._apply_style()
        
        # Charger les événements au démarrage
        QTimer.singleShot(500, self.refresh_events)
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header avec boutons d'action
        header = self._create_header()
        layout.addWidget(header)
        
# Splitter: Calendrier | Liste événements
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        
        # === GAUCHE: Widget calendrier ===
        calendar_section = self._create_calendar_section()
        splitter.addWidget(calendar_section)
        
        # === DROITE: Liste événements ===
        events_section = self._create_events_section()
        splitter.addWidget(events_section)
        
        # Proportions: Calendrier (40%) - Événements (60%)
        splitter.setSizes([450, 650])
        layout.addWidget(splitter)
    
    def _create_header(self) -> QWidget:
        """Crée le header avec actions."""
        header = QFrame()
        header.setObjectName("calendar-header")
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("📅 Calendrier")
        title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Bouton Nouvel événement
        new_event_btn = QPushButton("➕ Nouvel événement")
        new_event_btn.setObjectName("primary-btn")
        new_event_btn.setFixedHeight(40)
        new_event_btn.clicked.connect(self._create_new_event)
        layout.addWidget(new_event_btn)
        
        # Bouton Actualiser
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setObjectName("secondary-btn")
        refresh_btn.setFixedHeight(40)
        refresh_btn.clicked.connect(self.refresh_events)
        layout.addWidget(refresh_btn)
        
        return header
    
    def _create_calendar_section(self) -> QWidget:
        """Crée la section calendrier."""
        section = QFrame()
        section.setObjectName("calendar-section")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Titre section
        section_title = QLabel("📆 Vue mensuelle")
        section_title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #000000;")
        layout.addWidget(section_title)
        
        # Widget calendrier
        self.calendar_widget = ModernCalendarWidget()
        self.calendar_widget.setMinimumHeight(350)
        self.calendar_widget.clicked.connect(self._on_date_selected)
        layout.addWidget(self.calendar_widget)
        
        # Info sélection
        self.selection_info = QLabel("Sélectionnez une date pour voir les événements")
        self.selection_info.setFont(QFont("Inter", 12))
        self.selection_info.setStyleSheet("color: #6c757d; padding: 10px;")
        self.selection_info.setWordWrap(True)
        layout.addWidget(self.selection_info)
        
        layout.addStretch()
        
        return section
    
    def _create_events_section(self) -> QWidget:
        """Crée la section liste d'événements."""
        section = QFrame()
        section.setObjectName("events-section")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header avec filtre
        section_header = QHBoxLayout()
        section_header.setSpacing(15)
        
        section_title = QLabel("📋 Événements")
        section_title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #000000;")
        section_header.addWidget(section_title)
        
        section_header.addStretch()
        
        # Filtre période
        self.period_filter = QComboBox()
        self.period_filter.addItems([
            "Aujourd'hui", 
            "Cette semaine", 
            "Ce mois", 
            "Tous"
        ])
        self.period_filter.setMinimumWidth(140)
        self.period_filter.setFixedHeight(35)
        self.period_filter.currentTextChanged.connect(self._filter_events)
        section_header.addWidget(self.period_filter)
        
        layout.addLayout(section_header)
        
        # Zone de scroll pour les événements
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container pour les cartes d'événements
        self.events_container = QWidget()
        self.events_layout = QVBoxLayout(self.events_container)
        self.events_layout.setSpacing(10)
        self.events_layout.setContentsMargins(5, 5, 5, 5)
        self.events_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Message par défaut
        self.no_events_label = QLabel("📅 Aucun événement")
        self.no_events_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_events_label.setFont(QFont("Inter", 16, QFont.Weight.Medium))
        self.no_events_label.setStyleSheet("""
            QLabel {
                color: #6c757d; 
                padding: 50px;
                background-color: #f8f9fa;
                border-radius: 12px;
                border: 2px dashed #dee2e6;
                margin: 20px 0;
            }
        """)
        self.events_layout.addWidget(self.no_events_label)
        
        scroll_area.setWidget(self.events_container)
        layout.addWidget(scroll_area)
        
        return section
    
    def refresh_events(self):
        """Actualise les événements - CORRIGÉ."""
        try:
            logger.info("Actualisation des événements du calendrier...")
            
            # Récupérer tous les événements
            self.current_events = self.calendar_manager.get_all_events()
            
            logger.info(f"{len(self.current_events)} événements chargés")
            
            # Mettre à jour le calendrier
            self.calendar_widget.set_events(self.current_events)
            
            # Mettre à jour la liste
            self._filter_events(self.period_filter.currentText())
            
        except Exception as e:
            logger.error(f"Erreur actualisation événements: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les événements: {str(e)}")
    
    def _on_date_selected(self, qdate: QDate):
        """Gère la sélection d'une date - CORRIGÉ."""
        selected_date = date(qdate.year(), qdate.month(), qdate.day())
        logger.info(f"Date sélectionnée: {selected_date}")
        
        # Filtrer les événements de cette date
        events_on_date = [
            event for event in self.current_events
            if event.start_time and event.start_time.date() == selected_date
        ]
        
        if events_on_date:
            self.selection_info.setText(
                f"📅 {len(events_on_date)} événement(s) le {selected_date.strftime('%d/%m/%Y')}"
            )
            # Afficher ces événements
            self._display_specific_events(events_on_date)
        else:
            self.selection_info.setText(
                f"Aucun événement le {selected_date.strftime('%d/%m/%Y')}"
            )
    
    def _filter_events(self, period: str):
        """Filtre les événements selon la période - CORRIGÉ."""
        now = datetime.now()
        
        if period == "Aujourd'hui":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "Cette semaine":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif period == "Ce mois":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start.replace(day=28) + timedelta(days=4)
            end = next_month - timedelta(days=next_month.day)
            end = end.replace(hour=23, minute=59, second=59)
        else:  # Tous
            start = None
            end = None
        
        # Filtrer
        if start and end:
            filtered = [
                event for event in self.current_events
                if event.start_time and start <= event.start_time <= end
            ]
        else:
            filtered = self.current_events
        
        # Trier par date
        filtered.sort(key=lambda e: e.start_time if e.start_time else datetime.max)
        
        self._display_event_list(filtered)
    
    def _display_event_list(self, events: List[CalendarEvent]):
        """Affiche la liste d'événements - CORRIGÉ."""
        # Vider le container
        while self.events_layout.count():
            child = self.events_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not events:
            self.events_layout.addWidget(self.no_events_label)
            return
        
        # Créer les cartes d'événements
        for event in events:
            card = self._create_event_card(event)
            self.events_layout.addWidget(card)
    
    def _display_specific_events(self, events: List[CalendarEvent]):
        """Affiche des événements spécifiques."""
        self._display_event_list(events)
    
    def _create_event_card(self, event: CalendarEvent) -> QFrame:
        """Crée une carte d'événement - CORRIGÉE."""
        card = QFrame()
        card.setObjectName("event-card")
        card.setMinimumHeight(80)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Ligne 1: Titre + Actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        title_label = QLabel(event.title or "Sans titre")
        title_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Boutons d'action
        edit_btn = QPushButton("✏️")
        edit_btn.setObjectName("icon-btn")
        edit_btn.setFixedSize(30, 30)
        edit_btn.setToolTip("Modifier")
        edit_btn.clicked.connect(lambda: self._edit_event(event))
        header_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("icon-btn-danger")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setToolTip("Supprimer")
        delete_btn.clicked.connect(lambda: self._delete_event(event))
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Ligne 2: Infos
        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)
        
        # Date et heure
        if event.start_time:
            datetime_text = event.start_time.strftime("📅 %d/%m/%Y à %H:%M")
            datetime_label = QLabel(datetime_text)
            datetime_label.setFont(QFont("Inter", 12))
            datetime_label.setStyleSheet("color: #495057;")
            info_layout.addWidget(datetime_label)
        
        # Durée
        if hasattr(event, 'duration') and event.duration:
            duration_label = QLabel(f"⏱️ {event.duration} min")
            duration_label.setFont(QFont("Inter", 12))
            duration_label.setStyleSheet("color: #6c757d;")
            info_layout.addWidget(duration_label)
        
        # Lieu
        if hasattr(event, 'location') and event.location:
            location_label = QLabel(f"📍 {event.location}")
            location_label.setFont(QFont("Inter", 12))
            location_label.setStyleSheet("color: #6c757d;")
            info_layout.addWidget(location_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Ligne 3: Description (si présente)
        if hasattr(event, 'description') and event.description:
            desc_label = QLabel(event.description[:100] + ("..." if len(event.description) > 100 else ""))
            desc_label.setFont(QFont("Inter", 11))
            desc_label.setStyleSheet("color: #6c757d;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # Style de la carte
        card.setStyleSheet("""
            QFrame#event-card {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QFrame#event-card:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
        """)
        
        # Clic sur la carte pour afficher les détails
        card.mousePressEvent = lambda e: self._show_event_details(event)
        
        return card
    
    def _show_event_details(self, event: CalendarEvent):
        """Affiche les détails d'un événement."""
        details_text = f"""
Événement: {event.title}

📅 Date: {event.start_time.strftime('%d/%m/%Y') if event.start_time else 'Non définie'}
🕐 Heure: {event.start_time.strftime('%H:%M') if event.start_time else 'Non définie'}
⏱️ Durée: {getattr(event, 'duration', 'Non définie')} minutes
📍 Lieu: {getattr(event, 'location', 'Non défini') or 'Non défini'}

Description:
{getattr(event, 'description', 'Aucune description') or 'Aucune description'}
        """.strip()
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Détails de l'événement")
        msg.setText(details_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                color: #000000;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                background-color: #007bff;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 80px;
                font-weight: 600;
            }
            QMessageBox QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        msg.exec()
        
        logger.info(f"Détails événement affichés: {event.title}")
    
    def _create_new_event(self):
        """Crée un nouvel événement - CORRIGÉ."""
        dialog = EventDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.get_event_data()
            
            # Validation
            if not event_data['title'].strip():
                QMessageBox.warning(self, "Erreur", "Le titre est obligatoire.")
                return
            
            try:
                # Créer l'événement
                new_event = self.calendar_manager.create_event(**event_data)
                
                # Actualiser
                self.refresh_events()
                
                logger.info(f"Nouvel événement créé: {new_event.title}")
                
                QMessageBox.information(
                    self, 
                    "Succès", 
                    f"L'événement '{new_event.title}' a été créé avec succès."
                )
                
            except Exception as e:
                logger.error(f"Erreur création événement: {e}")
                QMessageBox.critical(
                    self, 
                    "Erreur", 
                    f"Impossible de créer l'événement:\n{str(e)}"
                )
    
    def _edit_event(self, event: CalendarEvent):
        """Modifie un événement - CORRIGÉ."""
        dialog = EventDialog(event, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.get_event_data()
            
            # Validation
            if not event_data['title'].strip():
                QMessageBox.warning(self, "Erreur", "Le titre est obligatoire.")
                return
            
            try:
                # Mettre à jour
                updated_event = self.calendar_manager.update_event(event.id, **event_data)
                
                # Actualiser
                self.refresh_events()
                
                logger.info(f"Événement modifié: {updated_event.title}")
                
                QMessageBox.information(
                    self, 
                    "Succès", 
                    f"L'événement '{updated_event.title}' a été modifié."
                )
                
            except Exception as e:
                logger.error(f"Erreur modification événement: {e}")
                QMessageBox.critical(
                    self, 
                    "Erreur", 
                    f"Impossible de modifier l'événement:\n{str(e)}"
                )
    
    def _delete_event(self, event: CalendarEvent):
        """Supprime un événement - CORRIGÉ."""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer l'événement '{event.title}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.calendar_manager.delete_event(event.id)
                
                # Actualiser
                self.refresh_events()
                
                logger.info(f"Événement supprimé: {event.title}")
                
                QMessageBox.information(
                    self, 
                    "Succès", 
                    "L'événement a été supprimé."
                )
                
            except Exception as e:
                logger.error(f"Erreur suppression événement: {e}")
                QMessageBox.critical(
                    self, 
                    "Erreur", 
                    f"Impossible de supprimer l'événement:\n{str(e)}"
                )
    
    def _apply_style(self):
        """Applique les styles."""
        self.setStyleSheet("""
            /* Header */
            QFrame#calendar-header {
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
            }
            
            QPushButton#primary-btn {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#primary-btn:hover { background-color: #0056b3; }
            
            QPushButton#secondary-btn {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#secondary-btn:hover { background-color: #218838; }
            
            /* Sections */
            QFrame#calendar-section, QFrame#events-section {
                background-color: #ffffff;
            }
            
            /* Boutons icônes */
            QPushButton#icon-btn {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton#icon-btn:hover { background-color: #0056b3; }
            
            QPushButton#icon-btn-danger {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton#icon-btn-danger:hover { background-color: #c82333; }
            
            /* ComboBox */
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox:focus { border-color: #007bff; }
        """)