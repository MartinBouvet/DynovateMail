#!/usr/bin/env python3
"""
Vue calendrier - VERSION CORRIGÉE
Design moderne, boutons visibles, invitations Teams fonctionnelles
"""
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QFrame, QScrollArea, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QDialog, QDialogButtonBox, QDateTimeEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QColor

from app.calendar_manager import CalendarManager, CalendarEvent

logger = logging.getLogger(__name__)


class EventDialog(QDialog):
    """Dialog pour créer/éditer un événement avec design moderne."""
    
    def __init__(self, parent=None, event: CalendarEvent = None):
        super().__init__(parent)
        
        self.event = event
        self.event_data = None
        
        self.setWindowTitle("✨ Nouvel événement" if not event else "✏️ Modifier l'événement")
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #202124;
                font-size: 14px;
            }
            QLineEdit, QTextEdit, QDateTimeEdit, QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: #ffffff;
                color: #202124;
            }
            QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus, QComboBox:focus {
                border-color: #000000;
            }
            QPushButton {
                background-color: #000000;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton:pressed {
                background-color: #666666;
            }
            QCheckBox {
                color: #202124;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #000000;
                border-color: #000000;
            }
        """)
        
        self._setup_ui()
        
        if event:
            self._load_event_data()
    
    def _setup_ui(self):
        """Interface moderne."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titre
        title_label = QLabel("Titre de l'événement *")
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ex: Réunion d'équipe")
        layout.addWidget(self.title_input)
        
        # Date et heure de début
        datetime_label = QLabel("Date et heure de début *")
        datetime_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        layout.addWidget(datetime_label)
        
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDateTime(datetime.now())
        self.start_datetime.setDisplayFormat("dd/MM/yyyy HH:mm")
        layout.addWidget(self.start_datetime)
        
        # Durée
        duration_label = QLabel("Durée")
        duration_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
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
        self.duration_combo.setCurrentIndex(3)  # 1 heure par défaut
        layout.addWidget(self.duration_combo)
        
        # Lieu
        location_label = QLabel("Lieu (optionnel)")
        location_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        layout.addWidget(location_label)
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ex: Salle de réunion A")
        layout.addWidget(self.location_input)
        
        # Description
        desc_label = QLabel("Description (optionnel)")
        desc_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Ajoutez des détails...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        # Invités
        invites_label = QLabel("Invités (séparés par des virgules)")
        invites_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        layout.addWidget(invites_label)
        
        self.invites_input = QLineEdit()
        self.invites_input.setPlaceholderText("email1@exemple.com, email2@exemple.com")
        layout.addWidget(self.invites_input)
        
        # Checkbox Teams
        self.teams_checkbox = QCheckBox("📹 Créer un lien Microsoft Teams")
        self.teams_checkbox.setFont(QFont("Arial", 13))
        layout.addWidget(self.teams_checkbox)
        
        layout.addStretch()
        
        # Boutons d'action avec style visible
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f3f4;
                color: #202124;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("💾 Sauvegarder" if not self.event else "✏️ Modifier")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_event_data(self):
        """Charge les données d'un événement existant."""
        if not self.event:
            return
        
        self.title_input.setText(self.event.title)
        
        if self.event.start_time:
            self.start_datetime.setDateTime(self.event.start_time)
        
        if self.event.location:
            self.location_input.setText(self.event.location)
        
        if self.event.description:
            self.description_input.setPlainText(self.event.description)
        
        if self.event.participants:
            self.invites_input.setText(', '.join(self.event.participants))
    
    def _on_save(self):
        """Sauvegarde l'événement."""
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
        
        # Parser les invités
        invites_text = self.invites_input.text().strip()
        invites = []
        if invites_text:
            invites = [email.strip() for email in invites_text.split(',') if email.strip()]
        
        # Lien Teams
        teams_link = None
        if self.teams_checkbox.isChecked():
            import uuid
            meeting_id = str(uuid.uuid4())[:8]
            teams_link = f"https://teams.microsoft.com/l/meetup-join/{meeting_id}"
        
        self.event_data = {
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'location': self.location_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'invites': invites,
            'teams_link': teams_link,
            'create_teams': self.teams_checkbox.isChecked()
        }
        
        self.accept()


