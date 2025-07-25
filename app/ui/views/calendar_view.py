#!/usr/bin/env python3
"""
Vue calendrier moderne corrigée avec affichage fonctionnel.
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QListWidget, QListWidgetItem, QFrame,
    QSplitter, QScrollArea, QDialog, QDialogButtonBox, QTextEdit,
    QLineEdit, QTimeEdit, QDateEdit, QComboBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QPainter, QBrush

from calendar_manager import CalendarManager
from models.calendar_model import CalendarEvent

logger = logging.getLogger(__name__)

class ModernCalendarWidget(QCalendarWidget):
    """Widget calendrier avec style moderne et événements."""
    
    def __init__(self):
        super().__init__()
        self.events_by_date = {}  # Dict[QDate, List[CalendarEvent]]
        self._setup_style()
    
    def _setup_style(self):
        """Configure le style moderne du calendrier."""
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                font-family: 'Inter';
                font-size: 14px;
            }
            
            QCalendarWidget QToolButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                color: #495057;
                font-weight: 600;
                padding: 8px 12px;
                margin: 2px;
                min-width: 40px;
                min-height: 30px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #e9ecef;
                color: #000000;
                border-color: #adb5bd;
            }
            
            QCalendarWidget QMenu {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 4px;
            }
            
            QCalendarWidget QSpinBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 8px;
                selection-background-color: #007bff;
                font-size: 14px;
                min-width: 60px;
            }
            
            QCalendarWidget QAbstractItemView {
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                selection-background-color: #007bff;
                selection-color: white;
                border: none;
                font-size: 14px;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                color: #495057;
            }
            
            QCalendarWidget QAbstractItemView:disabled {
                color: #adb5bd;
            }
            
            QCalendarWidget QHeaderView::section {
                background-color: #f8f9fa;
                color: #000000;
                font-weight: 600;
                border: 1px solid #dee2e6;
                padding: 8px;
            }
        """)
    
    def set_events(self, events: List[CalendarEvent]):
        """Définit les événements à afficher."""
        self.events_by_date.clear()
        
        for event in events:
            if event.start_time:
                qdate = QDate(event.start_time.date())
                if qdate not in self.events_by_date:
                    self.events_by_date[qdate] = []
                self.events_by_date[qdate].append(event)
        
        self.updateCells()
    
    def paintCell(self, painter: QPainter, rect, date: QDate):
        """Personnalise l'affichage des cellules avec événements."""
        super().paintCell(painter, rect, date)
        
        if date in self.events_by_date:
            events = self.events_by_date[date]
            
            # Dessiner un indicateur pour les événements
            indicator_size = 8
            x = rect.right() - indicator_size - 4
            y = rect.bottom() - indicator_size - 4
            
            # Couleur selon le nombre d'événements
            if len(events) == 1:
                color = QColor("#007bff")
            elif len(events) <= 3:
                color = QColor("#ffc107")
            else:
                color = QColor("#dc3545")
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x, y, indicator_size, indicator_size)

