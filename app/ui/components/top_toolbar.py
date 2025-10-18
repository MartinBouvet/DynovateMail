#!/usr/bin/env python3
"""
Barre d'outils supérieure - VERSION CORRIGÉE
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

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
        self.setFixedHeight(70)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e5e7eb;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 10, 25, 10)
        layout.setSpacing(15)
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Rechercher dans vos emails...")
        self.search_input.setFont(QFont("Arial", 13))
        self.search_input.setFixedWidth(500)
        self.search_input.setFixedHeight(42)
        self.search_input.returnPressed.connect(self._on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 21px;
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
        ]
        
        self.nav_buttons = {}
        
        for text, view_id in nav_buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 12))
            btn.setFixedHeight(42)
            btn.setFixedWidth(140)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=view_id: self._on_nav_clicked(v))
            layout.addWidget(btn)
            self.nav_buttons[view_id] = btn
        
        # Bouton composer
        compose_btn = QPushButton("✉️ Nouveau")
        compose_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        compose_btn.setFixedHeight(42)
        compose_btn.setFixedWidth(135)
        compose_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        compose_btn.clicked.connect(self.compose_requested.emit)
        compose_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 21px;
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
        refresh_btn.setFont(QFont("Arial", 16))
        refresh_btn.setFixedSize(42, 42)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 21px;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                color: white;
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
                    border: 1px solid transparent;
                    border-radius: 21px;
                }
                QPushButton:hover {
                    background-color: #f9fafb;
                    color: #000000;
                }
                QPushButton:checked {
                    background-color: #ede9fe;
                    color: #5b21b6;
                    border-color: #5b21b6;
                    font-weight: bold;
                }
            """)