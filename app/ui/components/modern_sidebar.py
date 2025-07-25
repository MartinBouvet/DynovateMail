#!/usr/bin/env python3
"""
Sidebar moderne CORRIGÉE avec affichage propre et lisible.
"""
import logging
from typing import Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)

class StatCard(QFrame):
    """Carte de statistique CORRIGÉE."""
    
    def __init__(self, title: str, value: str = "0", icon: str = "📊"):
        super().__init__()
        self.setObjectName("stat-card")
        self.setFixedHeight(70)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Header avec icône
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 14))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("stat-title")
        title_label.setFont(QFont("Inter", 10, QFont.Weight.Medium))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Valeur
        self.value_label = QLabel(value)
        self.value_label.setObjectName("stat-value")
        self.value_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        layout.addWidget(self.value_label)
        
        self._apply_style()
    
    def update_value(self, value: str):
        """Met à jour la valeur."""
        self.value_label.setText(value)
    
    def _apply_style(self):
        """Applique le style CORRIGÉ."""
        self.setStyleSheet("""
            QFrame#stat-card {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                margin: 4px 0;
            }
            
            QFrame#stat-card:hover {
                background-color: #f0f0f0;
                border-color: #bdbdbd;
            }
            
            QLabel#stat-title {
                color: #757575;
                font-weight: 500;
            }
            
            QLabel#stat-value {
                color: #1a1a1a;
                font-weight: 700;
            }
        """)

class NavButton(QPushButton):
    """Bouton de navigation CORRIGÉ."""
    
    def __init__(self, text: str, icon: str, view_name: str):
        super().__init__()
        self.view_name = view_name
        self.is_active = False
        
        # Layout avec icône et texte
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)
        
        # Icône
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Arial", 16))
        layout.addWidget(self.icon_label)
        
        # Texte
        self.text_label = QLabel(text)
        self.text_label.setFont(QFont("Inter", 13, QFont.Weight.Medium))
        layout.addWidget(self.text_label)
        
        layout.addStretch()
        
        self.setFixedHeight(45)
        self._apply_style()
    
    def set_active(self, active: bool):
        """Active/désactive le bouton."""
        self.is_active = active
        self._apply_style()
    
    def _apply_style(self):
        """Applique le style CORRIGÉ selon l'état."""
        if self.is_active:
            style = """
                QPushButton {
                    background-color: #1976d2;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                }
                QLabel {
                    color: #ffffff;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                }
                QLabel {
                    color: #424242;
                }
                QLabel:hover {
                    color: #1976d2;
                }
            """
        
        self.setStyleSheet(style)

