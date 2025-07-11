"""
Vue pour gérer les réponses automatiques en attente de validation - VERSION CORRIGÉE.
"""
import logging
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QTextEdit, QScrollArea, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QDialog, QDialogButtonBox,
    QGroupBox, QFormLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

from models.pending_response_model import PendingResponse, ResponseStatus
from pending_response_manager import PendingResponseManager
from auto_responder import AutoResponder

logger = logging.getLogger(__name__)

class ResponsePreviewDialog(QDialog):
    """Dialogue pour prévisualiser et modifier une réponse."""
    
    def __init__(self, response: PendingResponse, parent=None):
        super().__init__(parent)
        self.response = response
        self.modified_content = None
        
        self.setWindowTitle("Prévisualisation de la réponse")
        self.setModal(True)
        self.resize(800, 700)
        self.setMinimumSize(600, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface du dialogue."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title_label = QLabel("📧 Prévisualisation de la réponse automatique")
        title_label.setObjectName("dialog-title")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Scroll area pour le contenu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Informations sur l'email original
        original_group = QGroupBox("📨 Email original")
        original_group.setObjectName("info-group")
        original_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        original_layout = QFormLayout(original_group)
        original_layout.setSpacing(8)
        
        sender_label = QLabel(f"{self.response.original_sender}")
        sender_label.setWordWrap(True)
        original_layout.addRow("De:", sender_label)
        
        email_label = QLabel(f"{self.response.original_sender_email}")
        email_label.setWordWrap(True)
        original_layout.addRow("Email:", email_label)
        
        subject_label = QLabel(self.response.original_subject)
        subject_label.setWordWrap(True)
        original_layout.addRow("Sujet:", subject_label)
        
        category_label = QLabel(self.response.category.upper())
        category_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self._get_category_color(self.response.category)};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)
        original_layout.addRow("Catégorie:", category_label)
        
        # Aperçu du contenu original
        original_preview = QTextEdit()
        original_preview.setPlainText(self.response.original_body)
        original_preview.setReadOnly(True)
        original_preview.setMaximumHeight(120)
        original_preview.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        original_layout.addRow("Contenu:", original_preview)
        
        content_layout.addWidget(original_group)
        
        # Analyse IA
        ai_group = QGroupBox("🤖 Analyse IA")
        ai_group.setObjectName("info-group")
        ai_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        ai_layout = QFormLayout(ai_group)
        ai_layout.setSpacing(8)
        
        reason_label = QLabel(self.response.reason)
        reason_label.setWordWrap(True)
        ai_layout.addRow("Raison:", reason_label)
        
        confidence_label = QLabel(f"{self.response.confidence_score:.1%}")
        confidence_label.setStyleSheet("font-weight: bold; color: #4caf50;")
        ai_layout.addRow("Confiance:", confidence_label)
        
        content_layout.addWidget(ai_group)
        
        # Réponse proposée (modifiable)
        response_group = QGroupBox("✏️ Réponse proposée (modifiable)")
        response_group.setObjectName("info-group")
        response_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        response_layout = QVBoxLayout(response_group)
        
        self.response_text = QTextEdit()
        self.response_text.setObjectName("response-editor")
        self.response_text.setPlainText(self.response.proposed_response)
        self.response_text.setMinimumHeight(200)
        response_layout.addWidget(self.response_text)
        
        content_layout.addWidget(response_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        # Bouton rejeter
        reject_btn = QPushButton("❌ Rejeter")
        reject_btn.setObjectName("reject-button")
        reject_btn.clicked.connect(self.reject)
        reject_btn.setMinimumHeight(40)
        reject_btn.setMinimumWidth(120)
        buttons_layout.addWidget(reject_btn)
        
        buttons_layout.addStretch()
        
        # Bouton approuver
        approve_btn = QPushButton("✅ Approuver et envoyer")
        approve_btn.setObjectName("approve-button")
        approve_btn.clicked.connect(self.approve)
        approve_btn.setDefault(True)
        approve_btn.setMinimumHeight(40)
        approve_btn.setMinimumWidth(180)
        buttons_layout.addWidget(approve_btn)
        
        layout.addLayout(buttons_layout)
        
        self._apply_style()
    
    def _get_category_color(self, category: str) -> str:
        """Retourne la couleur associée à une catégorie."""
        colors = {
            'cv': '#9c27b0',
            'rdv': '#2196f3',
            'spam': '#f44336',
            'facture': '#ff9800',
            'support': '#4caf50',
            'partenariat': '#3f51b5',
            'newsletter': '#795548',
            'important': '#e91e63',
            'general': '#607d8b'
        }
        return colors.get(category, '#607d8b')
    
    def approve(self):
        """Approuve la réponse."""
        # Vérifier si le contenu a été modifié
        current_content = self.response_text.toPlainText().strip()
        if current_content != self.response.proposed_response:
            self.modified_content = current_content
        
        self.accept()
    
    def get_modified_content(self) -> Optional[str]:
        """Retourne le contenu modifié ou None."""
        return self.modified_content
    
    def _apply_style(self):
        """Applique le style au dialogue."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            
            QLabel#dialog-title {
                color: #000000;
                margin-bottom: 15px;
                padding: 10px;
                background-color: #f0f8ff;
                border-radius: 8px;
            }
            
            QGroupBox#info-group {
                font-size: 13px;
                font-weight: bold;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #fafafa;
            }
            
            QGroupBox#info-group::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #ffffff;
                border-radius: 5px;
            }
            
            QTextEdit#response-editor {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: Arial, sans-serif;
                line-height: 1.5;
            }
            
            QTextEdit#response-editor:focus {
                border-color: #2196f3;
            }
            
            QPushButton#approve-button {
                background-color: #4caf50;
                color: #ffffff;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton#approve-button:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            
            QPushButton#approve-button:pressed {
                background-color: #3d8b40;
            }
            
            QPushButton#reject-button {
                background-color: #f44336;
                color: #ffffff;
                border: 2px solid #f44336;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton#reject-button:hover {
                background-color: #da190b;
                border-color: #da190b;
            }
            
            QPushButton#reject-button:pressed {
                background-color: #c41e3a;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #cccccc;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #999999;
            }
        """)

