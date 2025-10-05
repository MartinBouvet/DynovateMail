#!/usr/bin/env python3
"""
Vue détaillée d'un email - VERSION CORRIGÉE COMPLÈTE
Corrections: Affichage HTML, pièces jointes, actions fonctionnelles
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
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

from models.email_model import Email, EmailAttachment
from gmail_client import GmailClient

logger = logging.getLogger(__name__)

class EmailDetailView(QWidget):
    """Vue détaillée d'un email avec TOUT fonctionnel."""
    
    # Signaux
    reply_requested = pyqtSignal(object)
    forward_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    ai_response_requested = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.gmail_client = None
        self._setup_ui()
    
    def set_gmail_client(self, gmail_client: GmailClient):
        """Définit le client Gmail."""
        self.gmail_client = gmail_client
    
    def _setup_ui(self):
        """Configure l'interface complète."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone de défilement principale
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
        
        # Pièces jointes
        self._create_attachments_section(content_layout)
        
        # Contenu email (HTML corrigé)
        self._create_html_content_section(content_layout)
        
        # Section analyse IA
        self._create_ai_analysis_section(content_layout)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self._apply_styles()
    
    def _create_header_section(self, layout):
        """Crée l'en-tête avec expéditeur, sujet, date."""
        header_frame = QFrame()
        header_frame.setObjectName("email-header")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Expéditeur
        self.sender_label = QLabel("Sélectionnez un email")
        self.sender_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.sender_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(self.sender_label)
        
        # Email de l'expéditeur
        self.address_label = QLabel("")
        self.address_label.setFont(QFont("Inter", 12))
        self.address_label.setStyleSheet("color: #6c757d;")
        header_layout.addWidget(self.address_label)
        
        # Sujet
        self.subject_label = QLabel("")
        self.subject_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
        self.subject_label.setStyleSheet("color: #495057;")
        self.subject_label.setWordWrap(True)
        header_layout.addWidget(self.subject_label)
        
        # Date
        self.date_label = QLabel("")
        self.date_label.setFont(QFont("Inter", 11))
        self.date_label.setStyleSheet("color: #6c757d;")
        header_layout.addWidget(self.date_label)
        
        layout.addWidget(header_frame)
    
    def _create_actions_section(self, layout):
        """Crée la barre d'actions CORRIGÉE."""
        actions_frame = QFrame()
        actions_frame.setObjectName("actions-bar")
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setSpacing(10)
        actions_layout.setContentsMargins(20, 12, 20, 12)
        
        # Bouton Répondre
        self.reply_btn = QPushButton("↩️ Répondre")
        self.reply_btn.setObjectName("action-btn")
        self.reply_btn.clicked.connect(self._on_reply_clicked)
        self.reply_btn.setEnabled(False)
        actions_layout.addWidget(self.reply_btn)
        
        # Bouton Transférer
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        self.forward_btn.clicked.connect(self._on_forward_clicked)
        self.forward_btn.setEnabled(False)
        actions_layout.addWidget(self.forward_btn)
        
        actions_layout.addStretch()
        
        # Bouton Archiver
        self.archive_btn = QPushButton("📁 Archiver")
        self.archive_btn.setObjectName("action-btn-secondary")
        self.archive_btn.clicked.connect(self._on_archive_clicked)
        self.archive_btn.setEnabled(False)
        actions_layout.addWidget(self.archive_btn)
        
        # Bouton Supprimer
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("action-btn-danger")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)
        
        layout.addWidget(actions_frame)
    
    def _create_attachments_section(self, layout):
        """Section pièces jointes CORRIGÉE."""
        self.attachments_frame = QFrame()
        self.attachments_frame.setObjectName("attachments-section")
        self.attachments_frame.hide()
        
        attachments_layout = QVBoxLayout(self.attachments_frame)
        attachments_layout.setContentsMargins(20, 15, 20, 15)
        attachments_layout.setSpacing(10)
        
        title_label = QLabel("📎 Pièces jointes")
        title_label.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000;")
        attachments_layout.addWidget(title_label)
        
        self.attachments_container = QWidget()
        self.attachments_layout_inner = QVBoxLayout(self.attachments_container)
        self.attachments_layout_inner.setSpacing(8)
        self.attachments_layout_inner.setContentsMargins(0, 0, 0, 0)
        
        attachments_layout.addWidget(self.attachments_container)
        layout.addWidget(self.attachments_frame)
    
    def _create_html_content_section(self, layout):
        """Section contenu email CORRIGÉE."""
        content_frame = QFrame()
        content_frame.setObjectName("email-content")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Utiliser QWebEngineView pour le HTML
        try:
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(400)
            content_layout.addWidget(self.web_view)
            self.fallback_view = None
        except Exception as e:
            logger.warning(f"QWebEngineView non disponible: {e}")
            self.web_view = None
            self.fallback_view = QTextEdit()
            self.fallback_view.setReadOnly(True)
            self.fallback_view.setMinimumHeight(400)
            content_layout.addWidget(self.fallback_view)
        
        layout.addWidget(content_frame)
    
    def _create_ai_analysis_section(self, layout):
        """Section analyse IA CORRIGÉE."""
        self.ai_frame = QFrame()
        self.ai_frame.setObjectName("ai-analysis-section")
        self.ai_frame.hide()
        
        ai_layout = QVBoxLayout(self.ai_frame)
        ai_layout.setContentsMargins(20, 15, 20, 15)
        ai_layout.setSpacing(12)
        
        # Titre
        ai_title = QLabel("🤖 Analyse IA")
        ai_title.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        ai_title.setStyleSheet("color: #000000;")
        ai_layout.addWidget(ai_title)
        
        # Informations d'analyse
        self.ai_info_label = QLabel("")
        self.ai_info_label.setFont(QFont("Inter", 12))
        self.ai_info_label.setStyleSheet("color: #495057;")
        self.ai_info_label.setWordWrap(True)
        ai_layout.addWidget(self.ai_info_label)
        
        # Zone de réponse suggérée
        self.ai_response_frame = QFrame()
        self.ai_response_frame.setObjectName("ai-response-frame")
        self.ai_response_frame.hide()
        
        response_layout = QVBoxLayout(self.ai_response_frame)
        response_layout.setSpacing(10)
        
        response_label = QLabel("💬 Réponse suggérée:")
        response_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        response_label.setStyleSheet("color: #007bff;")
        response_layout.addWidget(response_label)
        
        self.ai_response_text = QTextEdit()
        self.ai_response_text.setReadOnly(True)
        self.ai_response_text.setMaximumHeight(150)
        response_layout.addWidget(self.ai_response_text)
        
        # Bouton pour utiliser la réponse IA
        self.ai_reply_btn = QPushButton("✨ Utiliser cette réponse")
        self.ai_reply_btn.setObjectName("ai-action-btn")
        self.ai_reply_btn.clicked.connect(self._on_ai_reply_clicked)
        response_layout.addWidget(self.ai_reply_btn)
        
        ai_layout.addWidget(self.ai_response_frame)
        layout.addWidget(self.ai_frame)
    
    # === GESTIONNAIRES D'ÉVÉNEMENTS - CORRIGÉS ===
    
    def _on_reply_clicked(self):
        """Émet le signal de réponse."""
        if self.current_email:
            self.reply_requested.emit(self.current_email)
    
    def _on_forward_clicked(self):
        """Émet le signal de transfert."""
        if self.current_email:
            self.forward_requested.emit(self.current_email)
    
    def _on_archive_clicked(self):
        """Archive l'email."""
        if self.current_email and self.gmail_client:
            try:
                success = self.gmail_client.archive_email(self.current_email.id)
                if success:
                    QMessageBox.information(self, "Succès", "Email archivé avec succès")
                    self.clear_content()
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible d'archiver l'email")
            except Exception as e:
                logger.error(f"Erreur archivage: {e}")
                QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
    
    def _on_delete_clicked(self):
        """Émet le signal de suppression."""
        if self.current_email:
            self.delete_requested.emit(self.current_email)
    
    def _on_ai_reply_clicked(self):
        """Utilise la réponse IA suggérée."""
        if self.current_email:
            self.ai_response_requested.emit(self.current_email)
    
    # === AFFICHAGE - CORRIGÉ ===
    
    def show_email(self, email: Email):
        """Affiche un email avec TOUTES ses informations - CORRIGÉ."""
        try:
            self.current_email = email
            
            # Activer tous les boutons
            self.reply_btn.setEnabled(True)
            self.forward_btn.setEnabled(True)
            self.archive_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
            # === EN-TÊTE ===
            sender_name = getattr(email, 'get_sender_name', lambda: email.sender)()
            sender_email = getattr(email, 'get_sender_email', lambda: email.sender)()
            
            self.sender_label.setText(sender_name or "Expéditeur inconnu")
            self.address_label.setText(sender_email or "")
            self.subject_label.setText(email.subject or "Sans sujet")
            
            # Date formatée
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
            
            # === PIÈCES JOINTES ===
            self._show_attachments(email.attachments or [])
            
            # === CONTENU HTML - CORRIGÉ ===
            self._show_html_content(email)
            
            # === ANALYSE IA ===
            self._show_ai_analysis(email)
            
            logger.info(f"Email {email.id} affiché avec succès")
            
        except Exception as e:
            logger.error(f"Erreur affichage email: {e}")
            self._show_error_message(f"Erreur: {str(e)}")
    
    def _show_html_content(self, email: Email):
        """Affiche le contenu HTML - VERSION ULTRA CORRIGÉE avec images."""
        try:
        # Construire le HTML propre
            if hasattr(email, 'is_html') and email.is_html and email.body:
                html_content = email.body
            
            # IMPORTANT: Permettre le chargement des images externes
            # Ne pas filtrer les URLs d'images
            
            elif email.body:
            # Convertir texte brut en HTML
                html_content = f"<p>{html.escape(email.body).replace(chr(10), '<br>')}</p>"
            else:
                html_content = f"<p style='color: #6c757d;'>{html.escape(email.snippet or 'Contenu non disponible')}</p>"
        
        # Template HTML complet avec styles CORRIGÉS
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                        color: #212529 !important;
                        padding: 20px;
                        margin: 0;
                        background-color: #ffffff !important;
                    }}
                
                    /* CORRECTION: Forcer les couleurs de texte */
                    p, div, span, td, th, li {{ 
                        color: #212529 !important;
                    }}
                
                    /* CORRECTION: Texte blanc visible sur fond sombre */
                    *[style*="color: white"],
                    *[style*="color: #fff"],
                    *[style*="color: #ffffff"] {{
                        color: #212529 !important;
                        background-color: #f8f9fa !important;
                        padding: 2px 4px;
                    }}
                
                    /* CORRECTION: Texte noir visible sur fond noir */
                    *[style*="background-color: black"],
                    *[style*="background-color: #000"],
                    *[style*="background: black"],
                    *[style*="background: #000"] {{
                        background-color: #ffffff !important;
                        color: #212529 !important;
                    }}
                
                    p {{ margin: 0 0 10px 0; }}
                    a {{ 
                        color: #007bff !important; 
                        text-decoration: none; 
                    }}
                    a:hover {{ text-decoration: underline; }}
                
                    /* CORRECTION: Images s'affichent correctement */
                    img {{ 
                        max-width: 100% !important; 
                        height: auto !important;
                        display: block;
                        margin: 10px 0;
                    }}
                
                    pre {{ 
                        background-color: #f8f9fa; 
                        padding: 10px; 
                        border-radius: 4px; 
                        overflow-x: auto;
                        color: #212529 !important;
                    }}
                
                    blockquote {{ 
                        border-left: 3px solid #dee2e6; 
                        padding-left: 15px; 
                        color: #6c757d !important;
                        margin: 10px 0;
                    }}
                
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 10px 0;
                    }}
                
                    table td, table th {{
                        padding: 8px;
                        border: 1px solid #dee2e6;
                    }}
                
                    /* Emails marketing */
                    table[bgcolor] {{
                        background-color: transparent !important;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
        
            if self.web_view:
                self.web_view.setHtml(full_html)
            else:
                self.fallback_view.setHtml(full_html)
            
        except Exception as e:
            logger.error(f"Erreur affichage HTML: {e}")
            content = email.snippet or "Erreur d'affichage"
            if self.web_view:
                self.web_view.setHtml(f"<p style='color: #212529;'>{html.escape(content)}</p>")
            else:
                self.fallback_view.setPlainText(content)
    
    def _show_attachments(self, attachments: List[EmailAttachment]):
        """Affiche les pièces jointes - CORRIGÉ."""
        # Vider le container
        while self.attachments_layout_inner.count():
            child = self.attachments_layout_inner.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not attachments:
            self.attachments_frame.hide()
            return
        
        self.attachments_frame.show()
        
        for attachment in attachments:
            att_card = self._create_attachment_card(attachment)
            self.attachments_layout_inner.addWidget(att_card)
    
    def _create_attachment_card(self, attachment: EmailAttachment) -> QFrame:
        """Crée une carte pour une pièce jointe."""
        card = QFrame()
        card.setObjectName("attachment-card")
        card.setStyleSheet("""
            QFrame#attachment-card {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
            }
            QFrame#attachment-card:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setSpacing(10)
        
        # Icône + nom
        name_label = QLabel(f"📎 {attachment.filename}")
        name_label.setFont(QFont("Inter", 12))
        name_label.setStyleSheet("color: #495057;")
        layout.addWidget(name_label)
        
        # Taille
        if attachment.size:
            size_kb = attachment.size / 1024
            size_label = QLabel(f"{size_kb:.1f} KB")
            size_label.setFont(QFont("Inter", 10))
            size_label.setStyleSheet("color: #6c757d;")
            layout.addWidget(size_label)
        
        layout.addStretch()
        
        # Bouton télécharger
        download_btn = QPushButton("⬇️ Télécharger")
        download_btn.setObjectName("download-btn")
        download_btn.clicked.connect(lambda: self._download_attachment(attachment))
        layout.addWidget(download_btn)
        
        return card
    
    def _download_attachment(self, attachment: EmailAttachment):
        """Télécharge une pièce jointe."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer la pièce jointe",
                attachment.filename,
                "Tous les fichiers (*.*)"
            )
            
            if file_path:
                # Récupérer les données
                if hasattr(attachment, 'data') and attachment.data:
                    with open(file_path, 'wb') as f:
                        if isinstance(attachment.data, str):
                            f.write(base64.b64decode(attachment.data))
                        else:
                            f.write(attachment.data)
                    QMessageBox.information(self, "Succès", "Pièce jointe téléchargée")
                else:
                    QMessageBox.warning(self, "Erreur", "Données de la pièce jointe non disponibles")
                    
        except Exception as e:
            logger.error(f"Erreur téléchargement: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
    
    def _show_ai_analysis(self, email: Email):
        """Affiche l'analyse IA - CORRIGÉ."""
        if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
            self.ai_frame.hide()
            return
        
        self.ai_frame.show()
        analysis = email.ai_analysis
        
        # Informations d'analyse
        info_parts = []
        if hasattr(analysis, 'category'):
            info_parts.append(f"📂 Catégorie: {analysis.category}")
        if hasattr(analysis, 'priority'):
            info_parts.append(f"⚠️ Priorité: {analysis.priority}/5")
        if hasattr(analysis, 'sentiment'):
            info_parts.append(f"😊 Sentiment: {analysis.sentiment}")
        
        self.ai_info_label.setText(" | ".join(info_parts))
        
        # Réponse suggérée
        if hasattr(analysis, 'suggested_response') and analysis.suggested_response:
            self.ai_response_frame.show()
            self.ai_response_text.setPlainText(analysis.suggested_response)
            self.ai_reply_btn.setEnabled(True)
        else:
            self.ai_response_frame.hide()
    
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
        
        # Désactiver les boutons
        self.reply_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.archive_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
    
    def clear_content(self):
        """Vide le contenu de la vue."""
        self.current_email = None
        
        self.sender_label.setText("Sélectionnez un email")
        self.address_label.setText("")
        self.subject_label.setText("")
        self.date_label.setText("")
        
        placeholder = "<p style='color: #6c757d; text-align: center; padding: 40px;'>Aucun email sélectionné</p>"
        
        if self.web_view:
            self.web_view.setHtml(placeholder)
        else:
            self.fallback_view.setHtml(placeholder)
        
        self.attachments_frame.hide()
        self.ai_frame.hide()
        
        # Désactiver les boutons
        self.reply_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.archive_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            /* Scroll Area */
            QScrollArea#email-scroll-area {
                border: none;
                background-color: #ffffff;
            }
            
            /* Header */
            QFrame#email-header {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            
            /* Actions Bar */
            QFrame#actions-bar {
                background-color: #ffffff;
                border-bottom: 1px solid #dee2e6;
            }
            
            QPushButton#action-btn, QPushButton#action-btn-secondary, QPushButton#action-btn-danger {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                min-width: 100px;
            }
            
            QPushButton#action-btn {
                background-color: #007bff;
                color: white;
            }
            QPushButton#action-btn:hover { background-color: #0056b3; }
            QPushButton#action-btn:disabled { background-color: #6c757d; opacity: 0.5; }
            
            QPushButton#action-btn-secondary {
                background-color: #6c757d;
                color: white;
            }
            QPushButton#action-btn-secondary:hover { background-color: #545b62; }
            
            QPushButton#action-btn-danger {
                background-color: #dc3545;
                color: white;
            }
            QPushButton#action-btn-danger:hover { background-color: #c82333; }
            
            /* Content */
            QFrame#email-content {
                background-color: #ffffff;
                border: none;
            }
            
            /* Attachments */
QFrame#attachments-section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 10px 0;
            }
            
            QPushButton#download-btn {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton#download-btn:hover { background-color: #218838; }
            
            /* AI Analysis */
            QFrame#ai-analysis-section {
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                border-radius: 8px;
                margin: 10px 0;
            }
            
            QFrame#ai-response-frame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
            
            QPushButton#ai-action-btn {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton#ai-action-btn:hover { background-color: #0056b3; }
            
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                background-color: #f8f9fa;
                font-size: 13px;
            }
        """)