"""
Utilitaires pour l'authentification OAuth avec Google.
"""
import os
import logging
import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

# Définition des scopes d'accès à l'API Gmail
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Lecture des emails
    'https://www.googleapis.com/auth/gmail.send',      # Envoi d'emails
    'https://www.googleapis.com/auth/gmail.modify',    # Modification des emails (labels, etc.)
]

def authenticate_gmail() -> Optional[Credentials]:
    """
    Authentifie l'utilisateur auprès de l'API Gmail avec OAuth2.
    
    Returns:
        Les identifiants OAuth2 ou None en cas d'échec.
    """
    credentials = None
    token_path = Path('token.pickle')
    
    # Vérifier s'il existe déjà un token
    if token_path.exists():
        try:
            with open(token_path, 'rb') as token:
                credentials = pickle.load(token)
            logger.info("Token d'authentification chargé depuis le fichier.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du token: {e}")
    
    # Si les identifiants sont expirés ou n'existent pas
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                logger.info("Token d'authentification rafraîchi.")
            except Exception as e:
                logger.error(f"Erreur lors du rafraîchissement du token: {e}")
                credentials = None
        else:
            # Récupérer le chemin vers le fichier de configuration OAuth
            client_secret_file = os.getenv('GOOGLE_CLIENT_SECRET_FILE', 'client_secret.json')
            
            if not os.path.exists(client_secret_file):
                logger.error(f"Fichier de configuration OAuth non trouvé: {client_secret_file}")
                return None
            
            try:
                # Créer un flux d'authentification et ouvrir une page web pour l'authentification
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
                credentials = flow.run_local_server(port=0)
                logger.info("Authentification réussie avec Google.")
                
                # Sauvegarder les identifiants pour la prochaine exécution
                with open(token_path, 'wb') as token:
                    pickle.dump(credentials, token)
                logger.info("Token d'authentification sauvegardé.")
            
            except Exception as e:
                logger.error(f"Erreur lors de l'authentification: {e}")
                return None
    
    return credentials