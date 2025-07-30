#!/usr/bin/env python3
"""
Vue détaillée d'un email - MODE HTML UNIQUEMENT sans traits de positionnement.
"""
import logging
import html
import re
from typing import Optional, List
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

from models.email_model import Email, EmailAttachment
from gmail_client import GmailClient

logger = logging.getLogger(__name__)


class EmailDetailView(QWidget):
    """Vue détaillée d'un email - MODE HTML UNIQUEMENT."""
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.gmail_client = None
        self._setup_ui()
    
    def set_gmail_client(self, gmail_client: GmailClient):
        """Définit le client Gmail."""
        self.gmail_client = gmail_client
    
    def _setup_ui(self):
        """Configure l'interface - MODE HTML UNIQUEMENT."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone de défilement
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setObjectName("email-scroll-area")
        
        # Widget de contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # En-tête de l'email
        self._create_header_section(content_layout)
        
        # Actions rapides
        self._create_actions_section(content_layout)
        
        # Section pièces jointes
        self._create_attachments_section(content_layout)
        
        # Contenu email en HTML uniquement
        self._create_html_content_section(content_layout)
        
        # Section analyse IA
        self._create_ai_analysis_section(content_layout)
        
        # Stretch pour pousser vers le haut
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Appliquer les styles
        self._apply_styles()
    
    def _create_header_section(self, layout):
        """Crée la section d'en-tête."""
        self.header_frame = QFrame()
        self.header_frame.setObjectName("email-header")
        header_layout = QVBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(8)
        
        # Expéditeur
        self.sender_label = QLabel("Sélectionnez un email")
        self.sender_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self.sender_label.setObjectName("email-sender")
        header_layout.addWidget(self.sender_label)
        
        # Adresse email
        self.address_label = QLabel("")
        self.address_label.setFont(QFont("Inter", 11))
        self.address_label.setObjectName("email-address")
        header_layout.addWidget(self.address_label)
        
        # Sujet
        self.subject_label = QLabel("")
        self.subject_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setWordWrap(True)
        header_layout.addWidget(self.subject_label)
        
        # Date
        self.date_label = QLabel("")
        self.date_label.setFont(QFont("Inter", 10))
        self.date_label.setObjectName("email-date")
        header_layout.addWidget(self.date_label)
        
        layout.addWidget(self.header_frame)
    
    def _create_actions_section(self, layout):
        """Crée la section des actions."""
        self.actions_frame = QFrame()
        self.actions_frame.setObjectName("email-actions")
        
        actions_layout = QHBoxLayout(self.actions_frame)
        actions_layout.setContentsMargins(15, 12, 15, 12)
        actions_layout.setSpacing(12)
        
        # Bouton Répondre
        self.reply_btn = QPushButton("💬 Répondre")
        self.reply_btn.setObjectName("action-btn")
        actions_layout.addWidget(self.reply_btn)
        
        # Bouton Transférer
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        actions_layout.addWidget(self.forward_btn)
        
        # Bouton Supprimer
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("delete-btn")
        actions_layout.addWidget(self.delete_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(self.actions_frame)
    
    def _create_attachments_section(self, layout):
        """Crée la section des pièces jointes."""
        self.attachments_frame = QFrame()
        self.attachments_frame.setObjectName("attachments-section")
        self.attachments_frame.hide()  # Masqué par défaut
        
        attachments_layout = QVBoxLayout(self.attachments_frame)
        attachments_layout.setContentsMargins(15, 12, 15, 12)
        attachments_layout.setSpacing(8)
        
        # Titre de la section
        attachments_title = QLabel("📎 Pièces jointes")
        attachments_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        attachments_title.setObjectName("section-title")
        attachments_layout.addWidget(attachments_title)
        
        # Container pour les pièces jointes
        self.attachments_container = QVBoxLayout()
        self.attachments_container.setSpacing(4)
        attachments_layout.addLayout(self.attachments_container)
        
        layout.addWidget(self.attachments_frame)
    
    def _create_html_content_section(self, layout):
        """Crée la section du contenu HTML UNIQUEMENT."""
        # Vue web pour HTML
        try:
            self.web_view = QWebEngineView()
            self.web_view.setObjectName("email-web-view")
            layout.addWidget(self.web_view)
            logger.info("QWebEngineView créé avec succès")
        except Exception as e:
            logger.error(f"QWebEngineView non disponible: {e}")
            # Fallback avec QTextEdit en mode HTML
            self.web_view = None
            self.fallback_view = QTextEdit()
            self.fallback_view.setReadOnly(True)
            self.fallback_view.setObjectName("email-fallback-view")
            layout.addWidget(self.fallback_view)
    
    def _create_ai_analysis_section(self, layout):
        """Crée la section d'analyse IA."""
        self.ai_frame = QFrame()
        self.ai_frame.setObjectName("ai-analysis-frame")
        self.ai_frame.hide()  # Masqué par défaut
        
        ai_layout = QVBoxLayout(self.ai_frame)
        ai_layout.setContentsMargins(15, 12, 15, 12)
        ai_layout.setSpacing(8)
        
        # Titre de la section
        ai_title = QLabel("🤖 Analyse IA")
        ai_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        ai_title.setObjectName("section-title")
        ai_layout.addWidget(ai_title)
        
        # Contenu de l'analyse
        self.ai_content_label = QLabel("")
        self.ai_content_label.setObjectName("ai-analysis-content")
        self.ai_content_label.setWordWrap(True)
        ai_layout.addWidget(self.ai_content_label)
        
        layout.addWidget(self.ai_frame)
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            QScrollArea#email-scroll-area {
                border: none;
                background-color: #f8f9fa;
            }
            
            QScrollArea#email-scroll-area QScrollBar:vertical {
                background-color: #e9ecef;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollArea#email-scroll-area QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollArea#email-scroll-area QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            
            /* === EN-TÊTE === */
            QFrame#email-header {
                background-color: #ffffff;
                border: 3px solid #e3f2fd;
                border-radius: 20px;
            }
            
            QLabel#email-sender {
                color: #1976d2;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            QLabel#email-date {
                color: #78909c;
                font-weight: 400;
                margin-top: 5px;
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
            }
            
            QWebEngineView#email-web-view {
                border: none;
                background-color: #ffffff;
                min-height: 400px;
            }
            
            QTextEdit#email-fallback-view {
                background-color: #ffffff;
                border: none;
                color: #495057;
                font-family: 'Inter', Arial, sans-serif;
                min-height: 400px;
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
        """Affiche un email en HTML UNIQUEMENT."""
        try:
            self.current_email = email
            
            # Mettre à jour l'en-tête
            sender_name = email.get_sender_name() if hasattr(email, 'get_sender_name') else email.sender
            sender_email = email.get_sender_email() if hasattr(email, 'get_sender_email') else email.sender
            
            self.sender_label.setText(sender_name or "Expéditeur inconnu")
            self.address_label.setText(sender_email or "")
            self.subject_label.setText(email.subject or "Sans sujet")
            
            # Formater la date
            if email.received_date:
                try:
                    if isinstance(email.received_date, str):
                        date_obj = datetime.fromisoformat(email.received_date.replace('Z', '+00:00'))
                    else:
                        date_obj = email.received_date
                    formatted_date = date_obj.strftime("📅 %d/%m/%Y à %H:%M")
                except:
                    formatted_date = f"📅 {email.received_date}"
            else:
                formatted_date = "📅 Date inconnue"
            
            self.date_label.setText(formatted_date)
            
            # Afficher les pièces jointes
            self._show_attachments(email.attachments or [])
            
            # Afficher le contenu en HTML UNIQUEMENT
            self._show_html_content(email)
            
            # Afficher l'analyse IA si disponible
            self._show_ai_analysis(email)
            
            logger.info(f"Email {email.id} affiché en mode HTML")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'email: {e}")
            self._show_error_message(f"Erreur d'affichage: {str(e)}")
    
    def _show_html_content(self, email: Email):
        """Affiche le contenu en HTML avec styles Gmail."""
        try:
            # Déterminer le contenu à afficher
            html_content = ""
            
            if hasattr(email, 'is_html') and email.is_html and email.body:
                html_content = email.body
            elif email.body:
                # Convertir le texte en HTML simple
                html_content = f"<p>{html.escape(email.body).replace(chr(10), '<br>')}</p>"
            else:
                html_content = f"<p>{html.escape(email.snippet or 'Contenu non disponible')}</p>"
            
            # Créer le HTML complet SANS TRAITS
            full_html = self._create_clean_html(html_content)
            
            # Afficher dans WebView ou fallback
            if self.web_view:
                self.web_view.setHtml(full_html)
                logger.info("Contenu affiché dans QWebEngineView")
            else:
                self.fallback_view.setHtml(full_html)
                logger.info("Contenu affiché dans QTextEdit fallback")
                
        except Exception as e:
            logger.error(f"Erreur affichage HTML: {e}")
            # Fallback vers texte simple
            content = email.snippet or "Erreur d'affichage"
            if self.web_view:
                self.web_view.setHtml(f"<p>{html.escape(content)}</p>")
            else:
                self.fallback_view.setPlainText(content)
    
    def _create_clean_html(self, content: str) -> str:
        """Crée un HTML PROPRE avec chargement forcé des images."""
        try:
            # FORCER LE CHARGEMENT DES IMAGES
            # Remplacer les URLs relatives par des URLs absolues
            content = self._fix_image_urls(content)
            
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                        color: #333333;
                        margin: 0;
                        padding: 25px;
                        background-color: #ffffff;
                        max-width: 100%;
                        overflow-x: hidden;
                    }}
                    
                    /* FORCER L'AFFICHAGE DES IMAGES */
                    img {{
                        max-width: 100% !important;
                        height: auto !important;
                        margin: 12px 0;
                        display: block !important;
                        border-radius: 6px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                        /* FORCER LE CHARGEMENT */
                        loading: eager !important;
                        decoding: sync !important;
                    }}
                    
                    /* Images qui ne chargent pas - style de fallback */
                    img[src=""], img[src="#"], img:not([src]) {{
                        display: none !important;
                    }}
                    
                    /* Images cassées - remplacer par placeholder */
                    img[alt]:after {{
                        content: "📷 " attr(alt);
                        background-color: #f0f0f0;
                        padding: 20px;
                        border-radius: 6px;
                        color: #666;
                        font-size: 14px;
                        display: block;
                        text-align: center;
                        border: 2px dashed #ccc;
                    }}
                    
                    /* Images inline/logos */
                    img[style*="display:inline"], img[style*="display: inline"] {{
                        display: inline !important;
                        margin: 0 4px;
                        vertical-align: middle;
                        border-radius: 3px;
                        box-shadow: none;
                        max-height: 50px;
                        width: auto;
                    }}
                    
                    /* Logo Facebook et autres services */
                    img[alt*="Facebook"], img[src*="facebook"], 
                    img[alt*="Logo"], img[src*="logo"],
                    img[alt*="logo"], img[src*="Logo"] {{
                        display: inline !important;
                        margin: 0 8px 0 0;
                        vertical-align: middle;
                        border-radius: 50%;
                        box-shadow: 0 2px 4px rgba(66,103,178,0.3);
                        max-height: 40px;
                        max-width: 40px;
                    }}
                    
                    /* Démarcation visuelle */
                    .email-content {{
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 12px;
                        padding: 25px;
                        margin: 10px 0;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    }}
                    
                    a {{
                        color: #1976d2;
                        text-decoration: none;
                        transition: color 0.2s ease;
                    }}
                    
                    a:hover {{
                        color: #1565c0;
                        text-decoration: underline;
                    }}
                    
                    /* Titres avec démarcation */
                    h1, h2, h3, h4, h5, h6 {{
                        color: #1a237e;
                        margin: 20px 0 12px 0;
                        padding-bottom: 8px;
                        border-bottom: 2px solid #e3f2fd;
                        font-weight: 600;
                    }}
                    
                    p {{
                        margin: 12px 0;
                        word-wrap: break-word;
                        padding: 8px 0;
                    }}
                    
                    /* Tableaux */
                    table {{
                        border-collapse: separate;
                        border-spacing: 0;
                        width: 100%;
                        margin: 15px 0;
                        max-width: 100%;
                        background-color: #ffffff;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }}
                    
                    th, td {{
                        padding: 12px 15px;
                        text-align: left;
                        word-wrap: break-word;
                        border-bottom: 1px solid #f0f0f0;
                    }}
                    
                    th {{
                        background-color: #f8f9fa;
                        font-weight: 600;
                        color: #1a237e;
                        border-bottom: 2px solid #e3f2fd;
                    }}
                    
                    /* Citations */
                    blockquote {{
                        border-left: 4px solid #1976d2;
                        margin: 20px 0;
                        padding: 15px 20px;
                        background-color: #f8fbff;
                        font-style: italic;
                        border-radius: 0 8px 8px 0;
                        box-shadow: 0 1px 3px rgba(25,118,210,0.1);
                    }}
                    
                    /* Masquer les pixels de tracking */
                    img[width="1"], img[height="1"] {{
                        display: none !important;
                    }}
                    
                    /* Styles Outlook */
                    .MsoNormal {{
                        margin: 8px 0 !important;
                        padding: 6px 0 !important;
                    }}
                </style>
            </head>
            <body>
                <div class="email-content">
                    {content}
                </div>
            </body>
            </html>
            """
        except Exception as e:
            logger.error(f"Erreur création HTML: {e}")
            return f"<html><body><p>Erreur d'affichage: {html.escape(str(e))}</p></body></html>"
    
    def _show_attachments(self, attachments: List[EmailAttachment]):
        """Affiche les pièces jointes."""
        try:
            # Nettoyer les anciennes cartes
            for i in reversed(range(self.attachments_container.count())):
                child = self.attachments_container.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            if attachments and len(attachments) > 0:
                # Créer des labels simples pour les pièces jointes
                for attachment in attachments:
                    attachment_label = QLabel(f"📎 {attachment.filename} ({self._format_size(attachment.size_bytes)})")
                    attachment_label.setFont(QFont("Inter", 11))
                    attachment_label.setStyleSheet("""
                        QLabel {
                            background-color: #fff8e1;
                            border: 1px solid #ffb74d;
                            border-radius: 8px;
                            padding: 8px 12px;
                            margin: 2px 0;
                            color: #e65100;
                        }
                    """)
                    self.attachments_container.addWidget(attachment_label)
                
                self.attachments_frame.show()
                logger.info(f"Affichage de {len(attachments)} pièces jointes")
            else:
                self.attachments_frame.hide()
                
        except Exception as e:
            logger.error(f"Erreur affichage pièces jointes: {e}")
            self.attachments_frame.hide()
    
    def _format_size(self, size_bytes: int) -> str:
        """Formate la taille du fichier."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _show_ai_analysis(self, email: Email):
        """Affiche l'analyse IA si disponible."""
        try:
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                analysis = email.ai_analysis
                
                # Construire le texte d'analyse
                analysis_parts = []
                
                if hasattr(analysis, 'category') and analysis.category:
                    analysis_parts.append(f"📂 Catégorie: {analysis.category}")
                
                if hasattr(analysis, 'priority') and analysis.priority:
                    analysis_parts.append(f"⚡ Priorité: {analysis.priority}")
                
                if hasattr(analysis, 'sentiment') and analysis.sentiment:
                    analysis_parts.append(f"😊 Sentiment: {analysis.sentiment}")
                
                if hasattr(analysis, 'summary') and analysis.summary:
                    analysis_parts.append(f"📋 Résumé: {analysis.summary}")
                
                if hasattr(analysis, 'suggested_actions') and analysis.suggested_actions:
                    actions = ', '.join(analysis.suggested_actions)
                    analysis_parts.append(f"💡 Actions suggérées: {actions}")
                
                if analysis_parts:
                    analysis_text = '\n'.join(analysis_parts)
                    self.ai_content_label.setText(analysis_text)
                    self.ai_frame.show()
                    logger.info("Analyse IA affichée")
                else:
                    self.ai_frame.hide()
            else:
                self.ai_frame.hide()
                
        except Exception as e:
            logger.error(f"Erreur affichage analyse IA: {e}")
            self.ai_frame.hide()
    
    def _show_error_message(self, message: str):
        """Affiche un message d'erreur."""
        self.sender_label.setText("⚠️ Erreur")
        self.address_label.setText("")
        self.subject_label.setText("Impossible d'afficher l'email")
        self.date_label.setText("")
        
        error_html = f"<p style='color: #d32f2f; font-size: 14px;'>Erreur: {html.escape(message)}</p>"
        
        if self.web_view:
            self.web_view.setHtml(error_html)
        else:
            self.fallback_view.setHtml(error_html)
        
        self.attachments_frame.hide()
        self.ai_frame.hide()
    
    def clear_content(self):
        """Vide le contenu de la vue."""
        self.current_email = None
        
        self.sender_label.setText("Sélectionnez un email")
        self.address_label.setText("")
        self.subject_label.setText("")
        self.date_label.setText("")
        
        placeholder_html = "<p style='color: #6c757d; text-align: center; padding: 40px;'>Aucun email sélectionné pour l'affichage.</p>"
        
        if self.web_view:
            self.web_view.setHtml(placeholder_html)
        else:
            self.fallback_view.setHtml(placeholder_html)
        
        self.attachments_frame.hide()
        self.ai_frame.hide()
    def _fix_image_urls(self, content: str) -> str:
        """Corrige les URLs des images pour forcer leur chargement."""
        try:
            # Corriger les URLs relatives
            content = re.sub(r'src="\/\/', 'src="https://', content)
            content = re.sub(r"src='\/\/", "src='https://", content)
            
            # Corriger les URLs sans protocole
            content = re.sub(r'src="\/([^"]*)"', r'src="https://\1"', content)
            content = re.sub(r"src='\/([^']*)'", r"src='https://\1'", content)
            
            # Forcer HTTPS pour les images HTTP
            content = re.sub(r'src="http://', 'src="https://', content)
            content = re.sub(r"src='http://", "src='https://", content)
            
            # Ajouter des attributs pour forcer le chargement
            content = re.sub(r'<img ([^>]*?)>', r'<img \1 loading="eager" decoding="sync">', content)
            
            # Gérer les images CID (Content-ID) - images intégrées
            if 'cid:' in content:
                content = self._handle_cid_images(content)
            
            return content
            
        except Exception as e:
            logger.error(f"Erreur correction URLs images: {e}")
            return content
    
    def _handle_cid_images(self, content: str) -> str:
        """Gère les images CID (Content-ID) intégrées à l'email."""
        try:
            if not self.current_email or not self.gmail_client:
                return content
            
            # Trouver toutes les références CID
            cid_pattern = r'src=["\']cid:([^"\']+)["\']'
            cids = re.findall(cid_pattern, content, re.IGNORECASE)
            
            for cid in cids:
                # Chercher la pièce jointe correspondante
                attachment = None
                if hasattr(self.current_email, 'attachments'):
                    for att in self.current_email.attachments:
                        if hasattr(att, 'content_id') and att.content_id:
                            if att.content_id.strip('<>') == cid or att.content_id == cid:
                                attachment = att
                                break
                
                if attachment:
                    try:
                        # Télécharger l'image
                        image_data = self.gmail_client.download_attachment(
                            self.current_email.id, 
                            attachment.attachment_id
                        )
                        
                        if image_data:
                            # Convertir en base64
                            import base64
                            b64_data = base64.b64encode(image_data).decode()
                            
                            # Détecter le type MIME
                            mime_type = attachment.mime_type or 'image/jpeg'
                            
                            # Remplacer dans le contenu
                            data_url = f"data:{mime_type};base64,{b64_data}"
                            content = content.replace(f'cid:{cid}', data_url)
                            
                            logger.info(f"Image CID {cid} intégrée avec succès")
                        else:
                            logger.warning(f"Impossible de télécharger l'image CID {cid}")
                            
                    except Exception as e:
                        logger.error(f"Erreur téléchargement image CID {cid}: {e}")
                        # Remplacer par placeholder
                        placeholder = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2U8L3RleHQ+PC9zdmc+"
                        content = content.replace(f'cid:{cid}', placeholder)
                else:
                    logger.warning(f"Pièce jointe CID {cid} non trouvée")
            
            return content
            
        except Exception as e:
            logger.error(f"Erreur gestion images CID: {e}")
            return content
    def _create_html_content_section(self, layout):
        """Crée la section du contenu HTML avec chargement d'images forcé."""
        # Vue web pour HTML
        try:
            self.web_view = QWebEngineView()
            self.web_view.setObjectName("email-web-view")
            
            # FORCER LE CHARGEMENT DES IMAGES
            from PyQt6.QtWebEngineCore import QWebEngineSettings
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
            
            layout.addWidget(self.web_view)
            logger.info("QWebEngineView créé avec chargement d'images forcé")
        except Exception as e:
            logger.error(f"QWebEngineView non disponible: {e}")
            # Fallback avec QTextEdit en mode HTML
            self.web_view = None
            self.fallback_view = QTextEdit()
            self.fallback_view.setReadOnly(True)
            self.fallback_view.setObjectName("email-fallback-view")
            layout.addWidget(self.fallback_view)