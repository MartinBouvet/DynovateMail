#!/usr/bin/env python3
"""
Vue détaillée d'un email - CHARGEMENT D'IMAGES GARANTI.
"""
import logging
import html
import re
import base64
from typing import Optional, List
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile

from models.email_model import Email, EmailAttachment
from gmail_client import GmailClient

logger = logging.getLogger(__name__)


class EmailDetailView(QWidget):
    """Vue détaillée d'un email - IMAGES GARANTIES."""
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.gmail_client = None
        self._setup_ui()
    
    def set_gmail_client(self, gmail_client: GmailClient):
        """Définit le client Gmail."""
        self.gmail_client = gmail_client
    
    def _setup_ui(self):
        """Configure l'interface avec WebEngine optimisé."""
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
        
        # Contenu email avec WebEngine CONFIGURÉ
        self._create_webengine_section(content_layout)
        
        # Section analyse IA
        self._create_ai_analysis_section(content_layout)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self._apply_styles()
    
    def _create_webengine_section(self, layout):
        """Crée QWebEngineView avec TOUS les paramètres pour charger les images."""
        try:
            # Créer un profil personnalisé pour permettre les images
            self.profile = QWebEngineProfile.defaultProfile()
            
            # ACTIVER TOUTES LES PERMISSIONS IMAGES
            settings = self.profile.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
            
            # Créer WebEngineView
            self.web_view = QWebEngineView()
            self.web_view.setObjectName("email-web-view")
            
            # Appliquer les settings directement à la page
            page_settings = self.web_view.page().settings()
            page_settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            page_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            page_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            page_settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
            
            layout.addWidget(self.web_view)
            logger.info("✅ QWebEngineView créé avec chargement d'images FORCÉ")
            
        except Exception as e:
            logger.error(f"❌ QWebEngineView échoué: {e}")
            # Fallback QTextEdit
            self.web_view = None
            self.fallback_view = QTextEdit()
            self.fallback_view.setReadOnly(True)
            self.fallback_view.setObjectName("email-fallback-view")
            layout.addWidget(self.fallback_view)
    
    def _create_header_section(self, layout):
        """En-tête email."""
        self.header_frame = QFrame()
        self.header_frame.setObjectName("email-header")
        header_layout = QVBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(8)
        
        self.sender_label = QLabel("Sélectionnez un email")
        self.sender_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self.sender_label.setObjectName("email-sender")
        header_layout.addWidget(self.sender_label)
        
        self.address_label = QLabel("")
        self.address_label.setFont(QFont("Inter", 11))
        self.address_label.setObjectName("email-address")
        header_layout.addWidget(self.address_label)
        
        self.subject_label = QLabel("")
        self.subject_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setWordWrap(True)
        header_layout.addWidget(self.subject_label)
        
        self.date_label = QLabel("")
        self.date_label.setFont(QFont("Inter", 10))
        self.date_label.setObjectName("email-date")
        header_layout.addWidget(self.date_label)
        
        layout.addWidget(self.header_frame)
    
    def _create_actions_section(self, layout):
        """Actions email."""
        self.actions_frame = QFrame()
        self.actions_frame.setObjectName("email-actions")
        
        actions_layout = QHBoxLayout(self.actions_frame)
        actions_layout.setContentsMargins(15, 12, 15, 12)
        actions_layout.setSpacing(12)
        
        self.reply_btn = QPushButton("💬 Répondre")
        self.reply_btn.setObjectName("action-btn")
        actions_layout.addWidget(self.reply_btn)
        
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        actions_layout.addWidget(self.forward_btn)
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("delete-btn")
        actions_layout.addWidget(self.delete_btn)
        
        actions_layout.addStretch()
        layout.addWidget(self.actions_frame)
    
    def _create_attachments_section(self, layout):
        """Pièces jointes."""
        self.attachments_frame = QFrame()
        self.attachments_frame.setObjectName("attachments-section")
        self.attachments_frame.hide()
        
        attachments_layout = QVBoxLayout(self.attachments_frame)
        attachments_layout.setContentsMargins(15, 12, 15, 12)
        attachments_layout.setSpacing(8)
        
        attachments_title = QLabel("📎 Pièces jointes")
        attachments_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        attachments_title.setObjectName("section-title")
        attachments_layout.addWidget(attachments_title)
        
        self.attachments_container = QVBoxLayout()
        self.attachments_container.setSpacing(4)
        attachments_layout.addLayout(self.attachments_container)
        
        layout.addWidget(self.attachments_frame)
    
    def _create_ai_analysis_section(self, layout):
        """Analyse IA."""
        self.ai_frame = QFrame()
        self.ai_frame.setObjectName("ai-analysis-frame")
        self.ai_frame.hide()
        
        ai_layout = QVBoxLayout(self.ai_frame)
        ai_layout.setContentsMargins(15, 12, 15, 12)
        ai_layout.setSpacing(8)
        
        ai_title = QLabel("🤖 Analyse IA")
        ai_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        ai_title.setObjectName("section-title")
        ai_layout.addWidget(ai_title)
        
        self.ai_content_label = QLabel("")
        self.ai_content_label.setObjectName("ai-analysis-content")
        self.ai_content_label.setWordWrap(True)
        ai_layout.addWidget(self.ai_content_label)
        
        layout.addWidget(self.ai_frame)
    
    def _apply_styles(self):
        """Styles."""
        self.setStyleSheet("""
            QScrollArea#email-scroll-area {
                border: none;
                background-color: #f8f9fa;
            }
            
            QFrame#email-header {
                background-color: #ffffff;
                border: 3px solid #e3f2fd;
                border-radius: 20px;
            }
            
            QLabel#email-sender {
                color: #1976d2;
                font-weight: 700;
            }
            
            QLabel#email-address {
                color: #607d8b;
                font-style: italic;
            }
            
            QLabel#email-subject {
                color: #1a237e;
                font-weight: 700;
                margin-top: 10px;
                padding: 10px 0;
            }
            
            QLabel#email-date {
                color: #78909c;
            }
            
            QFrame#attachments-section {
                background-color: #fff3e0;
                border: 3px solid #ffcc02;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
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
            }
            
            QPushButton#delete-btn:hover {
                background-color: #c62828;
            }
            
            QWebEngineView#email-web-view {
                border: none;
                background-color: #ffffff;
                min-height: 500px;
            }
            
            QTextEdit#email-fallback-view {
                background-color: #ffffff;
                border: none;
                color: #495057;
                font-family: 'Inter', Arial, sans-serif;
                min-height: 500px;
            }
            
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
        """Affiche email avec images GARANTIES."""
        try:
            self.current_email = email
            
            # En-tête
            sender_name = email.get_sender_name() if hasattr(email, 'get_sender_name') else email.sender
            sender_email = email.get_sender_email() if hasattr(email, 'get_sender_email') else email.sender
            
            self.sender_label.setText(sender_name or "Expéditeur inconnu")
            self.address_label.setText(sender_email or "")
            self.subject_label.setText(email.subject or "Sans sujet")
            
            # Date
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
            
            # Pièces jointes
            self._show_attachments(email.attachments or [])
            
            # CONTENU HTML AVEC IMAGES
            self._show_html_with_images(email)
            
            # Analyse IA
            self._show_ai_analysis(email)
            
            logger.info(f"✅ Email {email.id} affiché")
            
        except Exception as e:
            logger.error(f"❌ Erreur affichage email: {e}")
            self._show_error_message(f"Erreur: {str(e)}")
    
    def _show_html_with_images(self, email: Email):
        """Affiche HTML avec TOUTES les images préchargées."""
        try:
            # Récupérer le contenu
            html_content = ""
            
            if hasattr(email, 'is_html') and email.is_html and email.body:
                html_content = email.body
            elif email.body:
                html_content = f"<p>{html.escape(email.body).replace(chr(10), '<br>')}</p>"
            else:
                html_content = f"<p>{html.escape(email.snippet or 'Contenu non disponible')}</p>"
            
            # PRÉCHARGER TOUTES LES IMAGES EN BASE64
            html_with_images = self._preload_all_images(html_content, email)
            
            # HTML final SANS dépendances externes
            final_html = self._create_standalone_html(html_with_images)
            
            # Afficher
            if self.web_view:
                # Utiliser setHtml avec base URL pour éviter les problèmes de sécurité
                self.web_view.setHtml(final_html, QUrl("https://mail.google.com/"))
                logger.info("✅ HTML chargé dans QWebEngineView avec base URL")
            else:
                self.fallback_view.setHtml(final_html)
                logger.info("✅ HTML chargé dans QTextEdit fallback")
                
        except Exception as e:
            logger.error(f"❌ Erreur affichage HTML: {e}")
            error_html = f"<p style='color: red;'>Erreur d'affichage: {html.escape(str(e))}</p>"
            if self.web_view:
                self.web_view.setHtml(error_html)
            else:
                self.fallback_view.setHtml(error_html)
    
    def _preload_all_images(self, html_content: str, email: Email) -> str:
        """Précharge TOUTES les images en base64 pour éviter les blocages."""
        try:
            import requests
            from urllib.parse import urljoin, urlparse
            
            # Trouver toutes les images
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            images = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            logger.info(f"🔍 Trouvé {len(images)} images à précharger")
            
            for img_url in images:
                try:
                    data_url = None
                    
                    # Gérer les différents types d'URLs
                    if img_url.startswith('data:'):
                        # Déjà en base64, garder tel quel
                        continue
                    elif img_url.startswith('cid:'):
                        # Image intégrée à l'email
                        data_url = self._get_cid_image_data(img_url, email)
                    elif img_url.startswith('http'):
                        # Image externe - télécharger
                        data_url = self._download_external_image(img_url)
                    elif img_url.startswith('//'):
                        # URL sans protocole
                        data_url = self._download_external_image(f"https:{img_url}")
                    elif img_url.startswith('/'):
                        # URL relative - essayer avec différents domaines
                        for domain in ['https://mail.google.com', 'https://ssl.gstatic.com', 'https://www.facebook.com']:
                            data_url = self._download_external_image(f"{domain}{img_url}")
                            if data_url:
                                break
                    
                    # Remplacer dans le HTML si on a récupéré l'image
                    if data_url:
                        html_content = html_content.replace(f'src="{img_url}"', f'src="{data_url}"')
                        html_content = html_content.replace(f"src='{img_url}'", f"src='{data_url}'")
                        logger.info(f"✅ Image préchargée: {img_url[:50]}...")
                    else:
                        logger.warning(f"⚠️ Impossible de précharger: {img_url[:50]}...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur préchargement {img_url[:30]}: {e}")
                    continue
            
            return html_content
            
        except Exception as e:
            logger.error(f"❌ Erreur préchargement images: {e}")
            return html_content
    
    def _download_external_image(self, url: str) -> Optional[str]:
        """Télécharge une image externe et la convertit en base64."""
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Cache-Control': 'no-cache'
            }
            
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            if response.status_code == 200:
                # Détecter le type MIME
                content_type = response.headers.get('content-type', 'image/jpeg')
                if not content_type.startswith('image/'):
                    content_type = 'image/jpeg'
                
                # Convertir en base64
                b64_data = base64.b64encode(response.content).decode()
                return f"data:{content_type};base64,{b64_data}"
            
        except Exception as e:
            logger.debug(f"Impossible de télécharger {url}: {e}")
        
        return None
    
    def _get_cid_image_data(self, cid_url: str, email: Email) -> Optional[str]:
        """Récupère une image CID intégrée à l'email."""
        try:
            cid = cid_url.replace('cid:', '').strip()
            
            if hasattr(email, 'attachments'):
                for att in email.attachments:
                    if hasattr(att, 'content_id') and att.content_id:
                        if att.content_id.strip('<>') == cid:
                            # Télécharger via Gmail API
                            if self.gmail_client:
                                image_data = self.gmail_client.download_attachment(email.id, att.attachment_id)
                                if image_data:
                                    b64_data = base64.b64encode(image_data).decode()
                                    mime_type = att.mime_type or 'image/jpeg'
                                    return f"data:{mime_type};base64,{b64_data}"
            
        except Exception as e:
            logger.error(f"Erreur récupération CID {cid_url}: {e}")
        
        return None
    
    def _create_standalone_html(self, content: str) -> str:
        """Crée un HTML autonome avec toutes les images intégrées."""
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
                }}
                
                .email-content {{
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 25px;
                    margin: 10px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                }}
                
                img {{
                    max-width: 100% !important;
                    height: auto !important;
                    margin: 8px 0;
                    display: block;
                    border-radius: 6px;
                }}
                
                img[style*="display:inline"], img[style*="display: inline"] {{
                    display: inline !important;
                    margin: 0 4px;
                    vertical-align: middle;
                }}
                
                a {{
                    color: #1976d2;
                    text-decoration: none;
                }}
                
                a:hover {{
                    color: #1565c0;
                    text-decoration: underline;
                }}
                
                p {{
                    margin: 12px 0;
                    word-wrap: break-word;
                }}
                
                table {{
                    border-collapse: separate;
                    border-spacing: 0;
                    width: 100%;
                    margin: 15px 0;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #f0f0f0;
                }}
                
                th {{
                    background-color: #f8f9fa;
                    font-weight: 600;
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
    
    def _show_attachments(self, attachments: List[EmailAttachment]):
        """Affiche pièces jointes."""
        try:
            for i in reversed(range(self.attachments_container.count())):
                child = self.attachments_container.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            if attachments and len(attachments) > 0:
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
            else:
                self.attachments_frame.hide()
                
        except Exception as e:
            logger.error(f"Erreur pièces jointes: {e}")
            self.attachments_frame.hide()
    
    def _format_size(self, size_bytes: int) -> str:
        """Formate taille fichier."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _show_ai_analysis(self, email: Email):
        """Affiche analyse IA."""
        try:
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                analysis = email.ai_analysis
                analysis_parts = []
                
                if hasattr(analysis, 'category') and analysis.category:
                    analysis_parts.append(f"📂 Catégorie: {analysis.category}")
                
                if hasattr(analysis, 'priority') and analysis.priority:
                    analysis_parts.append(f"⚡ Priorité: {analysis.priority}")
                
                if hasattr(analysis, 'sentiment') and analysis.sentiment:
                    analysis_parts.append(f"😊 Sentiment: {analysis.sentiment}")
                
                if analysis_parts:
                    analysis_text = '\n'.join(analysis_parts)
                    self.ai_content_label.setText(analysis_text)
                    self.ai_frame.show()
                else:
                    self.ai_frame.hide()
            else:
                self.ai_frame.hide()
                
        except Exception as e:
            logger.error(f"Erreur analyse IA: {e}")
            self.ai_frame.hide()
    
    def _show_error_message(self, message: str):
        """Affiche erreur."""
        self.sender_label.setText("⚠️ Erreur")
        self.address_label.setText("")
        self.subject_label.setText("Impossible d'afficher l'email")
        self.date_label.setText("")
        
        error_html = f"<p style='color: #d32f2f;'>Erreur: {html.escape(message)}</p>"
        
        if self.web_view:
            self.web_view.setHtml(error_html)
        else:
            self.fallback_view.setHtml(error_html)
        
        self.attachments_frame.hide()
        self.ai_frame.hide()
    
    def clear_content(self):
        """Vide contenu."""
        self.current_email = None
        
        self.sender_label.setText("Sélectionnez un email")
        self.address_label.setText("")
        self.subject_label.setText("")
        self.date_label.setText("")
        
        placeholder = "<p style='text-align: center; color: #6c757d; padding: 40px;'>Aucun email sélectionné.</p>"
        
        if self.web_view:
            self.web_view.setHtml(placeholder)
        else:
            self.fallback_view.setHtml(placeholder)
        
        self.attachments_frame.hide()
        self.ai_frame.hide()