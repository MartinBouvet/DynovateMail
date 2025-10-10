#!/usr/bin/env python3
"""
Barre d'outils supérieure - AVEC LOGO
"""
import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

logger = logging.getLogger(__name__)

class TopToolbar(QWidget):
    """Barre d'outils supérieure."""
    
    view_requested = pyqtSignal(str)
    compose_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    search_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée la toolbar."""
        self.setFixedHeight(70)
        self.setObjectName("top-toolbar")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        # Logo + Titre
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(10)
        
        # Logo (si vous avez un fichier logo.png)
        logo_label = QLabel("📧")  # Remplacer par une image si disponible
        logo_label.setFont(QFont("Segoe UI", 24))
        logo_layout.addWidget(logo_label)
        
        title = QLabel("Dynovate Mail")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #5b21b6;")
        logo_layout.addWidget(title)
        layout.addLayout(logo_layout)
        layout.addSpacing(30)
        
        # Bouton Nouveau message - AGRANDI
        compose_btn = QPushButton("✉️ Nouveau message")
        compose_btn.setObjectName("compose-btn")
        compose_btn.clicked.connect(self.compose_requested.emit)
        compose_btn.setFixedHeight(45)
        compose_btn.setMinimumWidth(180)
        compose_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(compose_btn)
        
        layout.addStretch()
        
        # Barre de recherche - AGRANDIE
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher dans les emails...")
        self.search_input.setFixedWidth(350)
        self.search_input.setFixedHeight(45)
        self.search_input.setFont(QFont("Segoe UI", 13))
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        layout.addSpacing(20)
        
        # Boutons de navigation - AGRANDIS
        inbox_btn = QPushButton("📥 Emails")
        inbox_btn.clicked.connect(lambda: self.view_requested.emit("inbox"))
        inbox_btn.setFixedHeight(45)
        inbox_btn.setMinimumWidth(120)
        inbox_btn.setFont(QFont("Segoe UI", 13))
        layout.addWidget(inbox_btn)
        
        calendar_btn = QPushButton("📅 Calendrier")
        calendar_btn.clicked.connect(lambda: self.view_requested.emit("calendar"))
        calendar_btn.setFixedHeight(45)
        calendar_btn.setMinimumWidth(130)
        calendar_btn.setFont(QFont("Segoe UI", 13))
        layout.addWidget(calendar_btn)
        
        ai_btn = QPushButton("🤖 Assistant IA")
        ai_btn.clicked.connect(lambda: self.view_requested.emit("ai"))
        ai_btn.setFixedHeight(45)
        ai_btn.setMinimumWidth(140)
        ai_btn.setFont(QFont("Segoe UI", 13))
        layout.addWidget(ai_btn)
        
        # Bouton paramètres AGRANDI
        settings_btn = QPushButton("⚙️ Paramètres")
        settings_btn.clicked.connect(lambda: self.view_requested.emit("settings"))
        settings_btn.setFixedHeight(45)
        settings_btn.setMinimumWidth(130)
        settings_btn.setFont(QFont("Segoe UI", 13))
        layout.addWidget(settings_btn)
        
        self._apply_styles()
    
    def _on_search(self):
        """Recherche déclenchée."""
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)
            logger.info(f"Recherche: {query}")
    
    def _apply_styles(self):
        """Applique les styles Dynovate."""
        self.setStyleSheet("""
            #top-toolbar {
                background-color: #ffffff;
                border-bottom: 2px solid #5b21b6;
            }
            
            #compose-btn {
                background-color: #5b21b6;
                color: #ffffff;
                border: none;
                font-weight: bold;
                padding: 0px 20px;
                font-size: 14px;
                border-radius: 6px;
            }
            
            #compose-btn:hover {
                background-color: #4c1d95;
            }
            
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #5b21b6;
            }
            
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 13px;
                background-color: #ffffff;
                color: #000000;
            }
            
            QLineEdit:focus {
                border-color: #5b21b6;
            }
        """)