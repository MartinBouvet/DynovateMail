#!/usr/bin/env python3
"""
Vue Calendrier - VERSION COMPLÈTE CORRIGÉE
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCalendarWidget, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QGridLayout, QLineEdit,
    QTextEdit, QDateEdit, QTimeEdit, QComboBox, QMessageBox,
    QFrame
)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QFont, QTextCharFormat, QColor

from app.calendar_manager import CalendarManager
from app.models.calendar_model import CalendarEvent

logger = logging.getLogger(__name__)

class CalendarView(QWidget):
    """Vue du calendrier avec gestion des événements."""
    
    event_selected = pyqtSignal(object)
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        
        self.calendar_manager = calendar_manager
        self.events = []
        
        self._setup_ui()
        self.refresh_events()
    
    def _setup_ui(self):
        """Crée l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # === EN-TÊTE ===
        header_layout = QHBoxLayout()
        
        title = QLabel("📅 Calendrier")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #5b21b6;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bouton nouvel événement
        new_event_btn = QPushButton("➕ Nouvel événement")
        new_event_btn.setFont(QFont("Arial", 12))
        new_event_btn.setFixedHeight(40)
        new_event_btn.setCursor(Qt.PointingHandCursor)
        new_event_btn.clicked.connect(self._create_event)
        new_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 0 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        header_layout.addWidget(new_event_btn)
        
        # Bouton rafraîchir
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFont(QFont("Arial", 16))
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_events)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 2px solid #e5e7eb;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                border-color: #5b21b6;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # === ZONE PRINCIPALE ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # CALENDRIER
        calendar_container = QWidget()
        calendar_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 16px;
            }
        """)
        
        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(20, 20, 20, 20)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._on_date_selected)
        self.calendar.setStyleSheet("""
            QCalendarWidget QToolButton {
                height: 40px;
                width: 60px;
                color: #111827;
                font-size: 14px;
            }
            QCalendarWidget QMenu {
                width: 150px;
            }
            QCalendarWidget QSpinBox {
                width: 100px;
                font-size: 14px;
            }
            QCalendarWidget QTableView {
                selection-background-color: #5b21b6;
            }
        """)
        calendar_layout.addWidget(self.calendar)
        
        content_layout.addWidget(calendar_container, 2)
        
        # LISTE DES ÉVÉNEMENTS
        events_container = QWidget()
        events_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 16px;
            }
        """)
        
        events_layout = QVBoxLayout(events_container)
        events_layout.setContentsMargins(20, 20, 20, 20)
        events_layout.setSpacing(15)
        
        events_title = QLabel("📋 Événements")
        events_title.setFont(QFont("Arial", 18, QFont.Bold))
        events_title.setStyleSheet("color: #111827;")
        events_layout.addWidget(events_title)
        
        self.events_list = QListWidget()
        self.events_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #f9fafb;
                border-radius: 10px;
                padding: 10px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 8px;
            }
            QListWidget::item:hover {
                background-color: #f3f4f6;
                border-color: #5b21b6;
            }
            QListWidget::item:selected {
                background-color: #ede9fe;
                border-color: #5b21b6;
                color: #5b21b6;
            }
        """)
        self.events_list.itemClicked.connect(self._on_event_selected)
        events_layout.addWidget(self.events_list)
        
        content_layout.addWidget(events_container, 1)
        
        layout.addLayout(content_layout)
    
    def refresh(self):
        """Rafraîchit la vue du calendrier."""
        logger.info("Actualisation du calendrier...")
        self.refresh_events()
    
    def refresh_events(self):
        """Rafraîchit la liste des événements."""
        logger.info("Actualisation des événements du calendrier...")
        
        try:
            # Récupérer les événements
            self.events = self.calendar_manager.get_all_events()
            
            # Mettre à jour l'affichage
            self._update_calendar_highlights()
            self._update_events_list()
            
            logger.info(f"{len(self.events)} événements chargés")
        
        except Exception as e:
            logger.error(f"Erreur actualisation événements: {e}")
    
    def _update_calendar_highlights(self):
        """Met en surbrillance les dates avec des événements."""
        # Réinitialiser le format
        default_format = QTextCharFormat()
        
        # Format pour les dates avec événements
        event_format = QTextCharFormat()
        event_format.setBackground(QColor("#ede9fe"))
        event_format.setForeground(QColor("#5b21b6"))
        event_format.setFontWeight(QFont.Bold)
        
        # Appliquer le format aux dates avec événements
        for event in self.events:
            if event.start_time:
                qdate = QDate(
                    event.start_time.year,
                    event.start_time.month,
                    event.start_time.day
                )
                self.calendar.setDateTextFormat(qdate, event_format)
    
    def _update_events_list(self):
        """Met à jour la liste des événements."""
        self.events_list.clear()
        
        # Filtrer par date sélectionnée
        selected_date = self.calendar.selectedDate().toPyDate()
        
        filtered_events = [
            e for e in self.events
            if e.start_time and e.start_time.date() == selected_date
        ]
        
        if not filtered_events:
            item = QListWidgetItem("📭 Aucun événement ce jour")
            item.setFont(QFont("Arial", 11))
            item.setForeground(QColor("#9ca3af"))
            self.events_list.addItem(item)
            return
        
        # Trier par heure
        filtered_events.sort(key=lambda e: e.start_time)
        
        for event in filtered_events:
            time_str = event.start_time.strftime("%H:%M")
            item_text = f"⏰ {time_str} - {event.title}"
            
            if event.location:
                item_text += f"\n📍 {event.location}"
            
            item = QListWidgetItem(item_text)
            item.setFont(QFont("Arial", 11))
            item.setData(Qt.UserRole, event)
            self.events_list.addItem(item)
    
    def _on_date_selected(self, date: QDate):
        """Gère la sélection d'une date."""
        logger.info(f"Date sélectionnée: {date.toString()}")
        self._update_events_list()
    
    def _on_event_selected(self, item: QListWidgetItem):
        """Gère la sélection d'un événement."""
        event = item.data(Qt.UserRole)
        
        if event:
            logger.info(f"Événement sélectionné: {event.title}")
            self._show_event_details(event)
    
    def _show_event_details(self, event: CalendarEvent):
        """Affiche les détails d'un événement."""
        details = f"""
📅 {event.title}

⏰ Date: {event.start_time.strftime('%d/%m/%Y à %H:%M')}
⏱️ Durée: {event.duration} minutes
"""
        
        if event.location:
            details += f"\n📍 Lieu: {event.location}"
        
        if event.description:
            details += f"\n\n📝 Description:\n{event.description}"
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Détails de l'événement")
        msg.setText(details)
        msg.setIcon(QMessageBox.Information)
        
        # Boutons
        msg.addButton("✏️ Modifier", QMessageBox.ActionRole)
        msg.addButton("🗑️ Supprimer", QMessageBox.DestructiveRole)
        msg.addButton("Fermer", QMessageBox.RejectRole)
        
        result = msg.exec()
        
        if result == 0:  # Modifier
            self._edit_event(event)
        elif result == 1:  # Supprimer
            self._delete_event(event)
    
    def _create_event(self):
        """Crée un nouvel événement."""
        dialog = EventDialog(parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            event = dialog.get_event()
            
            try:
                self.calendar_manager.add_event(event)
                self.refresh_events()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"✅ Événement '{event.title}' créé !"
                )
                
                logger.info(f"Événement créé: {event.title}")
            
            except Exception as e:
                logger.error(f"Erreur création événement: {e}")
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de créer l'événement:\n{e}"
                )
    
    def _edit_event(self, event: CalendarEvent):
        """Modifie un événement."""
        dialog = EventDialog(event=event, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            updated_event = dialog.get_event()
            
            try:
                # Mettre à jour l'événement
                self.calendar_manager.update_event(event.id, updated_event)
                self.refresh_events()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"✅ Événement modifié !"
                )
                
                logger.info(f"Événement modifié: {event.id}")
            
            except Exception as e:
                logger.error(f"Erreur modification événement: {e}")
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de modifier l'événement:\n{e}"
                )
    
    def _delete_event(self, event: CalendarEvent):
        """Supprime un événement."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'événement '{event.title}' ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.calendar_manager.delete_event(event.id)
                self.refresh_events()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    "✅ Événement supprimé !"
                )
                
                logger.info(f"Événement supprimé: {event.id}")
            
            except Exception as e:
                logger.error(f"Erreur suppression événement: {e}")
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de supprimer l'événement:\n{e}"
                )


class EventDialog(QDialog):
    """Dialogue pour créer/modifier un événement."""
    
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
            QDialogButtonBox.Save | 
            QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self._apply_dialog_style()
    
    def _populate_fields(self):
        """Remplit les champs avec les données de l'événement."""
        if not self.event:
            return
        
        self.title_input.setText(self.event.title)
        
        if self.event.start_time:
            self.date_input.setDate(QDate(
                self.event.start_time.year,
                self.event.start_time.month,
                self.event.start_time.day
            ))
            self.start_time_input.setTime(QTime(
                self.event.start_time.hour,
                self.event.start_time.minute
            ))
        
        if self.event.duration:
            self.duration_input.setCurrentText(str(self.event.duration))
        
        if self.event.location:
            self.location_input.setText(self.event.location)
        
        if self.event.description:
            self.description_input.setPlainText(self.event.description)
    
    def get_event(self) -> CalendarEvent:
        """Récupère l'événement depuis les champs du formulaire."""
        # Combiner date et heure
        date = self.date_input.date()
        time = self.start_time_input.time()
        
        start_time = datetime(
            date.year(),
            date.month(),
            date.day(),
            time.hour(),
            time.minute()
        )
        
        # Créer l'événement
        event = CalendarEvent(
            id=self.event.id if self.event else None,
            title=self.title_input.text().strip(),
            start_time=start_time,
            duration=int(self.duration_input.currentText()),
            location=self.location_input.text().strip() or None,
            description=self.description_input.toPlainText().strip() or None
        )
        
        return event
    
    def _apply_dialog_style(self):
        """Applique les styles au dialogue."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QLabel {
                color: #374151;
                font-size: 12px;
                font-weight: bold;
            }
            
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QComboBox {
                background-color: #ffffff;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                color: #111827;
            }
            
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, 
            QTimeEdit:focus, QComboBox:focus {
                border-color: #5b21b6;
                background-color: #faf5ff;
            }
            
            QDateEdit::drop-down, QTimeEdit::drop-down, QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QDateEdit::down-arrow, QTimeEdit::down-arrow, QComboBox::down-arrow {
                image: url(none);
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #5b21b6;
                margin-right: 5px;
            }
            
            QDialogButtonBox QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QDialogButtonBox QPushButton:hover {
                background-color: #4c1d95;
            }
            
            QDialogButtonBox QPushButton[text="Cancel"],
            QDialogButtonBox QPushButton[text="Annuler"] {
                background-color: #f3f4f6;
                color: #374151;
                border: 2px solid #e5e7eb;
            }
            
            QDialogButtonBox QPushButton[text="Cancel"]:hover,
            QDialogButtonBox QPushButton[text="Annuler"]:hover {
                background-color: #e5e7eb;
            }
        """)