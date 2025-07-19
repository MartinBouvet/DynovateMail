#!/usr/bin/env python3
"""
Carte d'email intelligente avec informations IA et actions rapides.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QCheckBox, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush
import logging
from typing import Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette

from models.email_model import Email
from ai.smart_classifier import EmailAnalysis

logger = logging.getLogger(__name__)

class ConfidenceBar(QWidget):
    """Barre de confiance visuelle pour l'IA."""
    
    def __init__(self, confidence: float):
        super().__init__()
        self.confidence = confidence
        self.setFixedHeight(8)
        self.setMinimumWidth(200)
    
    def paintEvent(self, event):
        """Dessine la barre de confiance."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Arrière-plan
        painter.setBrush(QBrush(QColor("#e9ecef")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)
        
        # Barre de progression
        width = int(self.width() * self.confidence)
        if self.confidence >= 0.8:
            color = QColor("#28a745")  # Vert
        elif self.confidence >= 0.6:
            color = QColor("#ffc107")  # Jaune
        else:
            color = QColor("#dc3545")  # Rouge
        
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(0, 0, width, self.height(), 4, 4)

class ActionButton(QPushButton):
    """Bouton d'action avec icône et style moderne."""
    
    def __init__(self, text: str, icon: str, button_type: str = "secondary"):
        super().__init__(f"{icon} {text}")
        self.button_type = button_type
        self.setFixedHeight(40)
        self.setFont(QFont("Inter", 13, QFont.Weight.Medium))
        self._apply_style()
    
    def _apply_style(self):
        """Applique le style selon le type."""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 8px 20px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 8px 20px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #1e7e34;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 8px 20px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #545b62;
                }
            """,
            "outline": """
                QPushButton {
                    background-color: transparent;
                    color: #007bff;
                    border: 2px solid #007bff;
                    border-radius: 20px;
                    padding: 8px 20px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #007bff;
                    color: white;
                }
            """
        }
        
        self.setStyleSheet(styles.get(self.button_type, styles["secondary"]))

class AISuggestionPanel(QWidget):
    """Panel flottant de suggestions IA avec interface moderne."""
    
    response_approved = pyqtSignal(str, object)  # response_text, email
    response_rejected = pyqtSignal(object)  # email
    action_requested = pyqtSignal(str, object)  # action_type, email
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_email = None
        self.current_analysis = None
        self.is_visible = False
        
        self.setObjectName("ai-suggestion-panel")
        self.setFixedSize(450, 600)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self._apply_style()
        self._setup_animations()
        
        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
    
    def _setup_ui(self):
        """Configure l'interface du panel."""
        # Container principal avec bordures arrondies
        self.main_container = QFrame()
        self.main_container.setObjectName("main-container")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_container)
        
        # Layout du container
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)
        
        # Header
        header = self._create_header()
        container_layout.addWidget(header)
        
        # Zone de scroll pour le contenu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(16)
        
        # Sections du contenu
        self.analysis_section = self._create_analysis_section()
        self.content_layout.addWidget(self.analysis_section)
        
        self.response_section = self._create_response_section()
        self.content_layout.addWidget(self.response_section)
        
        self.actions_section = self._create_actions_section()
        self.content_layout.addWidget(self.actions_section)
        
        self.content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        container_layout.addWidget(scroll_area)
        
        # Footer avec boutons principaux
        footer = self._create_footer()
        container_layout.addWidget(footer)
    
    def _create_header(self) -> QWidget:
        """Crée le header du panel."""
        header = QFrame()
        header.setObjectName("panel-header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)
        
        # Titre avec icône
        title_layout = QHBoxLayout()
        
        icon_label = QLabel("🤖")
        icon_label.setFont(QFont("Arial", 20))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("Assistant IA")
        title_label.setObjectName("panel-title")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Bouton fermer
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close-btn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)
        
        return header
    
    def _create_analysis_section(self) -> QWidget:
        """Crée la section d'analyse IA."""
        section = QFrame()
        section.setObjectName("analysis-section")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Titre de section
        title = QLabel("📊 Analyse IA")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Catégorie détectée
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
        
        # Priorité
        self.priority_label = QLabel()
        self.priority_label.setObjectName("priority-label")
        self.priority_label.setFont(QFont("Inter", 12))
        layout.addWidget(self.priority_label)
        
        # Raisonnement IA
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
        """Crée la section de réponse suggérée."""
        section = QFrame()
        section.setObjectName("response-section")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Titre avec checkbox
        header_layout = QHBoxLayout()
        
        title = QLabel("✉️ Réponse suggérée")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.auto_send_checkbox = QCheckBox("Envoi automatique")
        self.auto_send_checkbox.setFont(QFont("Inter", 11))
        header_layout.addWidget(self.auto_send_checkbox)
        
        layout.addLayout(header_layout)
        
        # Zone de texte éditable
        self.response_editor = QTextEdit()
        self.response_editor.setObjectName("response-editor")
        self.response_editor.setFont(QFont("Inter", 12))
        self.response_editor.setMaximumHeight(150)
        self.response_editor.setPlaceholderText("Aucune réponse suggérée...")
        layout.addWidget(self.response_editor)
        
        # Slider pour le délai d'envoi
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Délai d'envoi:")
        delay_label.setFont(QFont("Inter", 11))
        delay_layout.addWidget(delay_label)
        
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setRange(0, 60)  # 0 à 60 minutes
        self.delay_slider.setValue(5)  # 5 minutes par défaut
        self.delay_slider.valueChanged.connect(self._update_delay_label)
        delay_layout.addWidget(self.delay_slider)
        
        self.delay_value_label = QLabel("5 min")
        self.delay_value_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        delay_layout.addWidget(self.delay_value_label)
        
        layout.addLayout(delay_layout)
        
        return section
    
    def _create_actions_section(self) -> QWidget:
        """Crée la section d'actions rapides."""
        section = QFrame()
        section.setObjectName("actions-section")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Titre
        title = QLabel("⚡ Actions rapides")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Container pour les boutons d'actions
        self.actions_container = QWidget()
        self.actions_layout = QVBoxLayout(self.actions_container)
        self.actions_layout.setSpacing(8)
        layout.addWidget(self.actions_container)
        
        return section
    
    def _create_footer(self) -> QWidget:
        """Crée le footer avec boutons principaux."""
        footer = QFrame()
        footer.setObjectName("panel-footer")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)
        
        # Bouton rejeter
        reject_btn = ActionButton("Ignorer", "❌", "outline")
        reject_btn.clicked.connect(self._reject_suggestion)
        layout.addWidget(reject_btn)
        
        layout.addStretch()
        
        # Bouton approuver
        self.approve_btn = ActionButton("Envoyer réponse", "✅", "success")
        self.approve_btn.clicked.connect(self._approve_suggestion)
        layout.addWidget(self.approve_btn)
        
        return footer
    
    def _setup_animations(self):
        """Configure les animations."""
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
    
    def _apply_style(self):
        """Applique le style au panel."""
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
            
            #analysis-section, #response-section, #actions-section {
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
            
            #priority-label {
                color: #6c757d;
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
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #dee2e6;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QCheckBox {
                color: #495057;
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
    
    def show_suggestion(self, email: Email, analysis: EmailAnalysis):
        """Affiche le panel avec les suggestions pour un email."""
        self.current_email = email
        self.current_analysis = analysis
        
        # Mettre à jour l'analyse
        self._update_analysis_display(analysis)
        
        # Mettre à jour la réponse suggérée
        self._update_response_display(analysis)
        
        # Mettre à jour les actions rapides
        self._update_actions_display(analysis)
        
        # Positionner le panel
        self._position_panel()
        
        # Afficher avec animation
        self._animate_show()
        
        logger.info(f"Panel IA affiché pour email {email.id}")
    
    def _update_analysis_display(self, analysis: EmailAnalysis):
        """Met à jour l'affichage de l'analyse."""
        # Catégorie
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
        
        # Priorité
        priority_names = {
            1: "🔴 Très urgent",
            2: "🟠 Urgent", 
            3: "🟡 Normal",
            4: "🟢 Faible",
            5: "⚪ Très faible"
        }
        
        priority_display = priority_names.get(analysis.priority, f"Priorité {analysis.priority}")
        self.priority_label.setText(f"Priorité: {priority_display}")
        
        # Raisonnement
        self.reasoning_text.setText(analysis.reasoning or "Analyse automatique basée sur le contenu de l'email.")
    
    def _update_response_display(self, analysis: EmailAnalysis):
        """Met à jour l'affichage de la réponse."""
        if analysis.suggested_response and analysis.should_auto_respond:
            self.response_editor.setPlainText(analysis.suggested_response)
            self.response_editor.setEnabled(True)
            self.approve_btn.setEnabled(True)
            self.auto_send_checkbox.setEnabled(True)
        else:
            self.response_editor.setPlainText("Aucune réponse automatique suggérée pour ce type d'email.")
            self.response_editor.setEnabled(False)
            self.approve_btn.setEnabled(False)
            self.auto_send_checkbox.setEnabled(False)
    
    def _update_actions_display(self, analysis: EmailAnalysis):
        """Met à jour les actions rapides disponibles."""
        # Vider les actions existantes
        for i in reversed(range(self.actions_layout.count())):
            child = self.actions_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Actions selon la catégorie
        actions = []
        
        if analysis.category == 'cv':
            actions = [
                ("📁 Archiver CV", "archive_cv"),
                ("👥 Ajouter au CRM", "add_to_crm"),
                ("📧 Programmer rappel", "schedule_reminder")
            ]
        elif analysis.category == 'rdv':
            actions = [
                ("📅 Ajouter au calendrier", "add_to_calendar"),
                ("🔄 Proposer créneaux", "suggest_slots"),
                ("📧 Confirmer RDV", "confirm_meeting")
            ]
        elif analysis.category == 'support':
            actions = [
                ("🎫 Créer ticket", "create_ticket"),
                ("📞 Programmer appel", "schedule_call"),
                ("📚 Envoyer FAQ", "send_faq")
            ]
        elif analysis.category == 'facture':
            actions = [
                ("💳 Marquer payé", "mark_paid"),
                ("📊 Ajouter comptabilité", "add_accounting"),
                ("⏰ Programmer rappel", "payment_reminder")
            ]
        
        # Actions communes
        actions.extend([
            ("🏷️ Ajouter étiquette", "add_label"),
            ("📋 Copier dans presse-papier", "copy_content")
        ])
        
        # Créer les boutons d'actions
        for action_text, action_type in actions:
            btn = ActionButton(action_text, "", "outline")
            btn.clicked.connect(lambda checked, at=action_type: self.action_requested.emit(at, self.current_email))
            self.actions_layout.addWidget(btn)
    
    def _position_panel(self):
        """Positionne le panel sur l'écran."""
        if self.parent():
            parent_rect = self.parent().geometry()
            # Positionner à droite de la fenêtre parent
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 100
        else:
            # Position par défaut
            x = 100
            y = 100
        
        self.move(x, y)
    
    def _animate_show(self):
        """Anime l'apparition du panel."""
        # Position de départ (hors écran à droite)
        start_rect = self.geometry()
        start_rect.moveLeft(start_rect.left() + 300)
        
        # Position finale
        end_rect = self.geometry()
        
        self.setGeometry(start_rect)
        self.show()
        
        # Animation de glissement
        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(end_rect)
        self.slide_animation.start()
        
        # Animation de fade-in
        self.setWindowOpacity(0.0)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        self.is_visible = True
    
    def _animate_hide(self):
        """Anime la disparition du panel."""
        # Animation de fade-out
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
        
        self.is_visible = False
    
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
        
        # Émettre le signal avec la réponse modifiée
        self.response_approved.emit(response_text, self.current_email)
        
        # Fermer le panel
        self._animate_hide()
        
        logger.info("Réponse IA approuvée et envoyée")
    
    def _reject_suggestion(self):
        """Rejette la suggestion."""
        if self.current_email:
            self.response_rejected.emit(self.current_email)
        
        self._animate_hide()
        logger.info("Suggestion IA rejetée")
    
    def hide(self):
        """Cache le panel."""
        super().hide()
        self.is_visible = False
    
    def keyPressEvent(self, event):
        """Gère les touches clavier."""
        if event.key() == Qt.Key.Key_Escape:
            self._animate_hide()
        super().keyPressEvent(event)