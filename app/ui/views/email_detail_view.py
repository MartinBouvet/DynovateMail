#!/usr/bin/env python3
"""
Vue détaillée d'un email CORRIGÉE avec toutes les actions fonctionnelles.
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
    """Vue détaillée d'un email avec TOUTES les actions fonctionnelles."""
    
    # Signaux pour communiquer avec la fenêtre principale
    reply_requested = pyqtSignal(object)  # Email à répondre
    forward_requested = pyqtSignal(object)  # Email à transférer
    delete_requested = pyqtSignal(object)  # Email à supprimer
    ai_response_requested = pyqtSignal(object)  # Email pour réponse IA
    
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
        
        # Actions rapides - CORRIGÉES
        self._create_actions_section(content_layout)
        
        # Section pièces jointes
        self._create_attachments_section(content_layout)
        
        # Contenu email en HTML
        self._create_html_content_section(content_layout)
        
        # Section analyse IA - CORRIGÉE
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
        """Crée la section des actions FONCTIONNELLES."""
        self.actions_frame = QFrame()
        self.actions_frame.setObjectName("email-actions")
        
        actions_layout = QHBoxLayout(self.actions_frame)
        actions_layout.setContentsMargins(15, 12, 15, 12)
        actions_layout.setSpacing(12)
        
        # Bouton Répondre - FONCTIONNEL
        self.reply_btn = QPushButton("💬 Répondre")
        self.reply_btn.setObjectName("action-btn")
        self.reply_btn.clicked.connect(self._on_reply_clicked)
        self.reply_btn.setEnabled(False)
        actions_layout.addWidget(self.reply_btn)
        
        # Bouton Réponse IA - NOUVEAU FONCTIONNEL
        self.ai_reply_btn = QPushButton("🤖 Réponse IA")
        self.ai_reply_btn.setObjectName("ai-btn")
        self.ai_reply_btn.clicked.connect(self._on_ai_reply_clicked)
        self.ai_reply_btn.setEnabled(False)
        self.ai_reply_btn.hide()  # Caché par défaut
        actions_layout.addWidget(self.ai_reply_btn)
        
        # Bouton Transférer - FONCTIONNEL
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        self.forward_btn.clicked.connect(self._on_forward_clicked)
        self.forward_btn.setEnabled(False)
        actions_layout.addWidget(self.forward_btn)
        
        # Bouton Archiver - FONCTIONNEL
        self.archive_btn = QPushButton("📦 Archiver")
        self.archive_btn.setObjectName("archive-btn")
        self.archive_btn.clicked.connect(self._on_archive_clicked)
        self.archive_btn.setEnabled(False)
        actions_layout.addWidget(self.archive_btn)
        
        # Bouton Supprimer - FONCTIONNEL
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("delete-btn")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(self.actions_frame)
    
    def _create_attachments_section(self, layout):
        """Crée la section des pièces jointes."""
        self.attachments_frame = QFrame()
        self.attachments_frame.setObjectName("attachments-section")
        self.attachments_frame.hide()
        
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
        """Crée la section du contenu HTML."""
        try:
            self.web_view = QWebEngineView()
            self.web_view.setObjectName("email-web-view")
            
            # Configuration pour forcer le chargement des images
            from PyQt6.QtWebEngineCore import QWebEngineSettings
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            
            layout.addWidget(self.web_view)
            logger.info("QWebEngineView créé avec succès")
        except Exception as e:
            logger.error(f"QWebEngineView non disponible: {e}")
            self.web_view = None
            self.fallback_view = QTextEdit()
            self.fallback_view.setReadOnly(True)
            self.fallback_view.setObjectName("email-fallback-view")
            layout.addWidget(self.fallback_view)
    
    def _create_ai_analysis_section(self, layout):
        """Crée la section d'analyse IA AMÉLIORÉE."""
        self.ai_frame = QFrame()
        self.ai_frame.setObjectName("ai-analysis-frame")
        self.ai_frame.hide()
        
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
        
        # Réponse suggérée par l'IA
        self.ai_response_frame = QFrame()
        self.ai_response_frame.setObjectName("ai-response-frame")
        self.ai_response_frame.hide()
        
        response_layout = QVBoxLayout(self.ai_response_frame)
        response_layout.setContentsMargins(10, 10, 10, 10)
        response_layout.setSpacing(8)
        
        response_title = QLabel("✉️ Réponse suggérée:")
        response_title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        response_layout.addWidget(response_title)
        
        self.ai_response_text = QTextEdit()
        self.ai_response_text.setObjectName("ai-response-text")
        self.ai_response_text.setMaximumHeight(150)
        self.ai_response_text.setReadOnly(True)
        response_layout.addWidget(self.ai_response_text)
        
        # Boutons pour la réponse IA
        response_buttons = QHBoxLayout()
        
        self.edit_ai_response_btn = QPushButton("✏️ Modifier")
        self.edit_ai_response_btn.clicked.connect(self._on_edit_ai_response)
        response_buttons.addWidget(self.edit_ai_response_btn)
        
        self.send_ai_response_btn = QPushButton("📤 Envoyer")
        self.send_ai_response_btn.clicked.connect(self._on_send_ai_response)
        response_buttons.addWidget(self.send_ai_response_btn)
        
        response_buttons.addStretch()
        response_layout.addLayout(response_buttons)
        
        ai_layout.addWidget(self.ai_response_frame)
        layout.addWidget(self.ai_frame)
    
    # === MÉTHODES D'ACTION FONCTIONNELLES ===
    
    def _on_reply_clicked(self):
        """Gère le clic sur Répondre."""
        if not self.current_email:
            return
        
        logger.info(f"Répondre à l'email: {self.current_email.id}")
        self.reply_requested.emit(self.current_email)
    
    def _on_ai_reply_clicked(self):
        """Gère le clic sur Réponse IA."""
        if not self.current_email:
            return
        
        logger.info(f"Réponse IA demandée pour l'email: {self.current_email.id}")
        self.ai_response_requested.emit(self.current_email)
    
    def _on_forward_clicked(self):
        """Gère le clic sur Transférer."""
        if not self.current_email:
            return
        
        logger.info(f"Transférer l'email: {self.current_email.id}")
        self.forward_requested.emit(self.current_email)
    
    def _on_archive_clicked(self):
        """Gère le clic sur Archiver."""
        if not self.current_email or not self.gmail_client:
            return
        
        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer l'archivage",
            f"Êtes-vous sûr de vouloir archiver cet email ?\n\n{self.current_email.subject}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.gmail_client.archive_email(self.current_email.id)
                if success:
                    QMessageBox.information(self, "Succès", "Email archivé avec succès!")
                    logger.info(f"Email archivé: {self.current_email.id}")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible d'archiver l'email.")
            except Exception as e:
                logger.error(f"Erreur archivage: {e}")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'archivage: {str(e)}")
    
    def _on_delete_clicked(self):
        """Gère le clic sur Supprimer."""
        if not self.current_email:
            return
        
        logger.info(f"Supprimer l'email: {self.current_email.id}")
        self.delete_requested.emit(self.current_email)
    
    def _on_edit_ai_response(self):
        """Permet de modifier la réponse IA."""
        if self.ai_response_text.isReadOnly():
            self.ai_response_text.setReadOnly(False)
            self.edit_ai_response_btn.setText("💾 Sauvegarder")
            self.ai_response_text.setStyleSheet("""
                QTextEdit#ai-response-text {
                    background-color: #fff3e0;
                    border: 2px solid #ff9800;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
        else:
            self.ai_response_text.setReadOnly(True)
            self.edit_ai_response_btn.setText("✏️ Modifier")
            self.ai_response_text.setStyleSheet("")
    
    def _on_send_ai_response(self):
        """Envoie la réponse IA."""
        if not self.current_email or not self.ai_response_text.toPlainText().strip():
            return
        
        response_text = self.ai_response_text.toPlainText().strip()
        
        # Créer le sujet de réponse
        original_subject = self.current_email.subject or ""
        if not original_subject.lower().startswith("re:"):
            reply_subject = f"Re: {original_subject}"
        else:
            reply_subject = original_subject
        
        # Ouvrir la fenêtre de composition avec la réponse pré-remplie
        from ui.compose_view import ComposeView
        
        compose_dialog = ComposeView(
            gmail_client=self.gmail_client,
            parent=self,
            to=self.current_email.get_sender_email(),
            subject=reply_subject,
            body=response_text,
            is_reply=True
        )
        
        # Indiquer que c'est une réponse IA
        compose_dialog.show_ai_indicator()
        
        if compose_dialog.exec() == compose_dialog.DialogCode.Accepted:
            logger.info("Réponse IA envoyée")
            # Cacher le bouton après envoi
            self.ai_reply_btn.hide()
            self.ai_response_frame.hide()
    
    # === MÉTHODES D'AFFICHAGE ===
    
    def show_email(self, email: Email):
        """Affiche un email avec toutes ses informations."""
        try:
            self.current_email = email
            
            # Activer tous les boutons
            self.reply_btn.setEnabled(True)
            self.forward_btn.setEnabled(True)
            self.archive_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
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
            
            # Afficher le contenu
            self._show_html_content(email)
            
            # Afficher l'analyse IA
            self._show_ai_analysis(email)
            
            logger.info(f"Email {email.id} affiché")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'email: {e}")
            self._show_error_message(f"Erreur d'affichage: {str(e)}")
    
    def _show_html_content(self, email: Email):
        """Affiche le contenu HTML."""
        try:
            html_content = ""
            
            if hasattr(email, 'is_html') and email.is_html and email.body:
                html_content = email.body
            elif email.body:
                html_content = f"<p>{html.escape(email.body).replace(chr(10), '<br>')}</p>"
            else:
                html_content = f"<p>{html.escape(email.snippet or 'Contenu non disponible')}</p>"
            
            full_html = self._create_clean_html(html_content)
            
            if self.web_view:
                self.web_view.setHtml(full_html)
            else:
                self.fallback_view.setHtml(full_html)
                
        except Exception as e:
            logger.error(f"Erreur affichage HTML: {e}")
            content = email.snippet or "Erreur d'affichage"
            if self.web_view:
                self.web_view.setHtml(f"<p>{html.escape(content)}</p>")
            else:
                self.fallback_view.setPlainText(content)
    
    def _show_attachments(self, attachments: List[EmailAttachment]):
        """Affiche les pièces jointes avec bouton de téléchargement."""
        try:
            # Nettoyer les anciennes cartes
            for i in reversed(range(self.attachments_container.count())):
                child = self.attachments_container.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            if attachments and len(attachments) > 0:
                for attachment in attachments:
                    # Container pour chaque pièce jointe
                    att_container = QFrame()
                    att_layout = QHBoxLayout(att_container)
                    att_layout.setContentsMargins(5, 5, 5, 5)
                    
                    # Info pièce jointe
                    att_label = QLabel(f"{attachment.icon} {attachment.filename}")
                    att_label.setFont(QFont("Inter", 11))
                    att_layout.addWidget(att_label)
                    
                    # Taille
                    size_label = QLabel(f"({attachment.size})")
                    size_label.setFont(QFont("Inter", 9))
                    size_label.setStyleSheet("color: #666;")
                    att_layout.addWidget(size_label)
                    
                    att_layout.addStretch()
                    
                    # Bouton télécharger
                    download_btn = QPushButton("💾")
                    download_btn.setFixedSize(30, 25)
                    download_btn.setToolTip("Télécharger")
                    download_btn.clicked.connect(
                        lambda checked, att=attachment: self._download_attachment(att)
                    )
                    att_layout.addWidget(download_btn)
                    
                    att_container.setStyleSheet("""
                        QFrame {
                            background-color: #fff8e1;
                            border: 1px solid #ffb74d;
                            border-radius: 8px;
                            margin: 2px 0;
                        }
                        QPushButton {
                            background-color: #ff9800;
                            color: white;
                            border: none;
                            border-radius: 4px;
                        }
                        QPushButton:hover {
                            background-color: #f57c00;
                        }
                    """)
                    
                    self.attachments_container.addWidget(att_container)
                
                self.attachments_frame.show()
                logger.info(f"Affichage de {len(attachments)} pièces jointes")
            else:
                self.attachments_frame.hide()
                
        except Exception as e:
            logger.error(f"Erreur affichage pièces jointes: {e}")
            self.attachments_frame.hide()
    
    def _download_attachment(self, attachment: EmailAttachment):
        """Télécharge une pièce jointe."""
        if not self.current_email or not self.gmail_client:
            return
        
        try:
            # Demander où sauvegarder
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder la pièce jointe",
                attachment.filename,
                "Tous les fichiers (*.*)"
            )
            
            if save_path:
                success = self.gmail_client.save_attachment(
                    self.current_email.id,
                    attachment.attachment_id,
                    attachment.filename,
                    save_path
                )
                
                if success:
                    QMessageBox.information(
                        self,
                        "Téléchargement réussi",
                        f"La pièce jointe a été sauvegardée :\n{save_path}"
                    )
                    logger.info(f"Pièce jointe téléchargée: {attachment.filename}")
                else:
                    QMessageBox.warning(
                        self,
                        "Erreur",
                        "Impossible de télécharger la pièce jointe."
                    )
        
        except Exception as e:
            logger.error(f"Erreur téléchargement pièce jointe: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors du téléchargement: {str(e)}"
            )
    
    def _show_ai_analysis(self, email: Email):
        """Affiche l'analyse IA avec réponse suggérée."""
        try:
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                analysis = email.ai_analysis
                
                # Construire le texte d'analyse
                analysis_parts = []
                
                if hasattr(analysis, 'category') and analysis.category:
                    analysis_parts.append(f"📂 Catégorie: {analysis.category}")
                
                if hasattr(analysis, 'confidence') and analysis.confidence:
                    confidence_percent = int(analysis.confidence * 100)
                    analysis_parts.append(f"🎯 Confiance: {confidence_percent}%")
                
                if hasattr(analysis, 'priority') and analysis.priority:
                    priority_text = {1: "🔥 Très urgent", 2: "⚡ Urgent", 3: "📋 Normal", 4: "📉 Faible", 5: "💤 Très faible"}
                    analysis_parts.append(f"Priorité: {priority_text.get(analysis.priority, str(analysis.priority))}")
                
                if hasattr(analysis, 'reasoning') and analysis.reasoning:
                    analysis_parts.append(f"🧠 Raisonnement: {analysis.reasoning}")
                
                if analysis_parts:
                    analysis_text = '\n'.join(analysis_parts)
                    self.ai_content_label.setText(analysis_text)
                    self.ai_frame.show()
                
                # Afficher la réponse suggérée
                if hasattr(analysis, 'suggested_response') and analysis.suggested_response:
                    if hasattr(analysis, 'should_auto_respond') and analysis.should_auto_respond:
                        self.ai_response_text.setPlainText(analysis.suggested_response)
                        self.ai_response_frame.show()
                        self.ai_reply_btn.show()
                        self.ai_reply_btn.setEnabled(True)
                        logger.info("Réponse IA disponible")
                    else:
                        self.ai_response_frame.hide()
                        self.ai_reply_btn.hide()
                else:
                    self.ai_response_frame.hide()
                    self.ai_reply_btn.hide()
            else:
                self.ai_frame.hide()
                self.ai_reply_btn.hide()
                
        except Exception as e:
            logger.error(f"Erreur affichage analyse IA: {e}")
            self.ai_frame.hide()
            self.ai_reply_btn.hide()
    
    def _create_clean_html(self, content: str) -> str:
        """Crée un HTML propre."""
        try:
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
                    
                    img {{
                        max-width: 100% !important;
                        height: auto !important;
                        margin: 12px 0;
                        display: block !important;
                        border-radius: 6px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                    }}
                    
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
                    }}
                    
                    a:hover {{
                        color: #1565c0;
                        text-decoration: underline;
                    }}
                    
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
                    
                    blockquote {{
                        border-left: 4px solid #1976d2;
                        margin: 20px 0;
                        padding: 15px 20px;
                        background-color: #f8fbff;
                        font-style: italic;
                        border-radius: 0 8px 8px 0;
                        box-shadow: 0 1px 3px rgba(25,118,210,0.1);
                    }}
                    
                    img[width="1"], img[height="1"] {{
                        display: none !important;
                    }}
                    
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
    
    def _fix_image_urls(self, content: str) -> str:
        """Corrige les URLs des images."""
        try:
            content = re.sub(r'src="\/\/', 'src="https://', content)
            content = re.sub(r"src='\/\/", "src='https://", content)
            content = re.sub(r'src="\/([^"]*)"', r'src="https://\1"', content)
            content = re.sub(r"src='\/([^']*)'", r"src='https://\1'", content)
            content = re.sub(r'src="http://', 'src="https://', content)
            content = re.sub(r"src='http://", "src='https://", content)
            content = re.sub(r'<img ([^>]*?)>', r'<img \1 loading="eager" decoding="sync">', content)
            
            if 'cid:' in content:
                content = self._handle_cid_images(content)
            
            return content
        except Exception as e:
            logger.error(f"Erreur correction URLs images: {e}")
            return content
    
    def _handle_cid_images(self, content: str) -> str:
        """Gère les images CID intégrées."""
        try:
            if not self.current_email or not self.gmail_client:
                return content
            
            cid_pattern = r'src=["\']cid:([^"\']+)["\']'
            cids = re.findall(cid_pattern, content, re.IGNORECASE)
            
            for cid in cids:
                attachment = None
                if hasattr(self.current_email, 'attachments'):
                    for att in self.current_email.attachments:
                        if hasattr(att, 'content_id') and att.content_id:
                            if att.content_id.strip('<>') == cid or att.content_id == cid:
                                attachment = att
                                break
                
                if attachment:
                    try:
                        image_data = self.gmail_client.download_attachment(
                            self.current_email.id, 
                            attachment.attachment_id
                        )
                        
                        if image_data:
                            import base64
                            b64_data = base64.b64encode(image_data).decode()
                            mime_type = attachment.mime_type or 'image/jpeg'
                            data_url = f"data:{mime_type};base64,{b64_data}"
                            content = content.replace(f'cid:{cid}', data_url)
                            logger.info(f"Image CID {cid} intégrée avec succès")
                        else:
                            logger.warning(f"Impossible de télécharger l'image CID {cid}")
                    except Exception as e:
                        logger.error(f"Erreur téléchargement image CID {cid}: {e}")
                        placeholder = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2U8L3RleHQ+PC9zdmc+"
                        content = content.replace(f'cid:{cid}', placeholder)
                else:
                    logger.warning(f"Pièce jointe CID {cid} non trouvée")
            
            return content
        except Exception as e:
            logger.error(f"Erreur gestion images CID: {e}")
            return content
    
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
        
        # Désactiver tous les boutons
        self.reply_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.archive_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.ai_reply_btn.setEnabled(False)
    
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
        self.ai_reply_btn.hide()
        
        # Désactiver tous les boutons
        self.reply_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.archive_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.ai_reply_btn.setEnabled(False)
    
    def _apply_styles(self):
        """Applique les styles complets."""
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
                text-align: center;
                margin: 0px;
                min-width: 100px;
            }
            
            QPushButton#action-btn:hover {
                background-color: #1565c0;
            }
            
            QPushButton#action-btn:disabled {
                background-color: #bdbdbd;
                color: #757575;
            }
            
            QPushButton#ai-btn {
                background-color: #9c27b0;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;
                min-width: 120px;
            }
            
            QPushButton#ai-btn:hover {
                background-color: #7b1fa2;
            }
            
            QPushButton#ai-btn:disabled {
                background-color: #bdbdbd;
                color: #757575;
            }
            
            QPushButton#archive-btn {
                background-color: #ff9800;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;
                min-width: 100px;
            }
            
            QPushButton#archive-btn:hover {
                background-color: #f57c00;
            }
            
            QPushButton#archive-btn:disabled {
                background-color: #bdbdbd;
                color: #757575;
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
                min-width: 100px;
            }
            
            QPushButton#delete-btn:hover {
                background-color: #c62828;
            }
            
            QPushButton#delete-btn:disabled {
                background-color: #bdbdbd;
                color: #757575;
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
            
            QFrame#ai-analysis-frame {
                background-color: #f3e5f5;
                border: 3px solid #ce93d8;
                border-radius: 15px;
                margin-bottom: 20px;
            }
            
            QFrame#ai-response-frame {
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
                border-radius: 10px;
                margin-top: 10px;
                padding: 5px;
            }
            
            QTextEdit#ai-response-text {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Inter', Arial, sans-serif;
                font-size: 13px;
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