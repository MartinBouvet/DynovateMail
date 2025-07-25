#!/usr/bin/env python3
"""
Panel de suggestions IA avec réponses automatiques.
"""
import logging
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QCheckBox, QSlider, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

from models.email_model import Email

logger = logging.getLogger(__name__)

class ConfidenceBar(QWidget):
    """Barre de confiance visuelle."""
    
    def __init__(self, confidence: float):
        super().__init__()
        self.confidence = confidence
        self.setFixedHeight(8)
        self.setMinimumWidth(200)
    
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Arrière-plan
        painter.setBrush(QBrush(QColor("#e9ecef")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)
        
        # Barre de progression
        width = int(self.width() * self.confidence)
        if self.confidence >= 0.8:
            color = QColor("#28a745")
        elif self.confidence >= 0.6:
            color = QColor("#ffc107")
        else:
            color = QColor("#dc3545")
        
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(0, 0, width, self.height(), 4, 4)

class AISuggestionPanel(QWidget):
    """Panel de suggestions IA moderne."""
    
    response_approved = pyqtSignal(str, object)  # response_text, email
    response_rejected = pyqtSignal(object)  # email
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_email = None
        self.current_analysis = None
        
        self.setObjectName("ai-suggestion-panel")
        self.setFixedSize(450, 600)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self._apply_style()
        
        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
    
    def _setup_ui(self):
        """Configure l'interface."""
        # Container principal
        self.main_container = QFrame()
        self.main_container.setObjectName("main-container")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_container)
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)
        
        # Header
        header = self._create_header()
        container_layout.addWidget(header)
        
        # Analyse IA
        self.analysis_section = self._create_analysis_section()
        container_layout.addWidget(self.analysis_section)
        
        # Réponse suggérée
        self.response_section = self._create_response_section()
        container_layout.addWidget(self.response_section)
        
        # Footer avec boutons
        footer = self._create_footer()
        container_layout.addWidget(footer)
    
    def _create_header(self) -> QWidget:
        """Crée le header."""
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)
        
        # Titre
        icon_label = QLabel("🤖")
        icon_label.setFont(QFont("Arial", 20))
        layout.addWidget(icon_label)
        
        title_label = QLabel("Assistant IA")
        title_label.setObjectName("panel-title")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Bouton fermer
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close-btn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)
        
        return header
    
    def _create_analysis_section(self) -> QWidget:
        """Crée la section d'analyse."""
        section = QFrame()
        section.setObjectName("analysis-section")
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Titre
        title = QLabel("📊 Analyse IA")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Catégorie
        self.category_label = QLabel()
        self.category_label.setObjectName("category-label")
        self.category_label.setFont(QFont("Inter", 13))
        layout.addWidget(self.category_label)
        
        # Confiance
        confidence_layout = QHBoxLayout()
        confidence_text = QLabel("Confiance:")
        confidence_text.setFont(QFont("Inter", 12))
        confidence_layout.addWidget(confidence_text)
        
        self.confidence_bar = ConfidenceBar(0.0)
        confidence_layout.addWidget(self.confidence_bar)
        
        self.confidence_percent = QLabel("0%")
        self.confidence_percent.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        confidence_layout.addWidget(self.confidence_percent)
        
        layout.addLayout(confidence_layout)
        
        # Raisonnement
        reasoning_title = QLabel("🧠 Raisonnement:")
        reasoning_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        layout.addWidget(reasoning_title)
        
        self.reasoning_text = QLabel()
        self.reasoning_text.setObjectName("reasoning-text")
        self.reasoning_text.setFont(QFont("Inter", 11))
        self.reasoning_text.setWordWrap(True)
        self.reasoning_text.setMaximumHeight(80)
        layout.addWidget(self.reasoning_text)
        
        return section
    
    def _create_response_section(self) -> QWidget:
        """Crée la section de réponse."""
        section = QFrame()
        section.setObjectName("response-section")
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Titre
        title = QLabel("✉️ Réponse suggérée")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Zone de texte éditable
        self.response_editor = QTextEdit()
        self.response_editor.setObjectName("response-editor")
        self.response_editor.setFont(QFont("Inter", 12))
        self.response_editor.setMaximumHeight(200)
        self.response_editor.setPlaceholderText("Aucune réponse suggérée...")
        layout.addWidget(self.response_editor)
        
        # Délai d'envoi
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Délai d'envoi:")
        delay_label.setFont(QFont("Inter", 11))
        delay_layout.addWidget(delay_label)
        
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setRange(0, 60)
        self.delay_slider.setValue(5)
        self.delay_slider.valueChanged.connect(self._update_delay_label)
        delay_layout.addWidget(self.delay_slider)
        
        self.delay_value_label = QLabel("5 min")
        self.delay_value_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        delay_layout.addWidget(self.delay_value_label)
        
        layout.addLayout(delay_layout)
        
        return section
    
    def _create_footer(self) -> QWidget:
        """Crée le footer avec boutons."""
        footer = QFrame()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)
        
        # Bouton rejeter
        reject_btn = QPushButton("❌ Ignorer")
        reject_btn.setObjectName("reject-btn")
        reject_btn.clicked.connect(self._reject_suggestion)
        layout.addWidget(reject_btn)
        
        layout.addStretch()
        
        # Bouton approuver
        self.approve_btn = QPushButton("✅ Envoyer")
        self.approve_btn.setObjectName("approve-btn")
        self.approve_btn.clicked.connect(self._approve_suggestion)
        layout.addWidget(self.approve_btn)
        
        return footer
    
    def _apply_style(self):
        """Applique le style."""
        self.setStyleSheet("""
            #main-container {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 16px;
            }
            
            #panel-title {
                color: #000000;
            }
            
            #close-btn {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 15px;
                color: #6c757d;
                font-size: 14px;
                font-weight: bold;
            }
            
            #close-btn:hover {
                background-color: #e9ecef;
                color: #495057;
            }
            
            #analysis-section, #response-section {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 16px;
            }
            
            #section-title {
                color: #000000;
                margin-bottom: 8px;
            }
            
            #category-label {
                color: #007bff;
                font-weight: 600;
            }
            
            #reasoning-text {
                color: #495057;
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
            }
            
            #response-editor {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                color: #495057;
            }
            
            #approve-btn {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-width: 100px;
            }
            
            #approve-btn:hover {
                background-color: #1e7e34;
            }
            
            #reject-btn {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-width: 80px;
            }
            
            #reject-btn:hover {
                background-color: #545b62;
            }
            
            QSlider::groove:horizontal {
                background-color: #dee2e6;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background-color: #007bff;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
        """)
    
    def show_suggestion(self, email: Email, analysis):
        """Affiche le panel avec suggestions."""
        self.current_email = email
        self.current_analysis = analysis
        
        self._update_analysis_display(analysis)
        self._update_response_display(analysis)
        
        self.show()
        logger.info(f"Panel IA affiché pour email {email.id}")
    
    def _update_analysis_display(self, analysis):
        """Met à jour l'affichage de l'analyse."""
        category_names = {
            'cv': '📄 Candidature / CV',
            'rdv': '📅 Rendez-vous',
            'support': '🛠️ Support technique',
            'facture': '💰 Facture',
            'spam': '🚫 Spam',
            'general': '📧 Email général'
        }
        
        category_display = category_names.get(analysis.category, analysis.category)
        self.category_label.setText(f"Catégorie: {category_display}")
        
        # Confiance
        confidence_percent = int(analysis.confidence * 100)
        self.confidence_bar.confidence = analysis.confidence
        self.confidence_bar.update()
        self.confidence_percent.setText(f"{confidence_percent}%")
        
        # Raisonnement
        self.reasoning_text.setText(analysis.reasoning or "Analyse automatique basée sur le contenu.")
    
    def _update_response_display(self, analysis):
        """Met à jour l'affichage de la réponse."""
        if analysis.suggested_response and analysis.should_auto_respond:
            self.response_editor.setPlainText(analysis.suggested_response)
            self.response_editor.setEnabled(True)
            self.approve_btn.setEnabled(True)
        else:
            self.response_editor.setPlainText("Aucune réponse automatique suggérée pour ce type d'email.")
            self.response_editor.setEnabled(False)
            self.approve_btn.setEnabled(False)
    
    def _update_delay_label(self, value: int):
        """Met à jour le label du délai."""
        if value == 0:
            self.delay_value_label.setText("Immédiat")
        elif value == 1:
            self.delay_value_label.setText("1 min")
        else:
            self.delay_value_label.setText(f"{value} min")
    
    def _approve_suggestion(self):
        """Approuve et envoie la réponse."""
        if not self.current_email:
            return
        
        response_text = self.response_editor.toPlainText().strip()
        if not response_text:
            return
        
        self.response_approved.emit(response_text, self.current_email)
        self.hide()
        logger.info("Réponse IA approuvée")
    
    def _reject_suggestion(self):
        """Rejette la suggestion."""
        if self.current_email:
            self.response_rejected.emit(self.current_email)
        
        self.hide()
        logger.info("Suggestion IA rejetée")