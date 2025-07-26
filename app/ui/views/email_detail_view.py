#!/usr/bin/env python3
"""
Vue détaillée d'un email CORRIGÉE avec rendu HTML complet et images.
"""
import logging
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

from models.email_model import Email, EmailAttachment
from gmail_client import GmailClient

logger = logging.getLogger(__name__)

class AttachmentCard(QFrame):
    """Carte d'affichage d'une pièce jointe."""
    
    download_requested = pyqtSignal(object)  # EmailAttachment
    
    def __init__(self, attachment: EmailAttachment):
        super().__init__()
        self.attachment = attachment
        
        self.setObjectName("attachment-card")
        self.setFixedHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface de la carte de pièce jointe."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Icône du fichier
        icon_label = QLabel(self.attachment.icon)
        icon_label.setFont(QFont("Arial", 18))
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Informations du fichier
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Nom du fichier
        filename = self.attachment.filename
        if len(filename) > 35:
            filename = filename[:32] + "..."
        
        name_label = QLabel(filename)
        name_label.setObjectName("attachment-name")
        name_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        info_layout.addWidget(name_label)
        
        # Taille et type
        size_type_label = QLabel(f"{self.attachment.size} • {self.attachment.mime_type.split('/')[-1].upper()}")
        size_type_label.setObjectName("attachment-info")
        size_type_label.setFont(QFont("Inter", 10))
        info_layout.addWidget(size_type_label)
        
        layout.addWidget(info_container)
        layout.addStretch()
        
        # Bouton de téléchargement
        if self.attachment.downloadable:
            download_btn = QPushButton("📥")
            download_btn.setObjectName("download-btn")
            download_btn.setFixedSize(36, 36)
            download_btn.setFont(QFont("Arial", 14))
            download_btn.setToolTip("Télécharger")
            download_btn.clicked.connect(lambda: self.download_requested.emit(self.attachment))
            layout.addWidget(download_btn)
        else:
            unavailable_label = QLabel("❌")
            unavailable_label.setFont(QFont("Arial", 14))
            unavailable_label.setToolTip("Non téléchargeable")
            layout.addWidget(unavailable_label)
    
    def _apply_style(self):
        """Applique le style à la carte."""
        self.setStyleSheet("""
            QFrame#attachment-card {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin: 2px 0;
            }
            
            QFrame#attachment-card:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            
            QLabel#attachment-name {
                color: #495057;
                font-weight: 600;
            }
            
            QLabel#attachment-info {
                color: #6c757d;
                font-weight: 400;
            }
            
            QPushButton#download-btn {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
            }
            
            QPushButton#download-btn:hover {
                background-color: #0056b3;
            }
            
            QPushButton#download-btn:pressed {
                background-color: #004085;
            }
        """)