class PendingResponseItem(QFrame):
    """Widget pour afficher une réponse en attente dans la liste."""
    
    clicked = pyqtSignal(object)
    approved = pyqtSignal(object)
    rejected = pyqtSignal(object)
    
    def __init__(self, response: PendingResponse, parent=None):
        super().__init__(parent)
        self.response = response
        self.selected = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface du widget."""
        self.setObjectName("response-item")
        self.setMinimumHeight(140)
        self.setMaximumHeight(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Ligne 1: Expéditeur et catégorie
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Expéditeur
        sender_label = QLabel(f"De: {self.response.original_sender}")
        sender_label.setObjectName("sender-label")
        sender_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        sender_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_layout.addWidget(sender_label, 1)
        
        # Badge catégorie
        category_badge = QLabel(self.response.category.upper())
        category_badge.setObjectName("category-badge")
        category_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        category_badge.setFixedHeight(25)
        category_badge.setMinimumWidth(80)
        category_badge.setStyleSheet(f"""
            QLabel#category-badge {{
                background-color: {self._get_category_color(self.response.category)};
                color: white;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(category_badge, 0)
        
        layout.addLayout(header_layout)
        
        # Ligne 2: Sujet
        subject_label = QLabel(f"Sujet: {self.response.original_subject}")
        subject_label.setObjectName("subject-label")
        subject_label.setFont(QFont("Arial", 11))
        subject_label.setWordWrap(True)
        subject_label.setMaximumHeight(40)
        layout.addWidget(subject_label)
        
        # Ligne 3: Aperçu réponse
        preview = self.response.proposed_response[:80] + "..." if len(self.response.proposed_response) > 80 else self.response.proposed_response
        preview_label = QLabel(f"Réponse: {preview}")
        preview_label.setObjectName("preview-label")
        preview_label.setFont(QFont("Arial", 10))
        preview_label.setWordWrap(True)
        preview_label.setMaximumHeight(35)
        layout.addWidget(preview_label)
        
        # Ligne 4: Score et actions
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        
        # Score de confiance
        confidence_label = QLabel(f"🎯 {self.response.confidence_score:.0%}")
        confidence_label.setObjectName("confidence-label")
        confidence_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        footer_layout.addWidget(confidence_label)
        
        footer_layout.addStretch()
        
        # Actions rapides
        approve_btn = QPushButton("✅ Approuver")
        approve_btn.setObjectName("quick-approve")
        approve_btn.setFixedSize(85, 28)
        approve_btn.setToolTip("Approuver et envoyer")
        approve_btn.clicked.connect(lambda: self.approved.emit(self.response))
        footer_layout.addWidget(approve_btn)
        
        reject_btn = QPushButton("❌ Rejeter")
        reject_btn.setObjectName("quick-reject")
        reject_btn.setFixedSize(75, 28)
        reject_btn.setToolTip("Rejeter")
        reject_btn.clicked.connect(lambda: self.rejected.emit(self.response))
        footer_layout.addWidget(reject_btn)
        
        layout.addLayout(footer_layout)
        
        # Appliquer le style
        self._apply_style()
    
    def _get_category_color(self, category: str) -> str:
        """Retourne la couleur associée à une catégorie."""
        colors = {
            'cv': '#9c27b0',
            'rdv': '#2196f3',
            'spam': '#f44336',
            'facture': '#ff9800',
            'support': '#4caf50',
            'partenariat': '#3f51b5',
            'newsletter': '#795548',
            'important': '#e91e63',
            'general': '#607d8b'
        }
        return colors.get(category, '#607d8b')
    
    def _apply_style(self):
        """Applique le style au widget."""
        base_style = """
            QFrame#response-item {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin: 3px;
                border-left: 5px solid #2196f3;
            }
            
            QFrame#response-item:hover {
                background-color: #f8f9ff;
                border-color: #2196f3;
                border-left-color: #1976d2;
            }
            
            QLabel#sender-label {
                color: #000000;
            }
            
            QLabel#subject-label {
                color: #333333;
            }
            
            QLabel#preview-label {
                color: #666666;
                font-style: italic;
            }
            
            QLabel#confidence-label {
                color: #4caf50;
            }
            
            QPushButton#quick-approve {
                background-color: #4caf50;
                color: white;
                border: 1px solid #4caf50;
                border-radius: 14px;
                font-size: 10px;
                font-weight: bold;
            }
            
            QPushButton#quick-approve:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            
            QPushButton#quick-reject {
                background-color: #f44336;
                color: white;
                border: 1px solid #f44336;
                border-radius: 14px;
                font-size: 10px;
                font-weight: bold;
            }
            
            QPushButton#quick-reject:hover {
                background-color: #da190b;
                border-color: #da190b;
            }
        """
        
        # Style pour la sélection
        if self.selected:
            base_style += """
                QFrame#response-item {
                    background-color: #e3f2fd;
                    border-color: #1976d2;
                    border-left-color: #0d47a1;
                }
            """
        
        self.setStyleSheet(base_style)
    
    def set_selected(self, selected: bool):
        """Définit l'état de sélection."""
        self.selected = selected
        self._apply_style()
    
    def mousePressEvent(self, event):
        """Gère le clic sur l'item."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.response)
        super().mousePressEvent(event)

class PendingResponsesView(QWidget):
    """Vue principale pour gérer les réponses en attente."""
    
    def __init__(self, auto_responder: AutoResponder, parent=None):
        super().__init__(parent)
        self.auto_responder = auto_responder
        self.pending_manager = auto_responder.pending_manager
        self.response_widgets = []
        self.selected_widget = None
        
        self._setup_ui()
        self._apply_style()
        self._setup_timer()
        self._refresh_responses()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header avec titre et compteur
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        title_label = QLabel("📋 Réponses en attente de validation")
        title_label.setObjectName("page-title")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Compteur avec style
        self.count_label = QLabel("0 réponses en attente")
        self.count_label.setObjectName("count-label")
        self.count_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.count_label.setStyleSheet("""
            QLabel#count-label {
                background-color: #e3f2fd;
                color: #1976d2;
                padding: 8px 16px;
                border-radius: 20px;
                border: 2px solid #2196f3;
            }
        """)
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Barre d'actions améliorée
        actions_frame = QFrame()
        actions_frame.setObjectName("actions-frame")
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(15, 10, 15, 10)
        actions_layout.setSpacing(10)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setObjectName("action-button")
        refresh_btn.clicked.connect(self._refresh_responses)
        refresh_btn.setMinimumHeight(35)
        actions_layout.addWidget(refresh_btn)
        
        approve_all_btn = QPushButton("✅ Tout approuver")
        approve_all_btn.setObjectName("approve-all-button")
        approve_all_btn.clicked.connect(self._approve_all_responses)
        approve_all_btn.setMinimumHeight(35)
        actions_layout.addWidget(approve_all_btn)
        
        reject_all_btn = QPushButton("❌ Tout rejeter")
        reject_all_btn.setObjectName("reject-all-button")
        reject_all_btn.clicked.connect(self._reject_all_responses)
        reject_all_btn.setMinimumHeight(35)
        actions_layout.addWidget(reject_all_btn)
        
        actions_layout.addStretch()
        
        cleanup_btn = QPushButton("🧹 Nettoyer")
        cleanup_btn.setObjectName("action-button")
        cleanup_btn.clicked.connect(self._cleanup_old_responses)
        cleanup_btn.setMinimumHeight(35)
        actions_layout.addWidget(cleanup_btn)
        
        layout.addWidget(actions_frame)
        
        # Zone principale avec splitter amélioré
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(3)
        
        # Liste des réponses avec taille fixe
        list_container = self._create_list_container()
        list_container.setMinimumWidth(500)
        list_container.setMaximumWidth(700)
        main_splitter.addWidget(list_container)
        
        # Zone de détails avec taille fixe
        details_container = self._create_details_container()
        details_container.setMinimumWidth(350)
        main_splitter.addWidget(details_container)
        
        # Configuration du splitter pour éviter le rétrécissement
        main_splitter.setSizes([550, 400])
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)
        
        layout.addWidget(main_splitter)
    
    def _create_list_container(self) -> QWidget:
        """Crée le container de la liste."""
        container = QFrame()
        container.setObjectName("list-container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # En-tête de liste
        list_header = QFrame()
        list_header.setObjectName("list-header")
        list_header.setFixedHeight(45)
        
        header_layout = QHBoxLayout(list_header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        header_title = QLabel("📋 Liste des réponses")
        header_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(header_title)
        
        layout.addWidget(list_header)
        
        # Zone de scroll avec taille définie
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setMinimumHeight(400)
        
        # Widget conteneur pour les réponses
        self.responses_container = QWidget()
        self.responses_layout = QVBoxLayout(self.responses_container)
        self.responses_layout.setContentsMargins(8, 8, 8, 8)
        self.responses_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.responses_container)
        layout.addWidget(self.scroll_area)
        
        # Message vide
        self.empty_message = QLabel("🔍 Aucune réponse en attente\n\nLes réponses automatiques générées par l'IA apparaîtront ici.")
        self.empty_message.setObjectName("empty-message")
        self.empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_message.setFont(QFont("Arial", 14))
        self.empty_message.setWordWrap(True)
        self.empty_message.setVisible(False)
        layout.addWidget(self.empty_message)
        
        return container
    
    def _create_details_container(self) -> QWidget:
        """Crée le container des détails."""
        container = QFrame()
        container.setObjectName("details-container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # En-tête détails
        details_header = QFrame()
        details_header.setObjectName("details-header")
        details_header.setFixedHeight(45)
        
        header_layout = QHBoxLayout(details_header)
        header_layout.setContentsMargins(0, 10, 0, 10)
        
        details_title = QLabel("🔍 Détails de la réponse")
        details_title.setObjectName("details-title")
        details_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(details_title)
        
        layout.addWidget(details_header)
        
        # Zone de détails avec scroll
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.details_frame = QWidget()
        self.details_layout = QVBoxLayout(self.details_frame)
        self.details_layout.setSpacing(10)
        
        # Message par défaut
        self.no_selection_label = QLabel("👆 Sélectionnez une réponse dans la liste pour voir les détails")
        self.no_selection_label.setObjectName("no-selection")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_selection_label.setFont(QFont("Arial", 12))
        self.no_selection_label.setWordWrap(True)
        self.details_layout.addWidget(self.no_selection_label)
        
        details_scroll.setWidget(self.details_frame)
        layout.addWidget(details_scroll)
        
        # Boutons d'action fixes en bas
        actions_frame = QFrame()
        actions_frame.setObjectName("actions-frame")
        actions_frame.setMinimumHeight(140)
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setSpacing(8)
        
        self.preview_btn = QPushButton("👁️ Prévisualiser et modifier")
        self.preview_btn.setObjectName("preview-button")
        self.preview_btn.clicked.connect(self._preview_selected_response)
        self.preview_btn.setVisible(False)
        self.preview_btn.setMinimumHeight(40)
        actions_layout.addWidget(self.preview_btn)
        
        self.quick_approve_btn = QPushButton("✅ Approuver rapidement")
        self.quick_approve_btn.setObjectName("quick-approve-button")
        self.quick_approve_btn.clicked.connect(self._quick_approve_selected)
        self.quick_approve_btn.setVisible(False)
        self.quick_approve_btn.setMinimumHeight(40)
        actions_layout.addWidget(self.quick_approve_btn)
        
        self.quick_reject_btn = QPushButton("❌ Rejeter")
        self.quick_reject_btn.setObjectName("quick-reject-button")
        self.quick_reject_btn.clicked.connect(self._quick_reject_selected)
        self.quick_reject_btn.setVisible(False)
        self.quick_reject_btn.setMinimumHeight(40)
        actions_layout.addWidget(self.quick_reject_btn)
        
        layout.addWidget(actions_frame)
        
        return container
    
    def _setup_timer(self):
        """Configure le timer pour le rafraîchissement automatique."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_responses)
        self.refresh_timer.start(30000)  # Rafraîchir toutes les 30 secondes
    
    def _refresh_responses(self):
        """Rafraîchit la liste des réponses en attente."""
        try:
            # Récupérer les réponses en attente
            responses = self.pending_manager.get_pending_responses()
            
            # Mettre à jour le compteur
            count_text = f"{len(responses)} réponse{'s' if len(responses) != 1 else ''} en attente"
            self.count_label.setText(count_text)
            
            # Effacer les anciens widgets
            self._clear_response_widgets()
            
            if not responses:
                self.empty_message.setVisible(True)
                self.scroll_area.setVisible(False)
                self._update_details_view(None)
                return
            
            self.empty_message.setVisible(False)
            self.scroll_area.setVisible(True)
            
            # Créer les nouveaux widgets
            for response in responses:
                widget = PendingResponseItem(response)
                widget.clicked.connect(self._on_response_selected)
                widget.approved.connect(self._on_quick_approve)
                widget.rejected.connect(self._on_quick_reject)
                
                self.responses_layout.addWidget(widget)
                self.response_widgets.append(widget)
            
            # Spacer pour pousser les éléments vers le haut
            self.responses_layout.addStretch()
            
            logger.info(f"Liste rafraîchie: {len(responses)} réponses en attente")
            
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement: {e}")
    
    def _clear_response_widgets(self):
        """Supprime tous les widgets de réponses."""
        for widget in self.response_widgets:
            widget.deleteLater()
        self.response_widgets.clear()
        self.selected_widget = None
        
        # Nettoyer le layout
        while self.responses_layout.count() > 0:
            child = self.responses_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _on_response_selected(self, response: PendingResponse):
        """Callback quand une réponse est sélectionnée."""
        # Désélectionner l'ancien widget
        if self.selected_widget:
            self.selected_widget.set_selected(False)
        
        # Sélectionner le nouveau widget
        sender_widget = self.sender()
        if isinstance(sender_widget, PendingResponseItem):
            sender_widget.set_selected(True)
            self.selected_widget = sender_widget
        
        # Mettre à jour la vue des détails
        self._update_details_view(response)
    
    def _update_details_view(self, response: Optional[PendingResponse]):
        """Met à jour la vue des détails."""
        # Effacer l'ancien contenu
        while self.details_layout.count() > 0:
            child = self.details_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not response:
            # Aucune sélection
            self.no_selection_label = QLabel("👆 Sélectionnez une réponse dans la liste pour voir les détails")
            self.no_selection_label.setObjectName("no-selection")
            self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_selection_label.setFont(QFont("Arial", 12))
            self.no_selection_label.setWordWrap(True)
            self.details_layout.addWidget(self.no_selection_label)
            
            # Masquer les boutons
            self.preview_btn.setVisible(False)
            self.quick_approve_btn.setVisible(False)
            self.quick_reject_btn.setVisible(False)
            return
        
        # Créer les éléments de détails avec un style amélioré
        details_data = [
            ("📧 Expéditeur", f"{response.original_sender}"),
            ("✉️ Email", f"{response.original_sender_email}"),
            ("📝 Sujet", response.original_subject),
            ("📁 Catégorie", response.category.upper()),
            ("🤔 Raison", response.reason),
            ("🎯 Confiance", f"{response.confidence_score:.1%}"),
        ]
        
        if response.created_at:
            details_data.append(("📅 Créé le", response.created_at.strftime('%d/%m/%Y à %H:%M')))
        
        for icon_title, content in details_data:
            detail_frame = QFrame()
            detail_frame.setObjectName("detail-item")
            detail_frame.setMinimumHeight(35)
            
            detail_layout = QVBoxLayout(detail_frame)
            detail_layout.setContentsMargins(12, 8, 12, 8)
            detail_layout.setSpacing(3)
            
            title_label = QLabel(icon_title)
            title_label.setObjectName("detail-title-label")
            title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            detail_layout.addWidget(title_label)
            
            content_label = QLabel(content)
            content_label.setObjectName("detail-content-label")
            content_label.setFont(QFont("Arial", 11))
            content_label.setWordWrap(True)
            content_label.setMaximumHeight(50)
            detail_layout.addWidget(content_label)
            
            self.details_layout.addWidget(detail_frame)
        
        # Aperçu de la réponse
        preview_frame = QFrame()
        preview_frame.setObjectName("preview-frame")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        
        preview_title = QLabel("📄 Aperçu de la réponse:")
        preview_title.setObjectName("preview-title")
        preview_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        preview_layout.addWidget(preview_title)
        
        preview_text = QTextEdit()
        preview_text.setPlainText(response.proposed_response)
        preview_text.setReadOnly(True)
        preview_text.setMaximumHeight(120)
        preview_text.setObjectName("preview-text")
        preview_layout.addWidget(preview_text)
        
        self.details_layout.addWidget(preview_frame)
        
        # Afficher les boutons
        self.preview_btn.setVisible(True)
        self.quick_approve_btn.setVisible(True)
        self.quick_reject_btn.setVisible(True)
        
        self.details_layout.addStretch()
    
    def _preview_selected_response(self):
        """Prévisualise la réponse sélectionnée."""
        if not self.selected_widget:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez d'abord sélectionner une réponse.")
            return
        
        response = self.selected_widget.response
        dialog = ResponsePreviewDialog(response, self)
        
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            # L'utilisateur a approuvé
            modified_content = dialog.get_modified_content()
            self._approve_response(response, modified_content)
    
    def _quick_approve_selected(self):
        """Approuve rapidement la réponse sélectionnée."""
        if not self.selected_widget:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez d'abord sélectionner une réponse.")
            return
        
        self._approve_response(self.selected_widget.response)
    
    def _quick_reject_selected(self):
        """Rejette la réponse sélectionnée."""
        if not self.selected_widget:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez d'abord sélectionner une réponse.")
            return
        
        self._reject_response(self.selected_widget.response)
    
    def _on_quick_approve(self, response: PendingResponse):
        """Callback pour l'approbation rapide depuis un widget."""
        self._approve_response(response)
    
    def _on_quick_reject(self, response: PendingResponse):
        """Callback pour le rejet rapide depuis un widget."""
        self._reject_response(response)
    
    def _approve_response(self, response: PendingResponse, modified_content: Optional[str] = None):
        """Approuve et envoie une réponse."""
        try:
            # Confirmation avant envoi
            reply = QMessageBox.question(
                self,
                "Confirmer l'envoi",
                f"Êtes-vous sûr de vouloir approuver et envoyer cette réponse à {response.original_sender_email} ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            success = self.auto_responder.approve_and_send_response(
                response.id,
                modified_content,
                "Approuvé depuis l'interface utilisateur"
            )
            
            if success:
                QMessageBox.information(
                    self, 
                    "Succès", 
                    f"✅ Réponse envoyée avec succès à {response.original_sender_email}!"
                )
                self._refresh_responses()
            else:
                QMessageBox.critical(
                    self, 
                    "Erreur", 
                    "❌ Erreur lors de l'envoi de la réponse.\nVeuillez vérifier votre connexion et réessayer."
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de l'approbation: {e}")
            QMessageBox.critical(self, "Erreur", f"❌ Erreur inattendue: {str(e)}")
    
    def _reject_response(self, response: PendingResponse):
        """Rejette une réponse."""
        try:
            # Confirmation avant rejet
            reply = QMessageBox.question(
                self,
                "Confirmer le rejet",
                f"Êtes-vous sûr de vouloir rejeter cette réponse pour {response.original_sender_email} ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            success = self.auto_responder.reject_response(
                response.id,
                "Rejeté depuis l'interface utilisateur"
            )
            
            if success:
                QMessageBox.information(self, "Rejet confirmé", "❌ Réponse rejetée avec succès")
                self._refresh_responses()
            else:
                QMessageBox.critical(self, "Erreur", "❌ Erreur lors du rejet de la réponse")
                
        except Exception as e:
            logger.error(f"Erreur lors du rejet: {e}")
            QMessageBox.critical(self, "Erreur", f"❌ Erreur inattendue: {str(e)}")
    
    def _approve_all_responses(self):
        """Approuve toutes les réponses en attente."""
        if not self.response_widgets:
            QMessageBox.information(self, "Aucune réponse", "Il n'y a aucune réponse en attente à approuver.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmer l'approbation en lot",
            f"⚠️ Êtes-vous sûr de vouloir approuver et envoyer TOUTES les {len(self.response_widgets)} réponses en attente ?\n\nCette action ne peut pas être annulée.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        success_count = 0
        error_count = 0
        
        # Barre de progression simple
        progress_msg = QMessageBox(self)
        progress_msg.setWindowTitle("Traitement en cours")
        progress_msg.setText("Envoi des réponses en cours...")
        progress_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_msg.show()
        
        QApplication.processEvents()
        
        for i, widget in enumerate(self.response_widgets):
            try:
                progress_msg.setText(f"Envoi de la réponse {i+1}/{len(self.response_widgets)}...")
                QApplication.processEvents()
                
                if self.auto_responder.approve_and_send_response(
                    widget.response.id,
                    None,
                    "Approbation en lot depuis l'interface"
                ):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Erreur lors de l'approbation en lot: {e}")
                error_count += 1
        
        progress_msg.close()
        
        # Afficher le résultat
        if error_count == 0:
            QMessageBox.information(
                self,
                "Succès complet",
                f"✅ Toutes les {success_count} réponses ont été envoyées avec succès!"
            )
        else:
            QMessageBox.warning(
                self,
                "Résultat mitigé",
                f"📊 Résultat de l'opération:\n"
                f"✅ Réussies: {success_count}\n"
                f"❌ Échecs: {error_count}\n\n"
                f"Veuillez vérifier les réponses en échec individuellement."
            )
        
        self._refresh_responses()
    
    def _reject_all_responses(self):
        """Rejette toutes les réponses en attente."""
        if not self.response_widgets:
            QMessageBox.information(self, "Aucune réponse", "Il n'y a aucune réponse en attente à rejeter.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmer le rejet en lot",
            f"⚠️ Êtes-vous sûr de vouloir rejeter TOUTES les {len(self.response_widgets)} réponses en attente ?\n\nCette action ne peut pas être annulée.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        success_count = 0
        error_count = 0
        
        for widget in self.response_widgets:
            try:
                if self.auto_responder.reject_response(
                    widget.response.id,
                    "Rejet en lot depuis l'interface"
                ):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Erreur lors du rejet en lot: {e}")
                error_count += 1
        
        QMessageBox.information(
            self,
            "Rejet terminé",
            f"📊 Résultat de l'opération:\n"
            f"✅ Rejetées: {success_count}\n"
            f"❌ Échecs: {error_count}"
        )
        
        self._refresh_responses()
    
    def _cleanup_old_responses(self):
        """Nettoie les anciennes réponses."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirmer le nettoyage",
                "Voulez-vous supprimer les anciennes réponses (envoyées et rejetées de plus de 30 jours) ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            deleted_count = self.pending_manager.cleanup_old_responses(30)
            QMessageBox.information(
                self,
                "Nettoyage terminé",
                f"🧹 {deleted_count} anciennes réponse{'s' if deleted_count != 1 else ''} supprimée{'s' if deleted_count != 1 else ''}"
            )
            self._refresh_responses()
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            QMessageBox.critical(self, "Erreur", f"❌ Erreur lors du nettoyage: {str(e)}")
    
    def _apply_style(self):
        """Applique le style à la vue."""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            
            QLabel#page-title {
                color: #000000;
                margin-bottom: 10px;
            }
            
            QFrame#actions-frame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin: 5px 0px;
            }
            
            QPushButton#action-button {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 120px;
            }
            
            QPushButton#action-button:hover {
                background-color: #f0f0f0;
                border-color: #cccccc;
            }
            
            QPushButton#approve-all-button {
                background-color: #4caf50;
                color: #ffffff;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 140px;
            }
            
            QPushButton#approve-all-button:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            
            QPushButton#reject-all-button {
                background-color: #f44336;
                color: #ffffff;
                border: 2px solid #f44336;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 130px;
            }
            
            QPushButton#reject-all-button:hover {
                background-color: #da190b;
                border-color: #da190b;
            }
            
            QFrame#list-container {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin: 5px;
            }
            
            QFrame#list-header {
                background-color: #e9ecef;
                border-bottom: 2px solid #dee2e6;
                border-radius: 10px 10px 0px 0px;
            }
            
            QFrame#details-container {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin: 5px;
            }
            
            QFrame#details-header {
                background-color: #f8f9fa;
                border-bottom: 2px solid #e9ecef;
                border-radius: 10px 10px 0px 0px;
            }
            
            QLabel#details-title {
                color: #000000;
                padding: 5px 0px;
            }
            
            QLabel#no-selection {
                color: #6c757d;
                margin: 30px;
                font-style: italic;
            }
            
            QFrame#detail-item {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                margin: 2px 0px;
            }
            
            QLabel#detail-title-label {
                color: #495057;
            }
            
            QLabel#detail-content-label {
                color: #212529;
            }
            
            QFrame#preview-frame {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 8px;
                margin: 5px 0px;
            }
            
            QLabel#preview-title {
                color: #1976d2;
            }
            
            QTextEdit#preview-text {
                background-color: #ffffff;
                border: 1px solid #2196f3;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #212529;
            }
            
            QPushButton#preview-button {
                background-color: #2196f3;
                color: #ffffff;
                border: 2px solid #2196f3;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                margin: 3px 0px;
            }
            
            QPushButton#preview-button:hover {
                background-color: #1976d2;
                border-color: #1976d2;
            }
            
            QPushButton#quick-approve-button {
                background-color: #4caf50;
                color: #ffffff;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                margin: 3px 0px;
            }
            
            QPushButton#quick-approve-button:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            
            QPushButton#quick-reject-button {
                background-color: #f44336;
                color: #ffffff;
                border: 2px solid #f44336;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                margin: 3px 0px;
            }
            
            QPushButton#quick-reject-button:hover {
                background-color: #da190b;
                border-color: #da190b;
            }
            
            QLabel#empty-message {
                color: #6c757d;
                margin: 50px;
                font-style: italic;
                line-height: 1.5;
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
                background-color: #ced4da;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
            
            QSplitter::handle {
                background-color: #dee2e6;
                width: 3px;
                border-radius: 1px;
            }
            
            QSplitter::handle:hover {
                background-color: #adb5bd;
            }
        """)
    
    def get_pending_count(self) -> int:
        """Retourne le nombre de réponses en attente."""
        return len(self.response_widgets)