class EventCard(QFrame):
    """Carte d'événement moderne corrigée."""
    
    clicked = pyqtSignal(object)
    edit_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    
    def __init__(self, event: CalendarEvent):
        super().__init__()
        self.event = event
        self.setObjectName("event-card")
        self.setFixedHeight(120)
        self.setMinimumWidth(300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface de la carte."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        
        # Header avec titre et actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Titre (tronqué si trop long)
        title_text = self.event.title
        if len(title_text) > 35:
            title_text = title_text[:32] + "..."
        
        title_label = QLabel(title_text)
        title_label.setObjectName("event-title")
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Actions rapides
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip("Modifier")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 14px;
                color: #6c757d;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                color: #495057;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.event))
        header_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setToolTip("Supprimer")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 14px;
                color: #dc3545;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f5c6cb;
                color: #721c24;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.event))
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Informations principales
        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)
        
        # Heure
        if self.event.start_time:
            time_label = QLabel(f"🕐 {self.event.start_time.strftime('%H:%M')}")
            time_label.setObjectName("event-time")
            time_label.setFont(QFont("Inter", 13))
            info_layout.addWidget(time_label)
        
        # Durée
        if hasattr(self.event, 'duration') and self.event.duration and self.event.duration > 0:
            duration_label = QLabel(f"⏱️ {self.event.duration} min")
            duration_label.setObjectName("event-duration")
            duration_label.setFont(QFont("Inter", 13))
            info_layout.addWidget(duration_label)
        
        info_layout.addStretch()
        
        # Statut
        status_badge = self._create_status_badge()
        info_layout.addWidget(status_badge)
        
        layout.addLayout(info_layout)
        
        # Lieu si disponible
        if hasattr(self.event, 'location') and self.event.location:
            location_text = self.event.location
            if len(location_text) > 40:
                location_text = location_text[:37] + "..."
            
            location_label = QLabel(f"📍 {location_text}")
            location_label.setObjectName("event-location")
            location_label.setFont(QFont("Inter", 12))
            layout.addWidget(location_label)
    
    def _create_status_badge(self) -> QLabel:
        """Crée le badge de statut."""
        status_colors = {
            'confirmed': ('#28a745', 'Confirmé'),
            'pending': ('#ffc107', 'En attente'),
            'cancelled': ('#dc3545', 'Annulé'),
            'tentative': ('#6c757d', 'Provisoire')
        }
        
        status = getattr(self.event, 'status', 'confirmed')
        color, text = status_colors.get(status, ('#17a2b8', 'Inconnu'))
        
        badge = QLabel(text)
        badge.setFixedHeight(24)
        badge.setMinimumWidth(70)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                text-align: center;
            }}
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        return badge
    
    def _apply_style(self):
        """Applique le style à la carte."""
        # Couleur de bordure selon priorité
        priority = getattr(self.event, 'priority', 3)
        priority_colors = {
            1: '#dc3545',  # Rouge - Urgent
            2: '#fd7e14',  # Orange - Haute
            3: '#ffc107',  # Jaune - Normale
            4: '#28a745',  # Vert - Basse
            5: '#6c757d'   # Gris - Très basse
        }
        
        border_color = priority_colors.get(priority, '#dee2e6')
        
        self.setStyleSheet(f"""
            #event-card {{
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-left: 4px solid {border_color};
                border-radius: 12px;
                margin: 6px 0;
            }}
            
            #event-card:hover {{
                background-color: #f8f9fa;
                border-color: #adb5bd;
                border-left: 4px solid {border_color};
            }}
            
            #event-title {{
                color: #000000;
            }}
            
            #event-time, #event-duration {{
                color: #6c757d;
            }}
            
            #event-location {{
                color: #6c757d;
            }}
        """)
    
    def mousePressEvent(self, event):
        """Gère le clic sur la carte."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.event)
        super().mousePressEvent(event)

class EventDialog(QDialog):
    """Dialogue pour créer/modifier un événement - Version corrigée."""
    
    def __init__(self, event: Optional[CalendarEvent] = None, parent=None):
        super().__init__(parent)
        self.event = event
        self.is_editing = event is not None
        
        self.setWindowTitle("Modifier l'événement" if self.is_editing else "Nouvel événement")
        self.setModal(True)
        self.setFixedSize(550, 500)
        
        self._setup_ui()
        self._apply_style()
        
        if self.is_editing:
            self._populate_fields()
    
    def _setup_ui(self):
        """Configure l'interface du dialogue."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Titre du dialogue
        title_label = QLabel("✏️ Modifier l'événement" if self.is_editing else "➕ Nouvel événement")
        title_label.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Grille pour les champs
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setSpacing(15)
        form_layout.setColumnStretch(1, 1)
        
        # Titre
        form_layout.addWidget(QLabel("Titre:"), 0, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titre de l'événement")
        form_layout.addWidget(self.title_input, 0, 1)
        
        # Date
        form_layout.addWidget(QLabel("Date:"), 1, 0)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setMinimumWidth(150)
        form_layout.addWidget(self.date_input, 1, 1)
        
        # Heure
        form_layout.addWidget(QLabel("Heure:"), 2, 0)
        time_layout = QHBoxLayout()
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime())
        self.time_input.setMinimumWidth(100)
        time_layout.addWidget(self.time_input)
        time_layout.addStretch()
        form_layout.addLayout(time_layout, 2, 1)
        
        # Durée et statut
        form_layout.addWidget(QLabel("Durée:"), 3, 0)
        duration_layout = QHBoxLayout()
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("60")
        self.duration_input.setMaximumWidth(80)
        duration_layout.addWidget(self.duration_input)
        duration_layout.addWidget(QLabel("minutes"))
        duration_layout.addStretch()
        form_layout.addLayout(duration_layout, 3, 1)
        
        form_layout.addWidget(QLabel("Statut:"), 4, 0)
        self.status_input = QComboBox()
        self.status_input.addItems(["confirmed", "pending", "tentative", "cancelled"])
        self.status_input.setMinimumWidth(150)
        form_layout.addWidget(self.status_input, 4, 1)
        
        # Lieu
        form_layout.addWidget(QLabel("Lieu:"), 5, 0)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Lieu de l'événement")
        form_layout.addWidget(self.location_input, 5, 1)
        
        layout.addWidget(form_widget)
        
        # Description
        desc_label = QLabel("Description:")
        desc_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(120)
        self.description_input.setPlaceholderText("Description de l'événement (optionnel)")
        layout.addWidget(self.description_input)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("✅ Sauvegarder")
        save_btn.setFixedHeight(40)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _apply_style(self):
        """Applique le style au dialogue."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }
            
            QLabel {
                color: #495057;
                font-weight: 500;
                font-size: 14px;
                min-width: 80px;
            }
            
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 12px;
                color: #495057;
                font-size: 14px;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            
            QDateEdit, QTimeEdit, QComboBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 12px;
                color: #495057;
                font-size: 14px;
                min-height: 20px;
            }
            
            QDateEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border-color: #007bff;
            }
            
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton[text*="Sauvegarder"] {
                background-color: #007bff;
                color: white;
            }
            
            QPushButton[text*="Sauvegarder"]:hover {
                background-color: #0056b3;
            }
            
            QPushButton[text*="Annuler"] {
                background-color: #6c757d;
                color: white;
            }
            
            QPushButton[text*="Annuler"]:hover {
                background-color: #545b62;
            }
        """)
    
    def _populate_fields(self):
        """Remplit les champs avec les données de l'événement."""
        if not self.event:
            return
        
        self.title_input.setText(self.event.title or "")
        
        if self.event.start_time:
            self.date_input.setDate(QDate(self.event.start_time.date()))
            self.time_input.setTime(QTime(self.event.start_time.time()))
        
        if hasattr(self.event, 'duration') and self.event.duration:
            self.duration_input.setText(str(self.event.duration))
        
        if hasattr(self.event, 'status') and self.event.status:
            index = self.status_input.findText(self.event.status)
            if index >= 0:
                self.status_input.setCurrentIndex(index)
        
        if hasattr(self.event, 'location'):
            self.location_input.setText(self.event.location or "")
        
        if hasattr(self.event, 'description'):
            self.description_input.setPlainText(self.event.description or "")
    
    def get_event_data(self) -> Dict:
        """Retourne les données de l'événement."""
        date = self.date_input.date().toPython()
        time = self.time_input.time().toPython()
        start_time = datetime.combine(date, time)
        
        duration_text = self.duration_input.text().strip()
        duration = int(duration_text) if duration_text.isdigit() else 60
        
        return {
            'title': self.title_input.text().strip(),
            'start_time': start_time,
            'duration': duration,
            'status': self.status_input.currentText(),
            'location': self.location_input.text().strip(),
            'description': self.description_input.toPlainText().strip()
        }

