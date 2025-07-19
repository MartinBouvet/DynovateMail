def __init__(self, credentials: Optional[str] = None, mock_mode: bool = True):
    """
    Initialise le client Gmail.
    
    Args:
        credentials: Chemin vers le fichier de credentials (optionnel)
        mock_mode: Mode mock pour développement (par défaut True)
    """
    self.credentials = credentials or "client_secret.json"
    self.mock_mode = mock_mode
    self.authenticated = False
    self.service = None
    
    # Scopes Gmail
    self.SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    if mock_mode:
        logger.info("Client Gmail initialisé en mode mock")
        self.authenticated = True
    else:
        logger.info("Client Gmail initialisé en mode production")