"""
Interface utilisateur principale pour l'application Gmail Assistant.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QLabel, QTextEdit, QComboBox, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from gmail_client import GmailClient
from models.email_model import Email
from ui.email_view import EmailView
from ui.compose_view import ComposeView

logger = logging.getLogger(__name__)

class EmailLoaderThread(QThread):
    """Thread pour charger les emails en arrière-plan."""
    emails_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, gmail_client, query=""):
        super().__init__()
        self.gmail_client = gmail_client
        self.query = query
    
    def run(self):
        try:
            emails = self.gmail_client.list_messages(query=self.query)
            self.emails_loaded.emit(emails)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des emails: {e}")
            self.error_occurred.emit(str(e))

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""
    
    def __init__(self, gmail_client: GmailClient, config: dict):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.config = config
        self.emails = []
        
        self.setWindowTitle("Gmail Assistant IA")
        self.setGeometry(100, 100, 1200, 800)
        
        self._setup_ui()
        self._load_emails()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Widget principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Bouton de rafraîchissement
        refresh_button = QPushButton("Rafraîchir")
        refresh_button.clicked.connect(self._load_emails)
        toolbar_layout.addWidget(refresh_button)
        
        # Filtre de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher des emails...")
        self.search_input.returnPressed.connect(self._search_emails)
        toolbar_layout.addWidget(self.search_input)
        
        # Filtre par catégorie
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Tous", "Non lus", "Importants", "Envoyés"])
        self.category_filter.currentIndexChanged.connect(self._filter_emails)
        toolbar_layout.addWidget(self.category_filter)
        
        # Bouton de composition
        compose_button = QPushButton("Nouveau message")
        compose_button.clicked.connect(self._open_compose_window)
        toolbar_layout.addWidget(compose_button)
        
        main_layout.addLayout(toolbar_layout)
        
        # Splitter pour diviser la liste des emails et le contenu
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Liste des emails
        self.email_list = QListWidget()
        self.email_list.setMinimumWidth(300)
        self.email_list.currentItemChanged.connect(self._email_selected)
        splitter.addWidget(self.email_list)
        
        # Vue de l'email
        self.email_view = EmailView()
        splitter.addWidget(self.email_view)
        
        # Ajouter le splitter au layout principal
        main_layout.addWidget(splitter)
        
        # Barre de statut
        self.statusBar().showMessage("Prêt")
    
    def _load_emails(self):
        """Charge les emails depuis Gmail."""
        self.statusBar().showMessage("Chargement des emails...")
        
        # Désactiver l'interface pendant le chargement
        self.setEnabled(False)
        
        # Créer et démarrer le thread de chargement
        self.loader_thread = EmailLoaderThread(self.gmail_client)
        self.loader_thread.emails_loaded.connect(self._on_emails_loaded)
        self.loader_thread.error_occurred.connect(self._on_load_error)
        self.loader_thread.finished.connect(lambda: self.setEnabled(True))
        self.loader_thread.start()
    
    def _on_emails_loaded(self, emails):
        """Callback appelé lorsque les emails sont chargés."""
        self.emails = emails
        self._update_email_list()
        self.statusBar().showMessage(f"{len(emails)} emails chargés")
    
    def _on_load_error(self, error_message):
        """Callback appelé en cas d'erreur lors du chargement."""
        QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des emails : {error_message}")
        self.statusBar().showMessage("Erreur lors du chargement des emails")
    
    def _update_email_list(self):
        """Met à jour la liste des emails dans l'interface."""
        self.email_list.clear()
        
        for email in self.emails:
            item = QListWidgetItem()
            
            # Créer le texte de l'item
            sender = email.get_sender_name()
            subject = email.subject
            snippet = email.snippet[:50] + "..." if len(email.snippet) > 50 else email.snippet
            
            item.setText(f"{sender}\n{subject}\n{snippet}")
            item.setData(Qt.ItemDataRole.UserRole, email.id)
            
            # Mettre en gras si non lu
            if email.is_unread:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.email_list.addItem(item)
    
    def _email_selected(self, current, previous):
        """Callback appelé lorsqu'un email est sélectionné dans la liste."""
        if current is None:
            return
        
        email_id = current.data(Qt.ItemDataRole.UserRole)
        email = next((e for e in self.emails if e.id == email_id), None)
        
        if email:
            self.email_view.display_email(email)
    
    def _search_emails(self):
        """Recherche des emails correspondant au texte saisi."""
        query = self.search_input.text()
        self.statusBar().showMessage(f"Recherche de '{query}'...")
        
        # Désactiver l'interface pendant la recherche
        self.setEnabled(False)
        
        # Créer et démarrer le thread de recherche
        self.loader_thread = EmailLoaderThread(self.gmail_client, query=query)
        self.loader_thread.emails_loaded.connect(self._on_emails_loaded)
        self.loader_thread.error_occurred.connect(self._on_load_error)
        self.loader_thread.finished.connect(lambda: self.setEnabled(True))
        self.loader_thread.start()
    
    def _filter_emails(self, index):
        """Filtre les emails selon la catégorie sélectionnée."""
        category = self.category_filter.currentText()
        
        if category == "Tous":
            filtered_emails = self.emails
        elif category == "Non lus":
            filtered_emails = [e for e in self.emails if e.is_unread]
        elif category == "Importants":
            filtered_emails = [e for e in self.emails if e.is_important]
        elif category == "Envoyés":
            filtered_emails = [e for e in self.emails if e.is_sent]
        else:
            filtered_emails = self.emails
        
        self.email_list.clear()
        
        for email in filtered_emails:
            item = QListWidgetItem()
            
            # Créer le texte de l'item
            sender = email.get_sender_name()
            subject = email.subject
            snippet = email.snippet[:50] + "..." if len(email.snippet) > 50 else email.snippet
            
            item.setText(f"{sender}\n{subject}\n{snippet}")
            item.setData(Qt.ItemDataRole.UserRole, email.id)
            
            # Mettre en gras si non lu
            if email.is_unread:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.email_list.addItem(item)
        
        self.statusBar().showMessage(f"{len(filtered_emails)} emails dans la catégorie '{category}'")
    
    def _open_compose_window(self):
        """Ouvre la fenêtre de composition d'un nouvel email."""
        compose_window = ComposeView(self.gmail_client, parent=self)
        compose_window.email_sent.connect(self._on_email_sent)
        compose_window.show()
    
    def _on_email_sent(self):
        """Callback appelé lorsqu'un email est envoyé."""
        self.statusBar().showMessage("Email envoyé avec succès")
        self._load_emails()  # Rafraîchir la liste des emails