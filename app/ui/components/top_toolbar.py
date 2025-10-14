#!/usr/bin/env python3
"""
Barre d'outils supérieure - OPTIMISÉE
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class TopToolbar(QWidget):
    """Barre d'outils supérieure."""
    
    view_requested = pyqtSignal(str)
    compose_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    search_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_view = "inbox"
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface."""
        self.setFixedHeight(75)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 3px solid #5b21b6;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 12, 25, 12)
        layout.setSpacing(20)
        
        # Logo + Titre
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(15)
        
        logo = QLabel("📧")
        logo.setFont(QFont("Arial", 32))
        logo_layout.addWidget(logo)
        
        title = QLabel("Dynovate Mail")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #5b21b6;")
        logo_layout.addWidget(title)
        
        layout.addLayout(logo_layout)
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher...")
        self.search_input.setFont(QFont("Arial", 13))
        self.search_input.setFixedWidth(450)
        self.search_input.setFixedHeight(45)
        self.search_input.returnPressed.connect(self._on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f3f4f6;
                border: 2px solid #e5e7eb;
                border-radius: 22px;
                padding: 0 20px;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #5b21b6;
                background-color: #ffffff;
            }
        """)
        layout.addWidget(self.search_input)
        
        layout.addStretch()
        
        # Boutons de navigation
        nav_buttons = [
            ("📥 Inbox", "inbox"),
            ("📅 Calendrier", "calendar"),
            ("🤖 Assistant IA", "ai"),
            ("⚙️ Paramètres", "settings")
        ]
        
        self.nav_buttons = {}
        
        for text, view_id in nav_buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 12, QFont.Bold))
            btn.setFixedHeight(45)
            btn.setFixedWidth(155)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=view_id: self._on_nav_clicked(v))
            layout.addWidget(btn)
            self.nav_buttons[view_id] = btn
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFixedWidth(2)
        separator.setFixedHeight(45)
        separator.setStyleSheet("background-color: #e5e7eb;")
        layout.addWidget(separator)
        
        # Bouton composer
        compose_btn = QPushButton("✉️ Nouveau")
        compose_btn.setFont(QFont("Arial", 13, QFont.Bold))
        compose_btn.setFixedHeight(45)
        compose_btn.setFixedWidth(145)
        compose_btn.setCursor(Qt.PointingHandCursor)
        compose_btn.clicked.connect(self.compose_requested.emit)
        compose_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
        """)
        layout.addWidget(compose_btn)
        
        # Bouton rafraîchir
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFont(QFont("Arial", 18))
        refresh_btn.setFixedSize(45, 45)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 2px solid #e5e7eb;
                border-radius: 22px;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                border-color: #5b21b6;
            }
        """)
        layout.addWidget(refresh_btn)
        
        # Activer inbox par défaut
        self._update_active_view("inbox")
        self._apply_nav_styles()
    
    def _on_nav_clicked(self, view_id: str):
        """Navigation."""
        if view_id != self.current_view:
            self.current_view = view_id
            self._update_active_view(view_id)
            self.view_requested.emit(view_id)
    
    def _update_active_view(self, view_id: str):
        """Met à jour vue active."""
        for vid, btn in self.nav_buttons.items():
            btn.setChecked(vid == view_id)
    
    def _on_search(self):
        """Recherche."""
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)
            logger.info(f"Recherche: {query}")
    
    def _apply_nav_styles(self):
        """Styles navigation."""
        for btn in self.nav_buttons.values():
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #6b7280;
                    border: 2px solid transparent;
                    border-radius: 22px;
                }
                QPushButton:hover {
                    background-color: #f3f4f6;
                    color: #000000;
                }
                QPushButton:checked {
                    background-color: #ede9fe;
                    color: #5b21b6;
                    border-color: #5b21b6;
                }
            """)