class EmailContentDisplay(QWidget):
    """Widget d'affichage du contenu email avec rendu HTML."""
    
    def __init__(self):
        super().__init__()
        self.current_content = ""
        self.is_html = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toggle pour basculer entre HTML et texte
        self.toggle_frame = QFrame()
        self.toggle_frame.setObjectName("toggle-frame")
        self.toggle_frame.setFixedHeight(40)
        
        toggle_layout = QHBoxLayout(self.toggle_frame)
        toggle_layout.setContentsMargins(15, 5, 15, 5)
        toggle_layout.setSpacing(10)
        
        self.format_label = QLabel("📄 Format:")
        self.format_label.setFont(QFont("Inter", 11, QFont.Weight.Medium))
        toggle_layout.addWidget(self.format_label)
        
        self.html_btn = QPushButton("🌐 HTML")
        self.html_btn.setObjectName("format-btn")
        self.html_btn.setFixedSize(80, 28)
        self.html_btn.setCheckable(True)
        self.html_btn.clicked.connect(lambda: self._set_display_mode(True))
        toggle_layout.addWidget(self.html_btn)
        
        self.text_btn = QPushButton("📝 Texte")
        self.text_btn.setObjectName("format-btn")
        self.text_btn.setFixedSize(80, 28)
        self.text_btn.setCheckable(True)
        self.text_btn.clicked.connect(lambda: self._set_display_mode(False))
        toggle_layout.addWidget(self.text_btn)
        
        toggle_layout.addStretch()
        
        layout.addWidget(self.toggle_frame)
        
        # Vue web pour HTML
        try:
            self.web_view = QWebEngineView()
            self.web_view.setObjectName("email-web-view")
            layout.addWidget(self.web_view)
        except ImportError:
            logger.warning("QWebEngineView non disponible - rendu HTML désactivé")
            self.web_view = None
        
        # Vue texte pour fallback
        self.text_view = QTextEdit()
        self.text_view.setObjectName("email-text-view")
        self.text_view.setReadOnly(True)
        self.text_view.setFont(QFont("Inter", 13))
        self.text_view.hide()
        layout.addWidget(self.text_view)
        
        # Appliquer les styles
        self._apply_styles()
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            QFrame#toggle-frame {
                background-color: #f8f9fa;
                border-bottom: 2px solid #e9ecef;
            }
            
            QPushButton#format-btn {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 14px;
                color: #495057;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
            }
            
            QPushButton#format-btn:checked {
                background-color: #007bff;
                border-color: #007bff;
                color: #ffffff;
            }
            
            QPushButton#format-btn:hover {
                border-color: #adb5bd;
            }
            
            QWebEngineView#email-web-view {
                border: none;
                background-color: #ffffff;
            }
            
            QTextEdit#email-text-view {
                background-color: #ffffff;
                border: none;
                padding: 20px;
                color: #495057;
                line-height: 1.7;
                font-family: 'Inter', Arial, sans-serif;
            }
        """)
    
    def set_content(self, content: str, is_html: bool = False):
        """Définit le contenu à afficher."""
        self.current_content = content
        self.is_html = is_html
        
        # Afficher/masquer les boutons selon le type de contenu
        if is_html and self.web_view:
            self.toggle_frame.show()
            self._set_display_mode(True)  # Commencer en mode HTML
        else:
            self.toggle_frame.hide()
            self._set_display_mode(False)  # Mode texte uniquement
    
    def _set_display_mode(self, html_mode: bool):
        """Bascule entre mode HTML et texte."""
        if html_mode and self.is_html and self.web_view:
            # Mode HTML
            self.html_btn.setChecked(True)
            self.text_btn.setChecked(False)
            
            # Créer un HTML complet avec styles
            full_html = self._create_full_html(self.current_content)
            self.web_view.setHtml(full_html)
            
            self.web_view.show()
            self.text_view.hide()
        else:
            # Mode texte
            self.html_btn.setChecked(False)
            self.text_btn.setChecked(True)
            
            # Convertir HTML en texte si nécessaire
            if self.is_html:
                text_content = self._html_to_text(self.current_content)
            else:
                text_content = self.current_content
            
            self.text_view.setPlainText(text_content)
            
            self.web_view.hide() if self.web_view else None
            self.text_view.show()
    
    def _create_full_html(self, content: str) -> str:
        """Crée un document HTML complet avec styles."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #495057;
                    margin: 20px;
                    background-color: #ffffff;
                }}
                
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 6px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    margin: 8px 0;
                }}
                
                a {{
                    color: #007bff;
                    text-decoration: none;
                }}
                
                a:hover {{
                    text-decoration: underline;
                }}
                
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 12px 0;
                }}
                
                table, th, td {{
                    border: 1px solid #dee2e6;
                }}
                
                th, td {{
                    padding: 8px 12px;
                    text-align: left;
                }}
                
                th {{
                    background-color: #f8f9fa;
                    font-weight: 600;
                }}
                
                blockquote {{
                    border-left: 4px solid #007bff;
                    margin: 16px 0;
                    padding: 8px 16px;
                    background-color: #f8f9fa;
                    font-style: italic;
                }}
                
                pre {{
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    padding: 12px;
                    overflow-x: auto;
                    font-family: 'Courier New', monospace;
                }}
                
                code {{
                    background-color: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                
                .email-signature {{
                    border-top: 1px solid #dee2e6;
                    margin-top: 20px;
                    padding-top: 12px;
                    font-size: 12px;
                    color: #6c757d;
                }}
                
                /* Styles pour les emails Outlook/Exchange */
                .MsoNormal {{
                    margin: 0 !important;
                    padding: 4px 0 !important;
                }}
                
                /* Réduire l'espacement excessif */
                p {{
                    margin: 8px 0;
                }}
                
                div {{
                    margin: 4px 0;
                }}
                
                /* Masquer les éléments de tracking */
                img[width="1"], img[height="1"] {{
                    display: none !important;
                }}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """
    
    def _html_to_text(self, html_content: str) -> str:
        """Convertit HTML en texte lisible."""
        try:
            import re
            import html
            
            # Décoder les entités HTML
            text = html.unescape(html_content)
            
            # Supprimer les scripts, styles et commentaires
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
            
            # Traiter les balises de structure
            text = re.sub(r'</(div|p|section|article|header|footer|main|aside)>', '\n\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<(div|p|section|article|header|footer|main|aside)[^>]*>', '\n', text, flags=re.IGNORECASE)
            
            # Traiter les titres
            text = re.sub(r'</h[1-6]>', '\n\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<h[1-6][^>]*>', '\n\n', text, flags=re.IGNORECASE)
            
            # Traiter les listes
            text = re.sub(r'<li[^>]*>', '\n• ', text, flags=re.IGNORECASE)
            text = re.sub(r'</li>', '', text, flags=re.IGNORECASE)
            text = re.sub(r'</(ul|ol)>', '\n\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<(ul|ol)[^>]*>', '\n', text, flags=re.IGNORECASE)
            
            # Traiter les sauts de ligne
            text = re.sub(r'<br[^>]*/?>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<hr[^>]*/?>', '\n---\n', text, flags=re.IGNORECASE)
            
            # Traiter les liens
            def replace_link(match):
                href = match.group(1) if match.group(1) else ''
                link_text = match.group(2).strip()
                if href and href != link_text and not link_text.startswith('http'):
                    return f"{link_text} ({href})"
                else:
                    return link_text
            
            text = re.sub(r'<a[^>]*href=["\']?([^"\'>\s]+)["\']?[^>]*>(.*?)</a>', 
                         replace_link, text, flags=re.IGNORECASE | re.DOTALL)
            
            # Traiter le formatage
            text = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', text, flags=re.IGNORECASE | re.DOTALL)
            
            # Supprimer toutes les autres balises
            text = re.sub(r'<[^>]+>', '', text)
            
            # Nettoyer les espaces
            text = re.sub(r'[ \t]+\n', '\n', text)
            text = re.sub(r'\n[ \t]+', '\n', text)
            text = re.sub(r'[ \t]{2,}', ' ', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Erreur conversion HTML: {e}")
            return html_content

class EmailDetailView(QWidget):
    """Vue détaillée CORRIGÉE d'un email avec rendu HTML complet."""
    
    action_requested = pyqtSignal(str, object)
    
    def __init__(self, gmail_client: GmailClient = None):
        super().__init__()
        self.current_email = None
        self.gmail_client = gmail_client
        
        self.setObjectName("email-detail-view")
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface CORRIGÉE avec rendu HTML."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone de scroll pour tout le contenu
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu scrollable
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        
        # Message par défaut
        self.no_selection_widget = self._create_no_selection_widget()
        self.content_layout.addWidget(self.no_selection_widget)
        
        # Contenu de l'email (caché par défaut)
        self.email_content_widget = self._create_email_content_widget()
        self.email_content_widget.hide()
        self.content_layout.addWidget(self.email_content_widget)
        
        # Spacer pour pousser le contenu vers le haut
        self.content_layout.addStretch()
        
        # Configurer le scroll
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
    
    def _create_no_selection_widget(self) -> QWidget:
        """Widget quand aucun email n'est sélectionné."""
        widget = QWidget()
        widget.setObjectName("no-selection-widget")
        
        # Layout principal centré
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 0, 40, 0)
        main_layout.setSpacing(0)
        
        # Spacer du haut pour centrer verticalement
        main_layout.addStretch(1)
        
        # Container centré
        center_container = QWidget()
        center_container.setFixedSize(500, 300)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(25)
        
        # Icône
        icon_label = QLabel("📧")
        icon_label.setFont(QFont("Arial", 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #e0e0e0;")
        center_layout.addWidget(icon_label)
        
        # Texte principal
        title_label = QLabel("Sélectionnez un email")
        title_label.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #616161; margin: 0;")
        center_layout.addWidget(title_label)
        
        # Texte descriptif
        desc_label = QLabel("Cliquez sur un email dans la liste de gauche pour voir son contenu avec le rendu HTML complet et les images intégrées.")
        desc_label.setFont(QFont("Inter", 14))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #9e9e9e; line-height: 1.6; margin: 0; padding: 0;")
        center_layout.addWidget(desc_label)
        
        # Centrer le container horizontalement
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(center_container)
        h_layout.addStretch(1)
        
        main_layout.addLayout(h_layout)
        
        # Spacer du bas pour centrer verticalement
        main_layout.addStretch(1)
        
        return widget
    
    def _create_email_content_widget(self) -> QWidget:
        """Widget de contenu d'email CORRIGÉ avec rendu HTML."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header de l'email
        self.email_header = self._create_email_header()
        layout.addWidget(self.email_header)
        
        # Section des pièces jointes (cachée par défaut)
        self.attachments_section = self._create_attachments_section()
        self.attachments_section.hide()
        layout.addWidget(self.attachments_section)
        
        # Actions
        self.email_actions = self._create_email_actions()
        layout.addWidget(self.email_actions)
        
        # Contenu avec rendu HTML
        self.email_content_display = EmailContentDisplay()
        layout.addWidget(self.email_content_display)
        
        # Analyse IA
        self.ai_analysis_section = self._create_ai_analysis_section()
        layout.addWidget(self.ai_analysis_section)
        
        return widget
    
    def _create_email_header(self) -> QFrame:
        """Header de l'email CORRIGÉ."""
        header = QFrame()
        header.setObjectName("email-header")
        header.setMinimumHeight(140)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Ligne 1: Expéditeur et date
        first_row = QHBoxLayout()
        first_row.setSpacing(20)
        
        self.sender_label = QLabel()
        self.sender_label.setObjectName("sender-name")
        self.sender_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.sender_label.setWordWrap(True)
        first_row.addWidget(self.sender_label)
        
        first_row.addStretch()
        
        self.date_label = QLabel()
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Inter", 13))
        first_row.addWidget(self.date_label)
        
        layout.addLayout(first_row)
        
        # Ligne 2: Email address
        self.email_address_label = QLabel()
        self.email_address_label.setObjectName("email-address")
        self.email_address_label.setFont(QFont("Inter", 12))
        self.email_address_label.setWordWrap(True)
        layout.addWidget(self.email_address_label)
        
        # Ligne 3: Sujet
        self.subject_label = QLabel()
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        self.subject_label.setMinimumHeight(50)
        layout.addWidget(self.subject_label)
        
        return header
    
    def _create_attachments_section(self) -> QFrame:
        """Section des pièces jointes."""
        attachments_frame = QFrame()
        attachments_frame.setObjectName("attachments-section")
        
        layout = QVBoxLayout(attachments_frame)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 15, 25, 15)
        
        # Titre
        title_layout = QHBoxLayout()
        title_icon = QLabel("📎")
        title_icon.setFont(QFont("Arial", 16))
        title_layout.addWidget(title_icon)
        
        self.attachments_title = QLabel("Pièces jointes")
        self.attachments_title.setObjectName("section-title")
        self.attachments_title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        title_layout.addWidget(self.attachments_title)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Container pour les cartes de pièces jointes
        self.attachments_container = QWidget()
        self.attachments_layout = QVBoxLayout(self.attachments_container)
        self.attachments_layout.setSpacing(6)
        self.attachments_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.attachments_container)
        
        return attachments_frame
    
    def _create_email_actions(self) -> QFrame:
        """Barre d'actions."""
        actions = QFrame()
        actions.setObjectName("email-actions")
        actions.setFixedHeight(80)
        
        # Layout principal avec centrage parfait
        main_layout = QVBoxLayout(actions)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Spacer vertical pour centrer
        main_layout.addStretch(1)
        
        # Container des boutons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(25, 0, 25, 0)
        buttons_layout.setSpacing(0)
        
        # Centrage parfait avec des spacers
        buttons_layout.addStretch(2)
        
        # Boutons principaux
        self.reply_btn = QPushButton("↩️ Répondre")
        self.reply_btn.setObjectName("action-btn")
        self.reply_btn.setFixedSize(140, 45)
        self.reply_btn.clicked.connect(lambda: self.action_requested.emit("reply", self.current_email))
        buttons_layout.addWidget(self.reply_btn)
        
        buttons_layout.addSpacing(15)
        
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        self.forward_btn.setFixedSize(140, 45)
        self.forward_btn.clicked.connect(lambda: self.action_requested.emit("forward", self.current_email))
        buttons_layout.addWidget(self.forward_btn)
        
        buttons_layout.addSpacing(15)
        
        self.archive_btn = QPushButton("📁 Archiver")
        self.archive_btn.setObjectName("action-btn")
        self.archive_btn.setFixedSize(140, 45)
        self.archive_btn.clicked.connect(lambda: self.action_requested.emit("archive", self.current_email))
        buttons_layout.addWidget(self.archive_btn)
        
        buttons_layout.addSpacing(30)
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("delete-btn")
        self.delete_btn.setFixedSize(140, 45)
        self.delete_btn.clicked.connect(lambda: self.action_requested.emit("delete", self.current_email))
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch(2)
        
        main_layout.addWidget(buttons_container)
        main_layout.addStretch(1)
        
        return actions
    
    def _create_ai_analysis_section(self) -> QFrame:
        """Section d'analyse IA."""
        ai_frame = QFrame()
        ai_frame.setObjectName("ai-analysis-frame")
        ai_frame.setMinimumHeight(200)
        
        layout = QVBoxLayout(ai_frame)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Titre
        title = QLabel("🤖 Analyse Intelligence Artificielle")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Contenu de l'analyse
        self.ai_content = QLabel("Aucune analyse disponible")
        self.ai_content.setObjectName("ai-analysis-content")
        self.ai_content.setWordWrap(True)
        self.ai_content.setFont(QFont("Inter", 13))
        self.ai_content.setMinimumHeight(120)
        self.ai_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.ai_content)
        
        return ai_frame
    
    def _apply_style(self):
        """Style CORRIGÉ pour une excellente lisibilité."""
        self.setStyleSheet("""
            QWidget#email-detail-view {
                background-color: #ffffff;
            }
            
            QWidget#no-selection-widget {
                background-color: #ffffff;
            }
            
            /* === SCROLLBAR === */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #cbd3da;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #9ea7ad;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* === HEADER EMAIL === */
            QFrame#email-header {
                background-color: #f8fafe;
                border: 3px solid #e3f2fd;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QLabel#sender-name {
                color: #0d47a1;
                font-weight: 700;
                line-height: 1.3;
            }
            
            QLabel#email-date {
                color: #546e7a;
                font-weight: 500;
                background-color: #eceff1;
                padding: 8px 12px;
                border-radius: 20px;
            }
            
            QLabel#email-address {
                color: #607d8b;
                font-weight: 400;
                font-style: italic;
            }
            
            QLabel#email-subject {
                color: #1a237e;
                font-weight: 700;
                margin-top: 10px;
                line-height: 1.4;
                padding: 10px 0;
            }
            
            /* === PIÈCES JOINTES === */
            QFrame#attachments-section {
                background-color: #fff3e0;
                border: 3px solid #ffcc02;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            /* === ACTIONS === */
            QFrame#email-actions {
                background-color: #f8f9fa;
                border: 2px solid #e3f2fd;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QPushButton#action-btn {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;
            }
            
            QPushButton#action-btn:hover {
                background-color: #1565c0;
                transform: translateY(-1px);
            }
            
            QPushButton#action-btn:pressed {
                background-color: #0d47a1;
                transform: translateY(0px);
            }
            
            QPushButton#delete-btn {
                background-color: #d32f2f;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;
            }
            
            QPushButton#delete-btn:hover {
                background-color: #c62828;
                transform: translateY(-1px);
            }
            
            QPushButton#delete-btn:pressed {
                background-color: #b71c1c;
                transform: translateY(0px);
            }
            
            /* === ANALYSE IA === */
            QFrame#ai-analysis-frame {
                background-color: #f3e5f5;
                border: 3px solid #ce93d8;
                border-radius: 15px;
                margin-bottom: 20px;
            }
            
            QLabel#section-title {
                color: #1a237e;
                font-weight: 700;
                margin-bottom: 10px;
                padding: 5px 0;
            }
            
            QLabel#ai-analysis-content {
                background-color: #ffffff;
                border: 2px solid #e1bee7;
                border-radius: 12px;
                padding: 20px;
                color: #4a148c;
                line-height: 1.6;
                font-family: 'Inter', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
        """)
    
    def show_email(self, email: Email):
        """Affiche un email CORRIGÉ avec rendu HTML complet."""
        self.current_email = email
        
        # Cacher le message par défaut, afficher le contenu
        self.no_selection_widget.hide()
        self.email_content_widget.show()
        
        # Mettre à jour le header
        sender_name = email.get_sender_name()
        self.sender_label.setText(sender_name)
        
        self.email_address_label.setText(f"<{email.sender}>")
        
        subject = email.subject or "(Aucun sujet)"
        self.subject_label.setText(subject)
        
        if email.received_date:
            date_str = email.received_date.strftime("%d/%m/%Y à %H:%M")
            self.date_label.setText(date_str)
        else:
            self.date_label.setText("Date inconnue")
        
        # Mettre à jour les pièces jointes
        self._update_attachments()
        
        # Mettre à jour le contenu avec rendu HTML
        body_content = email.body or email.snippet or "(Aucun contenu)"
        is_html = getattr(email, 'is_html', False)
        
        # Définir le contenu dans le display HTML/texte
        self.email_content_display.set_content(body_content, is_html)
        
        # Mettre à jour l'analyse IA
        self._update_ai_analysis()
        
        # Scroller vers le haut
        self.scroll_area.verticalScrollBar().setValue(0)
        
        logger.info(f"Affichage email: {email.id} avec rendu {'HTML' if is_html else 'texte'}")
    
    def _update_attachments(self):
        """Met à jour l'affichage des pièces jointes."""
        # Vider le container existant
        for i in reversed(range(self.attachments_layout.count())):
            item = self.attachments_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        
        if not self.current_email or not self.current_email.has_attachments:
            self.attachments_section.hide()
            return
        
        # Mettre à jour le titre
        count = self.current_email.attachments_count
        total_size = self.current_email._format_total_size()
        
        if count == 1:
            title_text = f"1 pièce jointe ({total_size})"
        else:
            title_text = f"{count} pièces jointes ({total_size})"
        
        self.attachments_title.setText(title_text)
        
        # Créer les cartes de pièces jointes
        for attachment in self.current_email.attachments:
            card = AttachmentCard(attachment)
            card.download_requested.connect(self._download_attachment)
            self.attachments_layout.addWidget(card)
        
        self.attachments_section.show()
    
    def _download_attachment(self, attachment: EmailAttachment):
        """Télécharge une pièce jointe."""
        if not self.gmail_client or not self.current_email:
            QMessageBox.warning(self, "Erreur", "Impossible de télécharger la pièce jointe.")
            return
        
        try:
            # Demander où sauvegarder
            suggested_name = attachment.filename
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder la pièce jointe",
                suggested_name,
                "Tous les fichiers (*.*)"
            )
            
            if not file_path:
                return
            
            # Télécharger et sauvegarder
            success = self.gmail_client.save_attachment(
                self.current_email.id,
                attachment.attachment_id,
                attachment.filename,
                file_path
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Téléchargement réussi",
                    f"La pièce jointe '{attachment.filename}' a été sauvegardée."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur de téléchargement",
                    f"Impossible de télécharger '{attachment.filename}'."
                )
                
        except Exception as e:
            logger.error(f"Erreur téléchargement pièce jointe: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur s'est produite lors du téléchargement:\n{str(e)}"
            )
    
    def _update_ai_analysis(self):
        """Met à jour l'analyse IA."""
        if not self.current_email or not hasattr(self.current_email, 'ai_analysis'):
            self.ai_content.setText("🔍 Aucune analyse IA disponible pour cet email.")
            return
        
        analysis = self.current_email.ai_analysis
        if not analysis:
            self.ai_content.setText("🔍 Aucune analyse IA disponible pour cet email.")
            return
        
        # Construire le texte d'analyse
        category_names = {
            'cv': '📄 Candidature/CV',
            'rdv': '📅 Rendez-vous',
            'support': '🛠️ Support technique',
            'facture': '💰 Facture',
            'spam': '🚫 Spam',
            'general': '📧 Email général'
        }
        
        category_display = category_names.get(getattr(analysis, 'category', 'general'), '📝 Autre')
        confidence = getattr(analysis, 'confidence', 0) * 100
        priority = getattr(analysis, 'priority', 3)
        should_respond = getattr(analysis, 'should_auto_respond', False)
        reasoning = getattr(analysis, 'reasoning', 'Aucun raisonnement disponible')
       
        ai_text = f"""📂 CATÉGORIE DÉTECTÉE
    {category_display}

📊 NIVEAU DE CONFIANCE
    {confidence:.0f}% de certitude

⚡ NIVEAU DE PRIORITÉ
    {self._get_priority_text(priority)}

🤖 RÉPONSE AUTOMATIQUE
    {'✅ Recommandée par l\'IA' if should_respond else '❌ Non recommandée'}

🧠 ANALYSE DÉTAILLÉE
    {reasoning}"""
       
        # Ajouter des informations extraites si disponibles
        extracted_info = getattr(analysis, 'extracted_info', {})
        if extracted_info:
            ai_text += "\n\n📋 INFORMATIONS EXTRAITES"
            for key, value in extracted_info.items():
                if value:
                    ai_text += f"\n• {key.title()}: {value}"
       
        self.ai_content.setText(ai_text)
   
    def _get_priority_text(self, priority: int) -> str:
       """Convertit la priorité en texte."""
       priority_map = {
           1: "🔴 Très urgent (priorité maximale)",
           2: "🟠 Urgent (traitement rapide)", 
           3: "🟡 Normal (priorité standard)",
           4: "🟢 Faible (peut attendre)",
           5: "⚪ Très faible (non prioritaire)"
       }
       return priority_map.get(priority, f"❓ Priorité {priority}")
   
    def clear_selection(self):
       """Efface la sélection."""
       self.current_email = None
       self.email_content_widget.hide()
       self.no_selection_widget.show()
       
       # Scroller vers le haut
       self.scroll_area.verticalScrollBar().setValue(0)