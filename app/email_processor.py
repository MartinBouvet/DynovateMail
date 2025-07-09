"""
Module pour le traitement et l'analyse des emails avec IA.
"""
import logging
import re
from typing import List, Dict, Any, Optional
import spacy
from transformers import pipeline
import torch

from models.email_model import Email

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Classe pour traiter et analyser les emails avec IA."""
    
    def __init__(self):
        """Initialise le processeur d'emails."""
        self.initialized = False
        self.nlp = None
        self.classifier = None
        
        # Tenter de charger les modèles
        try:
            self._initialize_models()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des modèles d'IA: {e}")
    
    def _initialize_models(self):
        """Initialise les modèles d'IA."""
        if self.initialized:
            return
        
        logger.info("Initialisation des modèles d'IA...")
        
        # Charger spaCy pour l'analyse de texte (entités, mots-clés, etc.)
        try:
            self.nlp = spacy.load('fr_core_news_sm')
            logger.info("Modèle spaCy chargé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle spaCy: {e}")
            # Télécharger le modèle s'il n'est pas présent
            logger.info("Tentative de téléchargement du modèle spaCy...")
            spacy.cli.download('fr_core_news_sm')
            self.nlp = spacy.load('fr_core_news_sm')
        
        # Charger un modèle de classification pour les catégories d'emails
        # Utiliser un modèle pré-entraîné de Hugging Face
        try:
            if torch.cuda.is_available():
                device = 0  # GPU
            else:
                device = -1  # CPU
            
            self.classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=device
            )
            logger.info("Classificateur de texte chargé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du classificateur: {e}")
            self.classifier = None
        
        self.initialized = True
        logger.info("Modèles d'IA initialisés.")
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extrait les entités nommées du texte.
        
        Args:
            text: Le texte à analyser.
            
        Returns:
            Dictionnaire des entités par type.
        """
        if not self.initialized or not self.nlp:
            self._initialize_models()
        
        if not self.nlp:
            logger.error("Impossible d'extraire les entités: modèle spaCy non disponible.")
            return {}
        
        try:
            doc = self.nlp(text)
            
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                
                entities[ent.label_].append(ent.text)
            
            return entities
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des entités: {e}")
            return {}
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """
        Extrait les mots-clés du texte.
        
        Args:
            text: Le texte à analyser.
            num_keywords: Nombre de mots-clés à extraire.
            
        Returns:
            Liste des mots-clés.
        """
        if not self.initialized or not self.nlp:
            self._initialize_models()
        
        if not self.nlp:
            logger.error("Impossible d'extraire les mots-clés: modèle spaCy non disponible.")
            return []
        
        try:
            doc = self.nlp(text)
            
            # Filtrer les mots non significatifs (stopwords, ponctuation, etc.)
            keywords = [token.lemma_ for token in doc 
                       if not token.is_stop and not token.is_punct and token.has_vector]
            
            # Obtenir les fréquences des mots
            word_freq = {}
            for word in keywords:
                if word.lower() in word_freq:
                    word_freq[word.lower()] += 1
                else:
                    word_freq[word.lower()] = 1
            
            # Trier par fréquence
            sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Retourner les N premiers mots-clés
            return [word for word, _ in sorted_keywords[:num_keywords]]
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des mots-clés: {e}")
            return []
    
    def classify_email(self, email: Email) -> Optional[str]:
        """
        Classifie un email selon son contenu.
        
        Args:
            email: L'email à classifier.
            
        Returns:
            La catégorie de l'email ou None en cas d'erreur.
        """
        if not self.initialized or not self.classifier:
            self._initialize_models()
        
        if not self.classifier:
            logger.error("Impossible de classifier l'email: classificateur non disponible.")
            return None
        
        try:
            # Combiner le sujet et le corps pour la classification
            text = f"{email.subject} {email.body}"
            
            # Limiter la taille du texte pour éviter les problèmes de mémoire
            if len(text) > 512:
                text = text[:512]
            
            # Classifier le texte
            result = self.classifier(text)[0]
            
            # Retourner la catégorie avec le score
            category = result['label']
            score = result['score']
            
            logger.info(f"Email classifié comme '{category}' avec un score de {score:.2f}")
            
            return category
        
        except Exception as e:
            logger.error(f"Erreur lors de la classification de l'email: {e}")
            return None
    
    def is_spam(self, email: Email) -> bool:
        """
        Détermine si un email est un spam.
        
        Args:
            email: L'email à analyser.
            
        Returns:
            True si l'email est un spam, False sinon.
        """
        # Cette méthode utilise des règles simples pour la détection de spam
        # Dans une version plus avancée, on utiliserait un modèle ML dédié
        
        # Vérifier le sujet pour les mots-clés spam courants
        spam_keywords = [
            "viagra", "winner", "congratulations", "free", "buy now", "discount",
            "cheap", "earn money", "casino", "lottery", "prize", "guaranteed",
            "viagra", "gagnant", "félicitations", "gratuit", "achetez maintenant", 
            "réduction", "pas cher", "gagnez de l'argent", "casino", "loterie", 
            "prix", "garanti"
        ]
        
        subject_lower = email.subject.lower()
        for keyword in spam_keywords:
            if keyword in subject_lower:
                return True
        
        # Vérifier si l'email contient trop de liens ou d'images
        body_lower = email.body.lower()
        
        # Compter les liens
        link_count = len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', body_lower))
        if link_count > 5:
            return True
        
        # Vérifier le ratio texte/lien
        if len(body_lower) > 0 and link_count > 0:
            ratio = len(body_lower) / link_count
            if ratio < 20:  # Si moins de 20 caractères par lien
                return True
        
        return False
    
    def generate_response(self, email: Email) -> str:
        """
        Génère une réponse automatique à un email.
        
        Args:
            email: L'email auquel répondre.
            
        Returns:
            La réponse générée.
        """
        # Dans une version future, cette méthode utilisera un modèle de langage
        # plus avancé pour générer des réponses personnalisées
        
        # Pour l'instant, utiliser des templates simples
        
        # Extraire le nom de l'expéditeur
        sender_name = email.get_sender_name()
        
        # Réponse générique
        response = f"""Bonjour {sender_name},

Merci pour votre email. Je l'ai bien reçu et je vous répondrai dans les plus brefs délais.

Cordialement,
[Votre nom]
"""
        
        return response