class CalendarView(QWidget):
    """Vue calendrier moderne et intuitive."""
    
    def __init__(self, calendar_manager: CalendarManager, gmail_client=None):
        super().__init__()
        
        self.calendar_manager = calendar_manager
        self.gmail_client = gmail_client
        self.current_date = datetime.now()
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Interface moderne."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: none;
            }
        """)
        header.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        # Titre
        title_label = QLabel("📅 Calendrier")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Bouton créer événement
        create_btn = QPushButton("➕ Nouvel événement")
        create_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        create_btn.clicked.connect(self._on_create_event)
        header_layout.addWidget(create_btn)
        
        layout.addWidget(header)
        
        # Contenu principal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(30)
        
        # Calendrier
        calendar_container = QFrame()
        calendar_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        calendar_container.setFixedWidth(400)
        
        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setSpacing(15)
        
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                border: none;
            }
            QCalendarWidget QToolButton {
                background-color: #000000;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #333333;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
            QCalendarWidget QSpinBox {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #ffffff;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #f8f9fa;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #202124;
                background-color: #ffffff;
                selection-background-color: #000000;
                selection-color: #ffffff;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #9ca3af;
            }
        """)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.clicked.connect(self._on_date_selected)
        calendar_layout.addWidget(self.calendar)
        
        content_layout.addWidget(calendar_container)
        
        # Liste des événements
        events_container = QFrame()
        events_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: none;
            }
        """)
        
        events_layout = QVBoxLayout(events_container)
        events_layout.setSpacing(15)
        events_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre section
        events_title = QLabel("📋 Événements à venir")
        events_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        events_title.setStyleSheet("color: #202124;")
        events_layout.addWidget(events_title)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #ffffff;")
        self.events_layout = QVBoxLayout(scroll_widget)
        self.events_layout.setSpacing(15)
        self.events_layout.setContentsMargins(0, 0, 10, 0)
        self.events_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        events_layout.addWidget(scroll)
        
        content_layout.addWidget(events_container, 1)
        
        layout.addLayout(content_layout)
    
    def _on_create_event(self):
        """Crée un nouvel événement."""
        dialog = EventDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.event_data
            
            if event_data:
                # Créer l'événement
                event = CalendarEvent(
                    id=f"manual_{datetime.now().timestamp()}",
                    title=event_data['title'],
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    location=event_data['location'],
                    description=event_data['description'],
                    participants=event_data['invites']
                )
                
                self.calendar_manager.add_event(event)
                
                # Envoyer les invitations si nécessaire
                if event_data['invites'] and self.gmail_client:
                    self._send_invitations(event, event_data['teams_link'])
                
                # Rafraîchir
                self.refresh()
                
                QMessageBox.information(
                    self,
                    "✅ Événement créé",
                    f"L'événement '{event.title}' a été ajouté au calendrier."
                )
    
    def _send_invitations(self, event: CalendarEvent, teams_link: str = None):
        """Envoie les invitations par email via Gmail."""
        try:
            if not self.gmail_client or not hasattr(self.gmail_client, 'send_email'):
                logger.warning("Gmail client non disponible pour envoyer les invitations")
                return
            
            # Construire le corps de l'email
            email_body = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #202124;
                    }}
                    .invitation {{
                        background-color: #f8f9fa;
                        border-left: 4px solid #000000;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    .details {{
                        margin: 15px 0;
                    }}
                    .label {{
                        font-weight: bold;
                        color: #000000;
                    }}
                    .teams-link {{
                        background-color: #000000;
                        color: #ffffff;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 6px;
                        display: inline-block;
                        margin-top: 15px;
                    }}
                </style>
            </head>
            <body>
                <h2>📅 Vous êtes invité(e) à un événement</h2>
                
                <div class="invitation">
                    <h3>{event.title}</h3>
                    
                    <div class="details">
                        <p><span class="label">📅 Date :</span> {event.start_time.strftime('%d/%m/%Y')}</p>
                        <p><span class="label">🕐 Heure :</span> {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}</p>
                        {f'<p><span class="label">📍 Lieu :</span> {event.location}</p>' if event.location else ''}
                        {f'<p><span class="label">📝 Description :</span> {event.description}</p>' if event.description else ''}
                    </div>
                    
                    {f'<a href="{teams_link}" class="teams-link">🎥 Rejoindre la réunion Teams</a>' if teams_link else ''}
                </div>
                
                <p>À bientôt !</p>
            </body>
            </html>
            """
            
            # Envoyer à chaque invité
            for invite in event.participants:
                try:
                    self.gmail_client.send_email(
                        to=invite,
                        subject=f"Invitation : {event.title}",
                        body=email_body
                    )
                    logger.info(f"✅ Invitation envoyée à {invite}")
                except Exception as e:
                    logger.error(f"❌ Erreur envoi à {invite}: {e}")
            
            logger.info(f"📧 Invitations envoyées à : {', '.join(event.participants)}")
            if teams_link:
                logger.info(f"🔗 Lien Teams : {teams_link}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi invitations: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_date_selected(self, date: QDate):
        """Date sélectionnée."""
        logger.info(f"📅 Date: {date.toString('dd/MM/yyyy')}")
        
        selected_datetime = datetime(date.year(), date.month(), date.day())
        events_on_date = self.calendar_manager.get_events_for_date(selected_datetime)
        
        # Nettoyer la liste
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
            empty.setFont(QFont("Arial", 13))
            empty.setStyleSheet("color: #9ca3af; padding: 40px;")
            self.events_layout.insertWidget(0, empty)
    
    def _create_event_card(self, event: CalendarEvent) -> QFrame:
        """Crée une carte d'événement moderne."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
            }
            QFrame:hover {
                border-color: #000000;
                background-color: #f0f0f0;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        
        # Titre
        title_label = QLabel(event.title)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #202124; background-color: transparent;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Heure
        if event.start_time:
            time_str = event.start_time.strftime("%H:%M")
            if event.end_time:
                time_str += f" - {event.end_time.strftime('%H:%M')}"
            
            time_label = QLabel(f"🕐 {time_str}")
            time_label.setFont(QFont("Arial", 13))
            time_label.setStyleSheet("color: #5f6368; background-color: transparent;")
            layout.addWidget(time_label)
        
        # Lieu
        if event.location:
            location_label = QLabel(f"📍 {event.location}")
            location_label.setFont(QFont("Arial", 13))
            location_label.setStyleSheet("color: #5f6368; background-color: transparent;")
            layout.addWidget(location_label)
        
        # Participants
        if event.participants:
            participants_label = QLabel(f"👥 {len(event.participants)} participant(s)")
            participants_label.setFont(QFont("Arial", 13))
            participants_label.setStyleSheet("color: #5f6368; background-color: transparent;")
            layout.addWidget(participants_label)
        
        # Boutons d'action
        if hasattr(event, 'id'):
            actions_layout = QHBoxLayout()
            actions_layout.setSpacing(10)
            
            edit_btn = QPushButton("✏️ Modifier")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #000000;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #333333;
                }
            """)
            edit_btn.clicked.connect(lambda: self._on_edit_event(event))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️ Supprimer")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #b91c1c;
                }
            """)
            delete_btn.clicked.connect(lambda: self._on_delete_event(event))
            actions_layout.addWidget(delete_btn)
            
            actions_layout.addStretch()
            layout.addLayout(actions_layout)
        
        return card
    
    def _on_edit_event(self, event: CalendarEvent):
        """Modifie un événement."""
        dialog = EventDialog(self, event)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.event_data
            
            if event_data:
                # Mettre à jour l'événement
                event.title = event_data['title']
                event.start_time = event_data['start_time']
                event.end_time = event_data['end_time']
                event.location = event_data['location']
                event.description = event_data['description']
                event.participants = event_data['invites']
                
                # Envoyer les mises à jour
                if event_data['invites'] and self.gmail_client:
                    self._send_invitations(event, event_data['teams_link'])
                
                self.refresh()
                
                QMessageBox.information(
                    self,
                    "✅ Événement modifié",
                    f"L'événement '{event.title}' a été mis à jour."
                )
    
    def _on_delete_event(self, event: CalendarEvent):
        """Supprime un événement."""
        reply = QMessageBox.question(
            self,
            "❓ Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'événement '{event.title}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.calendar_manager.remove_event(event.id)
            self.refresh()
            
            QMessageBox.information(
                self,
                "✅ Événement supprimé",
                "L'événement a été supprimé du calendrier."
            )
    
    def _highlight_event_days(self):
        """Marque les jours avec événements."""
        try:
            events = self.calendar_manager.get_events(days_ahead=60)
            
            event_format = QTextCharFormat()
            event_format.setBackground(QColor("#f0f0f0"))
            event_format.setForeground(QColor("#000000"))
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
            logger.error(f"Erreur highlight: {e}")
    
    def refresh(self):
        """Rafraîchit la vue."""
        logger.info("🔄 Refresh calendrier")
        
        # Nettoyer
        while self.events_layout.count() > 1:
            item = self.events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Charger les événements à venir
        events = self.calendar_manager.get_events(days_ahead=30)
        
        if events:
            for event in events:
                card = self._create_event_card(event)
                self.events_layout.insertWidget(self.events_layout.count() - 1, card)
        else:
            empty = QLabel("📭 Aucun événement à venir")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(QFont("Arial", 13))
            empty.setStyleSheet("color: #9ca3af; padding: 40px;")
            self.events_layout.insertWidget(0, empty)
        
        # Mettre en surbrillance les jours
        self._highlight_event_days()