class ModernSidebar(QWidget):
    """Sidebar moderne CORRIGÉE avec navigation et statistiques."""
    
    view_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        
        self.nav_buttons = {}
        self.stat_cards = {}
        self.current_view = "inbox"
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface CORRIGÉE."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(0)
        
        # Logo et titre
        header = self._create_header()
        layout.addWidget(header)
        
        layout.addSpacing(30)
        
        # Navigation principale
        nav_section = self._create_navigation()
        layout.addWidget(nav_section)
        
        layout.addSpacing(30)
        
        # Statistiques
        stats_section = self._create_stats()
        layout.addWidget(stats_section)
        
        # Spacer pour pousser vers le bas
        layout.addStretch()
        
        # Informations utilisateur
        user_section = self._create_user_info()
        layout.addWidget(user_section)
    
    def _create_header(self) -> QWidget:
        """Crée le header CORRIGÉ."""
        header = QFrame()
        layout = QVBoxLayout(header)
        layout.setSpacing(6)
        
        # Logo
        logo = QLabel("⚡")
        logo.setFont(QFont("Arial", 28))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color: #1976d2;")
        layout.addWidget(logo)
        
        # Titre
        title = QLabel("Dynovate")
        title.setObjectName("app-title")
        title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Sous-titre
        subtitle = QLabel("Mail Assistant IA")
        subtitle.setObjectName("app-subtitle")
        subtitle.setFont(QFont("Inter", 11, QFont.Weight.Normal))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        return header
    
    def _create_navigation(self) -> QWidget:
        """Crée la section de navigation CORRIGÉE."""
        nav_frame = QFrame()
        nav_frame.setObjectName("nav-section")
        layout = QVBoxLayout(nav_frame)
        layout.setSpacing(6)
        
        # Titre de section
        section_title = QLabel("Navigation")
        section_title.setObjectName("section-title")
        section_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        layout.addWidget(section_title)
        
        layout.addSpacing(8)
        
        # Boutons de navigation
        nav_items = [
            ("Smart Inbox", "📧", "inbox"),
            ("Calendrier", "📅", "calendar"),
            ("Paramètres", "⚙️", "settings")
        ]
        
        for text, icon, view_name in nav_items:
            btn = NavButton(text, icon, view_name)
            btn.clicked.connect(lambda checked, vn=view_name: self._on_nav_clicked(vn))
            
            if view_name == self.current_view:
                btn.set_active(True)
            
            self.nav_buttons[view_name] = btn
            layout.addWidget(btn)
        
        return nav_frame
    
    def _create_stats(self) -> QWidget:
        """Crée la section des statistiques CORRIGÉE."""
        stats_frame = QFrame()
        stats_frame.setObjectName("stats-section")
        layout = QVBoxLayout(stats_frame)
        layout.setSpacing(6)
        
        # Titre de section
        section_title = QLabel("Statistiques")
        section_title.setObjectName("section-title")
        section_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        layout.addWidget(section_title)
        
        layout.addSpacing(8)
        
        # Cartes de statistiques
        stats_data = [
            ("Emails non lus", "0", "📬", "unread_emails"),
            ("IA Précision", "0%", "🤖", "ai_accuracy"),
            ("Réponses auto", "0", "⚡", "auto_responses")
        ]
        
        for title, value, icon, key in stats_data:
            card = StatCard(title, value, icon)
            self.stat_cards[key] = card
            layout.addWidget(card)
        
        return stats_frame
    
    def _create_user_info(self) -> QWidget:
        """Crée la section d'informations utilisateur CORRIGÉE."""
        user_frame = QFrame()
        user_frame.setObjectName("user-section")
        layout = QVBoxLayout(user_frame)
        layout.setSpacing(6)
        
        # Avatar
        avatar = QLabel("👤")
        avatar.setFont(QFont("Arial", 20))
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar)
        
        # Nom utilisateur
        username = QLabel("Utilisateur")
        username.setObjectName("username")
        username.setFont(QFont("Inter", 12, QFont.Weight.Medium))
        username.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(username)
        
        # Status
        status = QLabel("🟢 En ligne")
        status.setObjectName("user-status")
        status.setFont(QFont("Inter", 10))
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)
        
        return user_frame
    
    def _apply_style(self):
        """Applique le style CORRIGÉ à la sidebar."""
        self.setStyleSheet("""
            QWidget#sidebar {
                background-color: #ffffff;
                border-right: 2px solid #e0e0e0;
            }
            
            QLabel#app-title {
                color: #1a1a1a;
                font-weight: 700;
            }
            
            QLabel#app-subtitle {
                color: #757575;
                font-weight: 400;
            }
            
            QLabel#section-title {
                color: #1a1a1a;
                margin-bottom: 6px;
                font-weight: 600;
            }
            
            QLabel#username {
                color: #1a1a1a;
                font-weight: 500;
            }
            
            QLabel#user-status {
                color: #757575;
                font-weight: 400;
            }
        """)
    
    def _on_nav_clicked(self, view_name: str):
        """Gère le clic sur un bouton de navigation."""
        # Désactiver tous les boutons
        for btn in self.nav_buttons.values():
            btn.set_active(False)
        
        # Activer le bouton cliqué
        self.nav_buttons[view_name].set_active(True)
        
        self.current_view = view_name
        self.view_changed.emit(view_name)
    
    def update_stats(self, stats: Dict):
        """Met à jour les statistiques."""
        stat_mapping = {
            'unread_emails': str(stats.get('unread_emails', 0)),
            'ai_accuracy': f"{stats.get('ai_accuracy', 0) * 100:.0f}%",
            'auto_responses': str(stats.get('auto_responses', 0))
        }
        
        for key, value in stat_mapping.items():
            if key in self.stat_cards:
                self.stat_cards[key].update_value(value)