class CalendarView(QWidget):
    """Vue calendrier moderne corrigée."""
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        self.calendar_manager = calendar_manager
        self.current_events = []
        self.filtered_events = []
        
        self.setObjectName("calendar-view")
        self._setup_ui()
        self._apply_style()
        self._setup_connections()
        
        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_events)
        self.refresh_timer.start(300000)  # 5 minutes
        
        # Charger les événements initiaux
        self.refresh_events()
    
    def _setup_ui(self):
        """Configure l'interface de la vue calendrier."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(25)
        
        # Header avec titre et actions
        header = self._create_header()
        layout.addWidget(header)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        
        # Section calendrier
        calendar_section = self._create_calendar_section()
        splitter.addWidget(calendar_section)
        
        # Section événements
        events_section = self._create_events_section()
        splitter.addWidget(events_section)
        
        # Proportions du splitter
        splitter.setSizes([500, 400])
        layout.addWidget(splitter)
    
    def _create_header(self) -> QWidget:
        """Crée le header avec titre et actions."""
        header = QFrame()
        header.setObjectName("calendar-header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("📅 Calendrier Intelligent")
        title.setObjectName("calendar-title")
        title.setFont(QFont("Inter", 28, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Statistiques rapides
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setSpacing(25)
        
        self.today_events_label = QLabel("Aujourd'hui: 0")
        self.today_events_label.setObjectName("stat-label")
        stats_layout.addWidget(self.today_events_label)
        
        self.week_events_label = QLabel("Cette semaine: 0")
        self.week_events_label.setObjectName("stat-label")
        stats_layout.addWidget(self.week_events_label)
        
        layout.addWidget(stats_container)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        new_event_btn = QPushButton("➕ Nouvel événement")
        new_event_btn.setObjectName("primary-button")
        new_event_btn.setFixedHeight(45)
        new_event_btn.setMinimumWidth(160)
        new_event_btn.clicked.connect(self._create_new_event)
        actions_layout.addWidget(new_event_btn)
        
        sync_btn = QPushButton("🔄 Synchroniser")
        sync_btn.setObjectName("secondary-button")
        sync_btn.setFixedHeight(45)
        sync_btn.setMinimumWidth(140)
        sync_btn.clicked.connect(self.refresh_events)
        actions_layout.addWidget(sync_btn)
        
        layout.addLayout(actions_layout)
        
        return header
    
    def _create_calendar_section(self) -> QWidget:
        """Crée la section du calendrier."""
        section = QFrame()
        section.setObjectName("calendar-section")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Titre de section
        section_title = QLabel("📆 Vue mensuelle")
        section_title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #000000; margin-bottom: 10px;")
        layout.addWidget(section_title)
        
        # Widget calendrier moderne
        self.calendar_widget = ModernCalendarWidget()
        self.calendar_widget.setMinimumHeight(350)
        self.calendar_widget.clicked.connect(self._on_date_selected)
        layout.addWidget(self.calendar_widget)
        
        return section
    
    def _create_events_section(self) -> QWidget:
        """Crée la section de la liste des événements."""
        section = QFrame()
        section.setObjectName("events-section")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header de section avec filtres
        section_header = QHBoxLayout()
        section_header.setSpacing(15)
        
        section_title = QLabel("📋 Événements")
        section_title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #000000;")
        section_header.addWidget(section_title)
        
        section_header.addStretch()
        
        # Filtre par période
        self.period_filter = QComboBox()
        self.period_filter.addItems(["Aujourd'hui", "Cette semaine", "Ce mois", "Tous"])
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
        
        self.events_layout.addStretch()
        
        scroll_area.setWidget(self.events_container)
        layout.addWidget(scroll_area)
        
        return section
    
    def _setup_connections(self):
        """Configure les connexions de signaux."""
        pass
    
    def _apply_style(self):
        """Applique le style à la vue calendrier."""
        self.setStyleSheet("""
            #calendar-view {
                background-color: #ffffff;
            }
            
            #calendar-title {
                color: #000000;
            }
            
            #stat-label {
                color: #6c757d;
                font-size: 14px;
                font-weight: 500;
                background-color: #f8f9fa;
                padding: 8px 16px;
                border-radius: 20px;
                border: 1px solid #e9ecef;
            }
            
            #primary-button {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            
            #primary-button:hover {
                background-color: #0056b3;
            }
            
            #secondary-button {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            
            #secondary-button:hover {
                           background-color: #545b62;
           }
           
           #calendar-section, #events-section {
               background-color: #ffffff;
               border: 2px solid #e9ecef;
               border-radius: 15px;
           }
           
           QComboBox {
               background-color: #f8f9fa;
               border: 2px solid #dee2e6;
               border-radius: 8px;
               padding: 8px 12px;
               color: #495057;
               font-weight: 500;
               font-size: 14px;
           }
           
           QComboBox:focus {
               border-color: #007bff;
           }
           
           QComboBox::drop-down {
               border: none;
               width: 30px;
           }
           
           QComboBox::down-arrow {
               image: none;
               border-left: 5px solid transparent;
               border-right: 5px solid transparent;
               border-top: 6px solid #6c757d;
               margin-right: 8px;
           }
           
           QComboBox QAbstractItemView {
               background-color: #ffffff;
               border: 2px solid #dee2e6;
               border-radius: 8px;
               selection-background-color: #e3f2fd;
               selection-color: #000000;
               padding: 4px;
               outline: none;
           }
           
           QScrollArea {
               border: none;
               background-color: transparent;
           }
           
           QScrollBar:vertical {
               background-color: #f8f9fa;
               width: 12px;
               border-radius: 6px;
               margin: 2px;
           }
           
           QScrollBar::handle:vertical {
               background-color: #dee2e6;
               border-radius: 6px;
               min-height: 30px;
               margin: 2px;
           }
           
           QScrollBar::handle:vertical:hover {
               background-color: #adb5bd;
           }
           
           QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
               height: 0px;
           }
       """)
   
    def refresh_events(self):
       """Actualise la liste des événements."""
       try:
           # Récupérer les événements du manager
           self.current_events = self.calendar_manager.get_all_events()
           
           # Mettre à jour le calendrier
           self.calendar_widget.set_events(self.current_events)
           
           # Filtrer selon la sélection actuelle
           self._filter_events()
           
           # Mettre à jour les statistiques
           self._update_statistics()
           
           logger.info(f"{len(self.current_events)} événements chargés")
           
       except Exception as e:
           logger.error(f"Erreur lors du refresh des événements: {e}")
   
    def _filter_events(self):
       """Filtre les événements selon la période sélectionnée."""
       period = self.period_filter.currentText()
       now = datetime.now()
       
       if period == "Aujourd'hui":
           start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
           end_date = start_date + timedelta(days=1)
       elif period == "Cette semaine":
           days_since_monday = now.weekday()
           start_date = now - timedelta(days=days_since_monday)
           start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
           end_date = start_date + timedelta(days=7)
       elif period == "Ce mois":
           start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
           if now.month == 12:
               end_date = start_date.replace(year=now.year + 1, month=1)
           else:
               end_date = start_date.replace(month=now.month + 1)
       else:  # Tous
           self.filtered_events = self.current_events.copy()
           self._update_events_display()
           return
       
       # Filtrer les événements
       self.filtered_events = [
           event for event in self.current_events
           if event.start_time and start_date <= event.start_time < end_date
       ]
       
       self._update_events_display()
   
    def _update_events_display(self):
       """Met à jour l'affichage des événements."""
       # Vider la liste existante (sauf le message par défaut et le stretch)
       for i in reversed(range(self.events_layout.count())):
           item = self.events_layout.itemAt(i)
           if item and item.widget() and item.widget() != self.no_events_label:
               widget = item.widget()
               if not isinstance(widget, type(self.events_layout.itemAt(-1))):  # Pas le stretch
                   widget.setParent(None)
                   widget.deleteLater()
       
       if self.filtered_events:
           self.no_events_label.hide()
           
           # Trier par date
           sorted_events = sorted(
               self.filtered_events,
               key=lambda e: e.start_time if e.start_time else datetime.min
           )
           
           # Créer les cartes d'événements
           for i, event in enumerate(sorted_events):
               card = EventCard(event)
               card.clicked.connect(self._on_event_clicked)
               card.edit_requested.connect(self._edit_event)
               card.delete_requested.connect(self._delete_event)
               
               # Insérer avant le stretch (dernier élément)
               self.events_layout.insertWidget(self.events_layout.count() - 1, card)
       else:
           self.no_events_label.show()
   
    def _update_statistics(self):
       """Met à jour les statistiques affichées."""
       now = datetime.now()
       
       # Événements aujourd'hui
       today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
       today_end = today_start + timedelta(days=1)
       today_count = len([
           e for e in self.current_events
           if e.start_time and today_start <= e.start_time < today_end
       ])
       
       # Événements cette semaine
       days_since_monday = now.weekday()
       week_start = now - timedelta(days=days_since_monday)
       week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
       week_end = week_start + timedelta(days=7)
       week_count = len([
           e for e in self.current_events
           if e.start_time and week_start <= e.start_time < week_end
       ])
       
       self.today_events_label.setText(f"Aujourd'hui: {today_count}")
       self.week_events_label.setText(f"Cette semaine: {week_count}")
   
    def _on_date_selected(self, date: QDate):
       """Gère la sélection d'une date dans le calendrier."""
       # Filtrer les événements pour cette date
       selected_date = date.toPython()
       day_events = [
           event for event in self.current_events
           if event.start_time and event.start_time.date() == selected_date
       ]
       
       # Afficher les événements du jour sélectionné
       self.filtered_events = day_events
       self._update_events_display()
       
       # Changer temporairement le filtre pour refléter la sélection
       self.period_filter.blockSignals(True)
       self.period_filter.setCurrentText("Jour sélectionné")
       if self.period_filter.findText("Jour sélectionné") == -1:
           self.period_filter.addItem("Jour sélectionné")
       self.period_filter.blockSignals(False)
       
       logger.info(f"Date sélectionnée: {selected_date}, {len(day_events)} événement(s)")
   
    def _on_event_clicked(self, event: CalendarEvent):
       """Gère le clic sur un événement."""
       # Afficher les détails de l'événement
       details_text = f"""
Événement: {event.title}

📅 Date: {event.start_time.strftime('%d/%m/%Y') if event.start_time else 'Non définie'}
🕐 Heure: {event.start_time.strftime('%H:%M') if event.start_time else 'Non définie'}
⏱️ Durée: {getattr(event, 'duration', 'Non définie')} minutes
📍 Lieu: {getattr(event, 'location', 'Non défini') or 'Non défini'}
📝 Statut: {getattr(event, 'status', 'confirmed').title()}

Description:
{getattr(event, 'description', 'Aucune description') or 'Aucune description'}
       """.strip()
       
       from PyQt6.QtWidgets import QMessageBox
       msg = QMessageBox(self)
       msg.setWindowTitle("Détails de l'événement")
       msg.setText(details_text)
       msg.setIcon(QMessageBox.Icon.Information)
       msg.setStyleSheet("""
           QMessageBox {
               background-color: #ffffff;
               color: #000000;
               font-size: 14px;
           }
           QMessageBox QPushButton {
               background-color: #007bff;
               color: #ffffff;
               border: none;
               padding: 8px 16px;
               border-radius: 6px;
               min-width: 80px;
               font-weight: 500;
           }
           QMessageBox QPushButton:hover {
               background-color: #0056b3;
           }
       """)
       msg.exec()
       
       logger.info(f"Événement cliqué: {event.title}")
   
    def _create_new_event(self):
       """Crée un nouvel événement."""
       dialog = EventDialog(parent=self)
       if dialog.exec() == QDialog.DialogCode.Accepted:
           event_data = dialog.get_event_data()
           
           # Validation des données
           if not event_data['title'].strip():
               from PyQt6.QtWidgets import QMessageBox
               QMessageBox.warning(self, "Erreur", "Le titre de l'événement est obligatoire.")
               return
           
           try:
               # Créer l'événement via le manager
               new_event = self.calendar_manager.create_event(**event_data)
               
               # Actualiser l'affichage
               self.refresh_events()
               
               logger.info(f"Nouvel événement créé: {new_event.title}")
               
               # Message de confirmation
               from PyQt6.QtWidgets import QMessageBox
               msg = QMessageBox(self)
               msg.setWindowTitle("Succès")
               msg.setText(f"L'événement '{new_event.title}' a été créé avec succès.")
               msg.setIcon(QMessageBox.Icon.Information)
               msg.setStyleSheet("""
                   QMessageBox {
                       background-color: #ffffff;
                       color: #000000;
                   }
                   QMessageBox QPushButton {
                       background-color: #28a745;
                       color: white;
                       border: none;
                       padding: 8px 16px;
                       border-radius: 6px;
                       min-width: 80px;
                   }
               """)
               msg.exec()
               
           except Exception as e:
               logger.error(f"Erreur création événement: {e}")
               from PyQt6.QtWidgets import QMessageBox
               QMessageBox.critical(self, "Erreur", f"Impossible de créer l'événement:\n{str(e)}")
   
    def _edit_event(self, event: CalendarEvent):
       """Modifie un événement existant."""
       dialog = EventDialog(event, parent=self)
       if dialog.exec() == QDialog.DialogCode.Accepted:
           event_data = dialog.get_event_data()
           
           # Validation des données
           if not event_data['title'].strip():
               from PyQt6.QtWidgets import QMessageBox
               QMessageBox.warning(self, "Erreur", "Le titre de l'événement est obligatoire.")
               return
           
           try:
               # Mettre à jour l'événement
               updated_event = self.calendar_manager.update_event(event.id, **event_data)
               
               # Actualiser l'affichage
               self.refresh_events()
               
               logger.info(f"Événement modifié: {updated_event.title}")
               
               # Message de confirmation
               from PyQt6.QtWidgets import QMessageBox
               msg = QMessageBox(self)
               msg.setWindowTitle("Succès")
               msg.setText(f"L'événement '{updated_event.title}' a été modifié avec succès.")
               msg.setIcon(QMessageBox.Icon.Information)
               msg.setStyleSheet("""
                   QMessageBox {
                       background-color: #ffffff;
                       color: #000000;
                   }
                   QMessageBox QPushButton {
                       background-color: #007bff;
                       color: white;
                       border: none;
                       padding: 8px 16px;
                       border-radius: 6px;
                       min-width: 80px;
                   }
               """)
               msg.exec()
               
           except Exception as e:
               logger.error(f"Erreur modification événement: {e}")
               from PyQt6.QtWidgets import QMessageBox
               QMessageBox.critical(self, "Erreur", f"Impossible de modifier l'événement:\n{str(e)}")
   
    def _delete_event(self, event: CalendarEvent):
       """Supprime un événement."""
       # Demander confirmation
       from PyQt6.QtWidgets import QMessageBox
       reply = QMessageBox.question(
           self,
           "Confirmer la suppression",
           f"Êtes-vous sûr de vouloir supprimer l'événement '{event.title}' ?",
           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
           QMessageBox.StandardButton.No
       )
       
       if reply == QMessageBox.StandardButton.Yes:
           try:
               # Supprimer l'événement
               self.calendar_manager.delete_event(event.id)
               
               # Actualiser l'affichage
               self.refresh_events()
               
               logger.info(f"Événement supprimé: {event.title}")
               
               # Message de confirmation
               msg = QMessageBox(self)
               msg.setWindowTitle("Succès")
               msg.setText(f"L'événement '{event.title}' a été supprimé avec succès.")
               msg.setIcon(QMessageBox.Icon.Information)
               msg.setStyleSheet("""
                   QMessageBox {
                       background-color: #ffffff;
                       color: #000000;
                   }
                   QMessageBox QPushButton {
                       background-color: #dc3545;
                       color: white;
                       border: none;
                       padding: 8px 16px;
                       border-radius: 6px;
                       min-width: 80px;
                   }
               """)
               msg.exec()
               
           except Exception as e:
               logger.error(f"Erreur suppression événement: {e}")
               QMessageBox.critical(self, "Erreur", f"Impossible de supprimer l'événement:\n{str(e)}")