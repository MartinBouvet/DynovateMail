"""
Vue calendrier intégrée avec les événements extraits des emails.
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QCalendarWidget, QListWidget, QListWidgetItem,
    QSplitter, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor, QTextCharFormat

from models.calendar_model import CalendarEvent
from calendar_manager import CalendarManager

logger = logging.getLogger(__name__)

class EventDetailDialog(QDialog):
    """Dialogue pour afficher les détails d'un événement."""
    
    def __init__(self, event: CalendarEvent, parent=None):
        super().__init__(parent)
        self.event = event
        self.setWindowTitle("Détails de l'événement")
        self.setModal(True)
        self.resize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface du dialogue."""
        layout = QVBoxLayout(self)
        
        # Titre
        title_label = QLabel(self.event.title)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Informations
        info_text = f"""
        <b>Date/Heure:</b> {self.event.start_time.strftime('%d/%m/%Y à %H:%M') if self.event.start_time else 'Non définie'}
        <br><b>Durée:</b> {self.event.duration} minutes
        <br><b>Lieu:</b> {self.event.location or 'Non défini'}
        <br><b>Participants:</b> {', '.join(self.event.attendees) if self.event.attendees else 'Aucun'}
        <br><b>Statut:</b> {self.event.status}
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Description
        if self.event.description:
            desc_label = QLabel("<b>Description:</b>")
            layout.addWidget(desc_label)
            
            desc_text = QTextEdit()
            desc_text.setPlainText(self.event.description)
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(150)
            layout.addWidget(desc_text)
        
        # Boutons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class CalendarView(QWidget):
    """Vue calendrier moderne avec événements."""
    
    def __init__(self, calendar_manager: CalendarManager, parent=None):
        super().__init__(parent)
        self.calendar_manager = calendar_manager
        self.current_events = []
        self._setup_ui()
        self._setup_style()
        self.refresh_events()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Titre
        title_label = QLabel("📅 Calendrier")
        title_label.setObjectName("page-title")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Barre d'actions
        actions_layout = QHBoxLayout()
        
        # Bouton aujourd'hui
        today_btn = QPushButton("Aujourd'hui")
        today_btn.setObjectName("calendar-button")
        today_btn.clicked.connect(self._go_to_today)
        actions_layout.addWidget(today_btn)
        
        # Bouton rafraîchir
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setObjectName("calendar-button")
        refresh_btn.clicked.connect(self.refresh_events)
        actions_layout.addWidget(refresh_btn)
        
        actions_layout.addStretch()
        
        # Statistiques rapides
        self.stats_label = QLabel("0 événements")
        self.stats_label.setObjectName("stats-label")
        actions_layout.addWidget(self.stats_label)
        
        layout.addLayout(actions_layout)
        
        # Contenu principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Zone calendrier
        calendar_widget = self._create_calendar_widget()
        main_splitter.addWidget(calendar_widget)
        
        # Zone événements
        events_widget = self._create_events_widget()
        main_splitter.addWidget(events_widget)
        
        main_splitter.setSizes([400, 300])
        layout.addWidget(main_splitter)
    
    def _create_calendar_widget(self) -> QWidget:
        """Crée le widget calendrier."""
        widget = QFrame()
        widget.setObjectName("calendar-frame")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Calendrier
        self.calendar = QCalendarWidget()
        self.calendar.setObjectName("calendar")
        self.calendar.clicked.connect(self._on_date_selected)
        layout.addWidget(self.calendar)
        
        return widget
    
    def _create_events_widget(self) -> QWidget:
        """Crée le widget des événements."""
        widget = QFrame()
        widget.setObjectName("events-frame")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        events_title = QLabel("Événements")
        events_title.setObjectName("section-title")
        events_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(events_title)
        
        # Filtre par statut
        filter_layout = QHBoxLayout()
        
        self.filter_all_btn = QPushButton("Tous")
        self.filter_all_btn.setObjectName("filter-button")
        self.filter_all_btn.setCheckable(True)
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.clicked.connect(lambda: self._filter_events("all"))
        filter_layout.addWidget(self.filter_all_btn)
        
        self.filter_pending_btn = QPushButton("En attente")
        self.filter_pending_btn.setObjectName("filter-button")
        self.filter_pending_btn.setCheckable(True)
        self.filter_pending_btn.clicked.connect(lambda: self._filter_events("pending"))
        filter_layout.addWidget(self.filter_pending_btn)
        
        self.filter_confirmed_btn = QPushButton("Confirmés")
        self.filter_confirmed_btn.setObjectName("filter-button")
        self.filter_confirmed_btn.setCheckable(True)
        self.filter_confirmed_btn.clicked.connect(lambda: self._filter_events("confirmed"))
        filter_layout.addWidget(self.filter_confirmed_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Liste des événements
        self.events_list = QListWidget()
        self.events_list.setObjectName("events-list")
        self.events_list.itemDoubleClicked.connect(self._on_event_double_clicked)
        layout.addWidget(self.events_list)
        
        # Événements en attente
        pending_title = QLabel("⏳ Événements en attente de confirmation")
        pending_title.setObjectName("pending-title")
        pending_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(pending_title)
        
        self.pending_list = QListWidget()
        self.pending_list.setObjectName("pending-list")
        self.pending_list.itemDoubleClicked.connect(self._on_pending_event_clicked)
        layout.addWidget(self.pending_list)
        
        return widget
    
    def _setup_style(self):
        """Configure le style."""
        self.setStyleSheet("""
            QLabel#page-title {
                color: #000000;
                margin-bottom: 10px;
            }
            
            QPushButton#calendar-button {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            
            QPushButton#calendar-button:hover {
                background-color: #f0f0f0;
            }
            
            QLabel#stats-label {
                color: #666666;
                font-size: 14px;
            }
            
            QFrame#calendar-frame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            
            QFrame#events-frame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            
            QLabel#section-title {
                color: #000000;
                margin-bottom: 10px;
            }
            
            QPushButton#filter-button {
                background-color: #f8f8f8;
                color: #666666;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            
            QPushButton#filter-button:checked {
                background-color: #000000;
                color: #ffffff;
            }
            
            QPushButton#filter-button:hover {
                background-color: #e0e0e0;
            }
            
            QListWidget#events-list {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
            }
            
            QListWidget#pending-list {
                background-color: #fff8dc;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                max-height: 150px;
            }
            
            QLabel#pending-title {
                color: #ff6600;
                margin-top: 10px;
            }
            
            QCalendarWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
    
    def refresh_events(self):
        """Rafraîchit les événements du calendrier."""
        try:
            # Récupérer tous les événements
            all_events = self.calendar_manager.get_events()
            self.current_events = all_events
            
            # Mettre à jour les statistiques
            self.stats_label.setText(f"{len(all_events)} événements")
            
            # Mettre à jour le calendrier
            self._update_calendar_highlights()
            
            # Mettre à jour la liste des événements
            self._update_events_list()
            
            # Mettre à jour les événements en attente
            self._update_pending_events()
            
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du calendrier: {e}")
    
    def _update_calendar_highlights(self):
        """Met à jour les surlignages du calendrier."""
        # Effacer les anciens surlignages
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        
        # Ajouter les surlignages pour les événements
        for event in self.current_events:
            if event.start_time:
                date = QDate(event.start_time.year, event.start_time.month, event.start_time.day)
                
                # Format selon le statut
                format = QTextCharFormat()
                if event.status == "confirmed":
                    format.setBackground(QColor("#e8f5e8"))
                    format.setForeground(QColor("#2e7d32"))
                elif event.status == "pending":
                    format.setBackground(QColor("#fff8e1"))
                    format.setForeground(QColor("#f57c00"))
                else:
                    format.setBackground(QColor("#f3e5f5"))
                    format.setForeground(QColor("#7b1fa2"))
                
                format.setFontWeight(QFont.Weight.Bold)
                self.calendar.setDateTextFormat(date, format)
    
    def _update_events_list(self):
        """Met à jour la liste des événements."""
        self.events_list.clear()
        
        # Trier les événements par date
        sorted_events = sorted(
            [e for e in self.current_events if e.start_time],
            key=lambda x: x.start_time
        )
        
        for event in sorted_events:
            item = QListWidgetItem()
            
            # Icône selon le statut
            status_icon = "✅" if event.status == "confirmed" else "⏳" if event.status == "pending" else "❓"
            
            # Formatage de la date
            date_str = event.start_time.strftime("%d/%m à %H:%M") if event.start_time else "Date non définie"
            
            # Texte de l'item
            item.setText(f"{status_icon} {event.title}\n{date_str}")
            
            # Stocker l'événement
            item.setData(Qt.ItemDataRole.UserRole, event)
            
            self.events_list.addItem(item)
    
    def _update_pending_events(self):
        """Met à jour les événements en attente."""
        self.pending_list.clear()
        
        pending_events = self.calendar_manager.get_pending_events()
        
        for event in pending_events:
            item = QListWidgetItem()
            
            date_str = event.start_time.strftime("%d/%m à %H:%M") if event.start_time else "Date non définie"
            item.setText(f"⏳ {event.title} - {date_str}")
            
            # Stocker l'événement
            item.setData(Qt.ItemDataRole.UserRole, event)
            
            self.pending_list.addItem(item)
    
    def _filter_events(self, filter_type: str):
        """Filtre les événements affichés."""
        # Réinitialiser les boutons
        self.filter_all_btn.setChecked(filter_type == "all")
        self.filter_pending_btn.setChecked(filter_type == "pending")
        self.filter_confirmed_btn.setChecked(filter_type == "confirmed")
        
        # Filtrer les événements
        if filter_type == "all":
            filtered_events = self.current_events
        elif filter_type == "pending":
            filtered_events = [e for e in self.current_events if e.status == "pending"]
        elif filter_type == "confirmed":
            filtered_events = [e for e in self.current_events if e.status == "confirmed"]
        else:
            filtered_events = self.current_events
        
        # Mettre à jour la liste
        self.events_list.clear()
        
        for event in sorted(filtered_events, key=lambda x: x.start_time or datetime.min):
            item = QListWidgetItem()
            
            status_icon = "✅" if event.status == "confirmed" else "⏳" if event.status == "pending" else "❓"
            date_str = event.start_time.strftime("%d/%m à %H:%M") if event.start_time else "Date non définie"
            
            item.setText(f"{status_icon} {event.title}\n{date_str}")
            item.setData(Qt.ItemDataRole.UserRole, event)
            
            self.events_list.addItem(item)
    
    def _on_date_selected(self, date: QDate):
        """Gère la sélection d'une date."""
        selected_date = date.toPython()
        
        # Filtrer les événements pour cette date
        day_events = [
            e for e in self.current_events
            if e.start_time and e.start_time.date() == selected_date
        ]
        
        # Mettre à jour la liste
        self.events_list.clear()
        
        for event in day_events:
            item = QListWidgetItem()
            
            status_icon = "✅" if event.status == "confirmed" else "⏳" if event.status == "pending" else "❓"
            time_str = event.start_time.strftime("%H:%M") if event.start_time else "Heure non définie"
            
            item.setText(f"{status_icon} {event.title}\n{time_str}")
            item.setData(Qt.ItemDataRole.UserRole, event)
            
            self.events_list.addItem(item)
    
    def _on_event_double_clicked(self, item: QListWidgetItem):
        """Gère le double-clic sur un événement."""
        event = item.data(Qt.ItemDataRole.UserRole)
        if event:
            dialog = EventDetailDialog(event, self)
            dialog.exec()
    
    def _on_pending_event_clicked(self, item: QListWidgetItem):
        """Gère le clic sur un événement en attente."""
        event = item.data(Qt.ItemDataRole.UserRole)
        if event:
            from PyQt6.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self,
                "Confirmer l'événement",
                f"Voulez-vous confirmer l'événement:\n\n{event.title}\n{event.start_time.strftime('%d/%m/%Y à %H:%M') if event.start_time else 'Date non définie'}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success = self.calendar_manager.confirm_event(event.id)
                if success:
                    self.refresh_events()
                    QMessageBox.information(self, "Succès", "Événement confirmé!")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de confirmer l'événement")
    
    def _go_to_today(self):
        """Va à la date d'aujourd'hui."""
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self._on_date_selected(today)