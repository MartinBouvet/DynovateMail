"""
Vue pour gérer les réponses automatiques en attente de validation.
"""
import logging
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QTextEdit, QScrollArea, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QDialog, QDialogButtonBox,
    QGroupBox, QFormLayout
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
        self.resize(700, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface du dialogue."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title_label = QLabel("📧 Prévisualisation de la réponse automatique")
        title_label.setObjectName("dialog-title")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Informations sur l'email original
        original_group = QGroupBox("📨 Email original")
        original_group.setObjectName("info-group")
        original_layout = QFormLayout(original_group)
        
        original_layout.addRow("De:", QLabel(f"{self.response.original_sender} <{self.response.original_sender_email}>"))
        original_layout.addRow("Sujet:", QLabel(self.response.original_subject))
        original_layout.addRow("Catégorie:", QLabel(self.response.category.upper()))
        
        # Aperçu du contenu original
        original_preview = QLabel(self.response.original_body[:200] + "..." if len(self.response.original_body) > 200 else self.response.original_body)
        original_preview.setObjectName("email-preview")
        original_preview.setWordWrap(True)
        original_preview.setMaximumHeight(60)
        original_layout.addRow("Aperçu:", original_preview)
        
        layout.addWidget(original_group)
        
        # Analyse IA
        ai_group = QGroupBox("🤖 Analyse IA")
        ai_group.setObjectName("info-group")
        ai_layout = QFormLayout(ai_group)
        
        ai_layout.addRow("Raison:", QLabel(self.response.reason))
        ai_layout.addRow("Confiance:", QLabel(f"{self.response.confidence_score:.1%}"))
        
        layout.addWidget(ai_group)
        
        # Réponse proposée (modifiable)
        response_label = QLabel("✏️ Réponse proposée (modifiable)")
        response_label.setObjectName("section-title")
        response_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(response_label)
        
        self.response_text = QTextEdit()
        self.response_text.setObjectName("response-editor")
        self.response_text.setPlainText(self.response.proposed_response)
        self.response_text.setMinimumHeight(200)
        layout.addWidget(self.response_text)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        # Bouton rejeter
        reject_btn = QPushButton("❌ Rejeter")
        reject_btn.setObjectName("reject-button")
        reject_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(reject_btn)
        
        buttons_layout.addStretch()
        
        # Bouton approuver
        approve_btn = QPushButton("✅ Approuver et envoyer")
        approve_btn.setObjectName("approve-button")
        approve_btn.clicked.connect(self.approve)
        approve_btn.setDefault(True)
        buttons_layout.addWidget(approve_btn)
        
        layout.addLayout(buttons_layout)
        
        self._apply_style()
    
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
                margin-bottom: 10px;
            }
            
            QGroupBox#info-group {
                font-size: 13px;
                font-weight: bold;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f8f8f8;
            }
            
            QLabel#section-title {
                color: #000000;
                margin: 10px 0px 5px 0px;
            }
            
            QLabel#email-preview {
                color: #666666;
                font-style: italic;
                padding: 8px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            
            QTextEdit#response-editor {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-family: Arial, sans-serif;
                line-height: 1.4;
            }
            
            QTextEdit#response-editor:focus {
                border-color: #000000;
            }
            
            QPushButton#approve-button {
                background-color: #4caf50;
                color: #ffffff;
                border: 2px solid #4caf50;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 150px;
            }
            
            QPushButton#approve-button:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            
            QPushButton#reject-button {
                background-color: #f44336;
                color: #ffffff;
                border: 2px solid #f44336;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            
            QPushButton#reject-button:hover {
                background-color: #da190b;
                border-color: #da190b;
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
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)
        
        # Ligne 1: Expéditeur et catégorie
        header_layout = QHBoxLayout()
        
        # Expéditeur
        sender_label = QLabel(f"De: {self.response.original_sender}")
        sender_label.setObjectName("sender-label")
        sender_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(sender_label)
        
        header_layout.addStretch()
        
        # Badge catégorie
        category_badge = QLabel(self.response.category.upper())
        category_badge.setObjectName("category-badge")
        category_badge.setStyleSheet(f"""
            QLabel#category-badge {{
                background-color: {self._get_category_color(self.response.category)};
                color: white;
                border-radius: 10px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(category_badge)
        
        layout.addLayout(header_layout)
        
        # Ligne 2: Sujet
        subject_label = QLabel(f"Sujet: {self.response.original_subject}")
        subject_label.setObjectName("subject-label")
        subject_label.setFont(QFont("Arial", 11))
        layout.addWidget(subject_label)
        
        # Ligne 3: Aperçu réponse et actions
        footer_layout = QHBoxLayout()
        
        # Aperçu
        preview = self.response.proposed_response[:60] + "..." if len(self.response.proposed_response) > 60 else self.response.proposed_response
        preview_label = QLabel(f"Réponse: {preview}")
        preview_label.setObjectName("preview-label")
        preview_label.setFont(QFont("Arial", 10))
        footer_layout.addWidget(preview_label)
        
        footer_layout.addStretch()
        
        # Score de confiance
        confidence_label = QLabel(f"🎯 {self.response.confidence_score:.0%}")
        confidence_label.setObjectName("confidence-label")
        confidence_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        footer_layout.addWidget(confidence_label)
        
        # Actions rapides
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(5)
        
        approve_btn = QPushButton("✅")
        approve_btn.setObjectName("quick-approve")
        approve_btn.setFixedSize(25, 25)
        approve_btn.setToolTip("Approuver et envoyer")
        approve_btn.clicked.connect(lambda: self.approved.emit(self.response))
        quick_actions.addWidget(approve_btn)
        
        reject_btn = QPushButton("❌")
        reject_btn.setObjectName("quick-reject")
        reject_btn.setFixedSize(25, 25)
        reject_btn.setToolTip("Rejeter")
        reject_btn.clicked.connect(lambda: self.rejected.emit(self.response))
        quick_actions.addWidget(reject_btn)
        
        footer_layout.addLayout(quick_actions)
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
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px;
                border-left: 4px solid #0066cc;
            }
            
            QFrame#response-item:hover {
                background-color: #f5f5f5;
                border-color: #cccccc;
            }
            
            QLabel#sender-label {
                color: #000000;
            }
            
            QLabel#subject-label {
                color: #333333;
            }
            
            QLabel#preview-label {
                color: #666666;
            }
            
            QLabel#confidence-label {
                color: #4caf50;
            }
            
            QPushButton#quick-approve {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }
            
            QPushButton#quick-approve:hover {
                background-color: #45a049;
            }
            
            QPushButton#quick-reject {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }
            
            QPushButton#quick-reject:hover {
                background-color: #da190b;
            }
        """
        
        # Style pour la sélection
        if self.selected:
            base_style += """
                QFrame#response-item {
                    background-color: #e3f2fd;
                    border-color: #0066cc;
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
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📋 Réponses en attente de validation")
        title_label.setObjectName("page-title")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Compteur
        self.count_label = QLabel("0 réponses en attente")
        self.count_label.setObjectName("count-label")
        self.count_label.setFont(QFont("Arial", 14))
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Barre d'actions
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setObjectName("action-button")
        refresh_btn.clicked.connect(self._refresh_responses)
        actions_layout.addWidget(refresh_btn)
        
        approve_all_btn = QPushButton("✅ Tout approuver")
        approve_all_btn.setObjectName("approve-all-button")
        approve_all_btn.clicked.connect(self._approve_all_responses)
        actions_layout.addWidget(approve_all_btn)
        
        reject_all_btn = QPushButton("❌ Tout rejeter")
        reject_all_btn.setObjectName("reject-all-button")
        reject_all_btn.clicked.connect(self._reject_all_responses)
        actions_layout.addWidget(reject_all_btn)
        
        actions_layout.addStretch()
        
        cleanup_btn = QPushButton("🧹 Nettoyer")
        cleanup_btn.setObjectName("action-button")
        cleanup_btn.clicked.connect(self._cleanup_old_responses)
        actions_layout.addWidget(cleanup_btn)
        
        layout.addLayout(actions_layout)
        
        # Zone principale avec liste et détails
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Liste des réponses
        list_container = self._create_list_container()
        main_splitter.addWidget(list_container)
        
        # Zone de détails/actions
        details_container = self._create_details_container()
        main_splitter.addWidget(details_container)
        
        main_splitter.setSizes([400, 300])
        layout.addWidget(main_splitter)
    
    def _create_list_container(self) -> QWidget:
        """Crée le container de la liste."""
        container = QFrame()
        container.setObjectName("list-container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Zone de scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget conteneur pour les réponses
        self.responses_container = QWidget()
        self.responses_layout = QVBoxLayout(self.responses_container)
        self.responses_layout.setContentsMargins(5, 5, 5, 5)
        self.responses_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.responses_container)
        layout.addWidget(self.scroll_area)
        
        # Message vide
        self.empty_message = QLabel("Aucune réponse en attente")
        self.empty_message.setObjectName("empty-message")
        self.empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_message.setFont(QFont("Arial", 14))
        self.empty_message.setVisible(False)
        layout.addWidget(self.empty_message)
        
        return container
    
    def _create_details_container(self) -> QWidget:
        """Crée le container des détails."""
        container = QFrame()
        container.setObjectName("details-container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Titre
        details_title = QLabel("Détails de la réponse")
        details_title.setObjectName("details-title")
        details_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(details_title)
        
        # Zone de détails
        self.details_frame = QFrame()
        self.details_frame.setObjectName("details-frame")
        self.details_layout = QVBoxLayout(self.details_frame)
        
        # Message par défaut
        self.no_selection_label = QLabel("Sélectionnez une réponse pour voir les détails")
        self.no_selection_label.setObjectName("no-selection")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_selection_label.setFont(QFont("Arial", 12))
        self.details_layout.addWidget(self.no_selection_label)
        
        layout.addWidget(self.details_frame)
        
        # Boutons d'action détaillés
        actions_frame = QFrame()
        actions_frame.setObjectName("actions-frame")
        actions_layout = QVBoxLayout(actions_frame)
        
        self.preview_btn = QPushButton("👁️ Prévisualiser et modifier")
        self.preview_btn.setObjectName("preview-button")
        self.preview_btn.clicked.connect(self._preview_selected_response)
        self.preview_btn.setVisible(False)
        actions_layout.addWidget(self.preview_btn)
        
        self.quick_approve_btn = QPushButton("✅ Approuver rapidement")
        self.quick_approve_btn.setObjectName("quick-approve-button")
        self.quick_approve_btn.clicked.connect(self._quick_approve_selected)
        self.quick_approve_btn.setVisible(False)
        actions_layout.addWidget(self.quick_approve_btn)
        
        self.quick_reject_btn = QPushButton("❌ Rejeter")
        self.quick_reject_btn.setObjectName("quick-reject-button")
        self.quick_reject_btn.clicked.connect(self._quick_reject_selected)
        self.quick_reject_btn.setVisible(False)
        actions_layout.addWidget(self.quick_reject_btn)
        
        layout.addWidget(actions_frame)
        layout.addStretch()
        
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
            self.count_label.setText(f"{len(responses)} réponses en attente")
            
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
        for i in reversed(range(self.details_layout.count())):
            child = self.details_layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
        
        if not response:
            # Aucune sélection
            self.no_selection_label = QLabel("Sélectionnez une réponse pour voir les détails")
            self.no_selection_label.setObjectName("no-selection")
            self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_selection_label.setFont(QFont("Arial", 12))
            self.details_layout.addWidget(self.no_selection_label)
            
            # Masquer les boutons
            self.preview_btn.setVisible(False)
            self.quick_approve_btn.setVisible(False)
            self.quick_reject_btn.setVisible(False)
            return
        
        # Afficher les détails
        # Expéditeur
        sender_label = QLabel(f"📧 De: {response.original_sender}")
        sender_label.setObjectName("detail-label")
        sender_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.details_layout.addWidget(sender_label)
        
        # Email
        email_label = QLabel(f"✉️ Email: {response.original_sender_email}")
        email_label.setObjectName("detail-label")
        email_label.setFont(QFont("Arial", 11))
        self.details_layout.addWidget(email_label)
        
        # Sujet
        subject_label = QLabel(f"📝 Sujet: {response.original_subject}")
        subject_label.setObjectName("detail-label")
        subject_label.setFont(QFont("Arial", 11))
        subject_label.setWordWrap(True)
        self.details_layout.addWidget(subject_label)
        
        # Catégorie
        category_label = QLabel(f"📁 Catégorie: {response.category.upper()}")
        category_label.setObjectName("detail-label")
        category_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.details_layout.addWidget(category_label)
        
        # Raison
        reason_label = QLabel(f"🤔 Raison: {response.reason}")
        reason_label.setObjectName("detail-label")
        reason_label.setFont(QFont("Arial", 11))
        reason_label.setWordWrap(True)
        self.details_layout.addWidget(reason_label)
        
        # Score de confiance
        confidence_label = QLabel(f"🎯 Confiance: {response.confidence_score:.1%}")
        confidence_label.setObjectName("detail-label")
        confidence_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.details_layout.addWidget(confidence_label)
        
        # Date
        if response.created_at:
            date_label = QLabel(f"📅 Créé le: {response.created_at.strftime('%d/%m/%Y à %H:%M')}")
            date_label.setObjectName("detail-label")
            date_label.setFont(QFont("Arial", 10))
            self.details_layout.addWidget(date_label)
        
        # Aperçu de la réponse
        preview_title = QLabel("📄 Aperçu de la réponse:")
        preview_title.setObjectName("detail-title")
        preview_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.details_layout.addWidget(preview_title)
        
        preview_text = QLabel(response.proposed_response[:200] + "..." if len(response.proposed_response) > 200 else response.proposed_response)
        preview_text.setObjectName("response-preview")
        preview_text.setWordWrap(True)
        preview_text.setMaximumHeight(100)
        self.details_layout.addWidget(preview_text)
        
        # Afficher les boutons
        self.preview_btn.setVisible(True)
        self.quick_approve_btn.setVisible(True)
        self.quick_reject_btn.setVisible(True)
        
        self.details_layout.addStretch()
    
    def _preview_selected_response(self):
        """Prévisualise la réponse sélectionnée."""
        if not self.selected_widget:
            return
        
        response = self.selected_widget.response
        dialog = ResponsePreviewDialog(response, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # L'utilisateur a approuvé
            modified_content = dialog.get_modified_content()
            self._approve_response(response, modified_content)
        # Si rejeté, on ne fait rien (le dialogue gère le rejet)
    
    def _quick_approve_selected(self):
        """Approuve rapidement la réponse sélectionnée."""
        if self.selected_widget:
            self._approve_response(self.selected_widget.response)
    
    def _quick_reject_selected(self):
        """Rejette la réponse sélectionnée."""
        if self.selected_widget:
            self._reject_response(self.selected_widget.response)
    
    def _on_quick_approve(self, response: PendingResponse):
        """Callback pour l'approbation rapide."""
        self._approve_response(response)
    
    def _on_quick_reject(self, response: PendingResponse):
       """Callback pour le rejet rapide."""
       self._reject_response(response)
   
    def _approve_response(self, response: PendingResponse, modified_content: Optional[str] = None):
       """Approuve et envoie une réponse."""
       try:
           success = self.auto_responder.approve_and_send_response(
               response.id,
               modified_content,
               "Approuvé depuis l'interface"
           )
           
           if success:
               QMessageBox.information(self, "Succès", "✅ Réponse envoyée avec succès!")
               self._refresh_responses()
           else:
               QMessageBox.critical(self, "Erreur", "❌ Erreur lors de l'envoi de la réponse")
               
       except Exception as e:
           logger.error(f"Erreur lors de l'approbation: {e}")
           QMessageBox.critical(self, "Erreur", f"❌ Erreur: {e}")
   
    def _reject_response(self, response: PendingResponse):
       """Rejette une réponse."""
       try:
           success = self.auto_responder.reject_response(
               response.id,
               "Rejeté depuis l'interface"
           )
           
           if success:
               QMessageBox.information(self, "Rejet", "❌ Réponse rejetée")
               self._refresh_responses()
           else:
               QMessageBox.critical(self, "Erreur", "❌ Erreur lors du rejet")
               
       except Exception as e:
           logger.error(f"Erreur lors du rejet: {e}")
           QMessageBox.critical(self, "Erreur", f"❌ Erreur: {e}")
   
    def _approve_all_responses(self):
       """Approuve toutes les réponses en attente."""
       if not self.response_widgets:
           return
       
       reply = QMessageBox.question(
           self,
           "Confirmer l'approbation",
           f"Êtes-vous sûr de vouloir approuver et envoyer toutes les {len(self.response_widgets)} réponses en attente ?",
           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
           QMessageBox.StandardButton.No
       )
       
       if reply == QMessageBox.StandardButton.Yes:
           success_count = 0
           for widget in self.response_widgets:
               try:
                   if self.auto_responder.approve_and_send_response(
                       widget.response.id,
                       None,
                       "Approbation en lot"
                   ):
                       success_count += 1
               except Exception as e:
                   logger.error(f"Erreur lors de l'approbation en lot: {e}")
           
           QMessageBox.information(
               self,
               "Résultat",
               f"✅ {success_count}/{len(self.response_widgets)} réponses envoyées avec succès"
           )
           self._refresh_responses()
   
    def _reject_all_responses(self):
       """Rejette toutes les réponses en attente."""
       if not self.response_widgets:
           return
       
       reply = QMessageBox.question(
           self,
           "Confirmer le rejet",
           f"Êtes-vous sûr de vouloir rejeter toutes les {len(self.response_widgets)} réponses en attente ?",
           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
           QMessageBox.StandardButton.No
       )
       
       if reply == QMessageBox.StandardButton.Yes:
           success_count = 0
           for widget in self.response_widgets:
               try:
                   if self.auto_responder.reject_response(
                       widget.response.id,
                       "Rejet en lot"
                   ):
                       success_count += 1
               except Exception as e:
                   logger.error(f"Erreur lors du rejet en lot: {e}")
           
           QMessageBox.information(
               self,
               "Résultat",
               f"❌ {success_count}/{len(self.response_widgets)} réponses rejetées"
           )
           self._refresh_responses()
   
    def _cleanup_old_responses(self):
       """Nettoie les anciennes réponses."""
       try:
           deleted_count = self.pending_manager.cleanup_old_responses(30)
           QMessageBox.information(
               self,
               "Nettoyage",
               f"🧹 {deleted_count} anciennes réponses supprimées"
           )
           self._refresh_responses()
       except Exception as e:
           logger.error(f"Erreur lors du nettoyage: {e}")
           QMessageBox.critical(self, "Erreur", f"❌ Erreur lors du nettoyage: {e}")
   
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
           
           QLabel#count-label {
               color: #666666;
               font-weight: bold;
           }
           
           QPushButton#action-button {
               background-color: #ffffff;
               color: #000000;
               border: 2px solid #e0e0e0;
               border-radius: 6px;
               padding: 8px 16px;
               font-size: 13px;
               min-width: 100px;
           }
           
           QPushButton#action-button:hover {
               background-color: #f0f0f0;
               border-color: #cccccc;
           }
           
           QPushButton#approve-all-button {
               background-color: #4caf50;
               color: #ffffff;
               border: 2px solid #4caf50;
               border-radius: 6px;
               padding: 8px 16px;
               font-size: 13px;
               min-width: 120px;
           }
           
           QPushButton#approve-all-button:hover {
               background-color: #45a049;
               border-color: #45a049;
           }
           
           QPushButton#reject-all-button {
               background-color: #f44336;
               color: #ffffff;
               border: 2px solid #f44336;
               border-radius: 6px;
               padding: 8px 16px;
               font-size: 13px;
               min-width: 120px;
           }
           
           QPushButton#reject-all-button:hover {
               background-color: #da190b;
               border-color: #da190b;
           }
           
           QFrame#list-container {
               background-color: #f8f8f8;
               border: 1px solid #e0e0e0;
               border-radius: 8px;
           }
           
           QFrame#details-container {
               background-color: #ffffff;
               border: 1px solid #e0e0e0;
               border-radius: 8px;
           }
           
           QLabel#details-title {
               color: #000000;
               margin-bottom: 15px;
               padding-bottom: 5px;
               border-bottom: 2px solid #e0e0e0;
           }
           
           QLabel#no-selection {
               color: #999999;
               margin: 50px;
           }
           
           QLabel#detail-label {
               color: #333333;
               margin: 3px 0px;
               padding: 5px;
               background-color: #f8f8f8;
               border-radius: 4px;
           }
           
           QLabel#detail-title {
               color: #000000;
               margin: 10px 0px 5px 0px;
           }
           
           QLabel#response-preview {
               color: #666666;
               font-style: italic;
               padding: 10px;
               background-color: #f0f0f0;
               border-radius: 6px;
               border-left: 4px solid #0066cc;
           }
           
           QPushButton#preview-button {
               background-color: #2196f3;
               color: #ffffff;
               border: 2px solid #2196f3;
               border-radius: 6px;
               padding: 10px 15px;
               font-size: 13px;
               margin: 5px 0px;
           }
           
           QPushButton#preview-button:hover {
               background-color: #1976d2;
               border-color: #1976d2;
           }
           
           QPushButton#quick-approve-button {
               background-color: #4caf50;
               color: #ffffff;
               border: 2px solid #4caf50;
               border-radius: 6px;
               padding: 10px 15px;
               font-size: 13px;
               margin: 5px 0px;
           }
           
           QPushButton#quick-approve-button:hover {
               background-color: #45a049;
               border-color: #45a049;
           }
           
           QPushButton#quick-reject-button {
               background-color: #f44336;
               color: #ffffff;
               border: 2px solid #f44336;
               border-radius: 6px;
               padding: 10px 15px;
               font-size: 13px;
               margin: 5px 0px;
           }
           
           QPushButton#quick-reject-button:hover {
               background-color: #da190b;
               border-color: #da190b;
           }
           
           QLabel#empty-message {
               color: #999999;
               margin: 50px;
           }
           
           QScrollArea {
               border: none;
               background-color: transparent;
           }
           
           QScrollBar:vertical {
               background-color: #f8f8f8;
               width: 8px;
               border-radius: 4px;
           }
           
           QScrollBar::handle:vertical {
               background-color: #cccccc;
               border-radius: 4px;
               min-height: 20px;
           }
           
           QScrollBar::handle:vertical:hover {
               background-color: #999999;
           }
       """)
   
    def get_pending_count(self) -> int:
       """Retourne le nombre de réponses en attente."""
       return len(self.response_widgets)