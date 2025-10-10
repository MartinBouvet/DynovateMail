#!/usr/bin/env python3
"""
Sidebar avec dossiers et catégories - CORRIGÉE
"""
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class EmailFoldersSidebar(QWidget):
    """Sidebar avec dossiers et catégories."""
    
    folder_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_folder = "INBOX"
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée la sidebar."""
        self.setObjectName("folders-sidebar")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(2)
        
        # Titre Dossiers
        title = QLabel("DOSSIERS")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setContentsMargins(15, 10, 15, 10)
        title.setStyleSheet("color: #5b21b6;")
        layout.addWidget(title)
        
        # Dossiers principaux
        folders = [
            ("INBOX", "📥 Boîte de réception"),
            ("SENT", "📤 Envoyés"),
            ("DRAFTS", "📝 Brouillons"),
            ("ARCHIVED", "📦 Archives"),
            ("TRASH", "🗑️ Corbeille"),
            ("SPAM", "⚠️ Spam")
        ]
        
        self.folder_buttons = {}
        
        for folder_id, folder_name in folders:
            btn = QPushButton(folder_name)
            btn.setObjectName(f"folder-{folder_id}")
            btn.setFixedHeight(45)
            btn.setFont(QFont("Segoe UI", 12))
            btn.clicked.connect(lambda checked, f=folder_id: self._on_folder_clicked(f))
            layout.addWidget(btn)
            self.folder_buttons[folder_id] = btn
        
        layout.addStretch()
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #5b21b6; max-height: 2px;")
        layout.addWidget(separator)
        
        # Section TRI (au lieu de Catégories IA)
        tri_label = QLabel("TRI PAR CATÉGORIE")
        tri_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        tri_label.setContentsMargins(15, 10, 15, 10)
        tri_label.setStyleSheet("color: #5b21b6;")
        layout.addWidget(tri_label)
        
        # Boutons de tri par catégorie
        categories = [
            ("cv", "📄 CV"),
            ("meeting", "📅 Rendez-vous"),
            ("invoice", "💰 Factures"),
            ("newsletter", "📰 Newsletters"),
            ("support", "🛠️ Support"),
            ("spam", "⚠️ Spam")
        ]
        
        for cat_id, cat_name in categories:
            btn = QPushButton(cat_name)
            btn.setFixedHeight(40)
            btn.setFont(QFont("Segoe UI", 11))
            btn.clicked.connect(lambda checked, c=cat_id: self._on_category_clicked(c))
            layout.addWidget(btn)
        
        self._apply_styles()
        self._update_active_folder("INBOX")
    
    def _on_folder_clicked(self, folder_id: str):
        """Dossier cliqué."""
        if folder_id != self.current_folder:
            self.current_folder = folder_id
            self._update_active_folder(folder_id)
            self.folder_changed.emit(folder_id)
            logger.info(f"Dossier sélectionné: {folder_id}")
    
    def _on_category_clicked(self, category: str):
        """Catégorie cliquée."""
        self.folder_changed.emit(f"CATEGORY:{category}")
        logger.info(f"Tri par catégorie: {category}")
    
    def _update_active_folder(self, folder_id: str):
        """Met à jour l'apparence du dossier actif."""
        for fid, btn in self.folder_buttons.items():
            if fid == folder_id:
                btn.setStyleSheet("""
                    background-color: #5b21b6; 
                    color: #ffffff;
                    border-left: 4px solid #000000; 
                    font-weight: bold;
                """)
            else:
                btn.setStyleSheet("")
    
    def _apply_styles(self):
        """Applique les styles Dynovate."""
        self.setStyleSheet("""
            #folders-sidebar {
                background-color: #f5f5f5;
                border-right: 2px solid #5b21b6;
            }
            
            QPushButton {
                text-align: left;
                padding-left: 15px;
                border: none;
                border-radius: 0px;
                background-color: transparent;
                color: #000000;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background-color: #e0e0e0;
                border-left: 4px solid #5b21b6;
            }
            
            QPushButton:pressed {
                background-color: #5b21b6;
                color: #ffffff;
            }
        """)