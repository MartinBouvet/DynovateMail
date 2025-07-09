"""
Modèles d'IA pour l'analyse et le traitement des emails.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from transformers import pipeline

logger = logging.getLogger(__name__)

class EmailClassifier:
    """Classe pour la classification des emails."""
    
    def __init__(self):
        """Initialise le classificateur d'emails."""
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.model = None
        self.sentiment_analyzer = None
        self.category_mapping = {}
        
        try:
            self.sentiment_analyzer = pipeline('sentiment-analysis')
            logger.info("Analyseur de sentiment initialisé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'analyseur de sentiment: {e}")
    
    def train(self, texts: List[str], labels: List[str] = None):
        """
        Entraîne le modèle de classification.
        
        Args:
            texts: Liste des textes d'email pour l'entraînement.
            labels: Liste des étiquettes correspondantes (si disponibles).
        """
        try:
            # Vectoriser les textes
            X = self.vectorizer.fit_transform(texts)
            
            if labels is None:
                # Si pas d'étiquettes, utiliser un clustering non supervisé
                n_clusters = min(10, len(texts))
                self.model = KMeans(n_clusters=n_clusters, random_state=42)
                self.model.fit(X)
                logger.info(f"Modèle de clustering entraîné avec {n_clusters} clusters.")
            else:
                # Si des étiquettes sont disponibles, utiliser un classificateur supervisé
                unique_labels = list(set(labels))
                self.category_mapping = {i: label for i, label in enumerate(unique_labels)}
                
                # Convertir les étiquettes textuelles en indices numériques
                y = np.array([unique_labels.index(label) for label in labels])
                
                # Entraîner un classificateur Random Forest
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
                self.model.fit(X, y)
                logger.info(f"Classificateur supervisé entraîné avec {len(unique_labels)} catégories.")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle: {e}")
    
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Prédit la catégorie d'un email.
        
        Args:
            text: Le texte de l'email à classifier.
            
        Returns:
            Dictionnaire contenant la catégorie prédite et d'autres informations.
        """
        if self.model is None:
            logger.warning("Le modèle n'a pas été entraîné. Impossible de faire une prédiction.")
            return {"category": "unknown", "confidence": 0.0}
        
        try:
            # Vectoriser le texte
            X = self.vectorizer.transform([text])
            
            # Faire la prédiction
            if isinstance(self.model, KMeans):
                # Pour le clustering non supervisé
                cluster = self.model.predict(X)[0]
                return {"category": f"cluster_{cluster}", "confidence": 1.0}
            else:
                # Pour la classification supervisée
                proba = self.model.predict_proba(X)[0]
                category_idx = np.argmax(proba)
                confidence = proba[category_idx]
                
                category = self.category_mapping.get(category_idx, f"category_{category_idx}")
                
                return {"category": category, "confidence": float(confidence)}
        
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {e}")
            return {"category": "error", "confidence": 0.0}
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyse le sentiment d'un texte.
        
        Args:
            text: Le texte à analyser.
            
        Returns:
            Dictionnaire contenant le sentiment et le score.
        """
        if self.sentiment_analyzer is None:
            logger.warning("Analyseur de sentiment non initialisé.")
            return {"sentiment": "unknown", "score": 0.0}
        
        try:
            # Limiter la taille du texte pour éviter les problèmes de mémoire
            if len(text) > 512:
                text = text[:512]
            
            result = self.sentiment_analyzer(text)[0]
            
            return {
                "sentiment": result["label"],
                "score": float(result["score"])
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du sentiment: {e}")
            return {"sentiment": "error", "score": 0.0}


class ResponseGenerator:
    """Classe pour la génération de réponses automatiques aux emails."""
    
    def __init__(self, model_name: str = "gpt2"):
        """
        Initialise le générateur de réponses.
        
        Args:
            model_name: Nom du modèle Hugging Face à utiliser.
        """
        self.generator = None
        
        try:
            self.generator = pipeline('text-generation', model=model_name)
            logger.info(f"Générateur de texte initialisé avec le modèle {model_name}.")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du générateur de texte: {e}")
    
    def generate_response(self, prompt: str, max_length: int = 150) -> str:
        """
        Génère une réponse à partir d'un prompt.
        
        Args:
            prompt: Le texte d'amorce pour la génération.
            max_length: Longueur maximale de la réponse générée.
            
        Returns:
            La réponse générée.
        """
        if self.generator is None:
            logger.warning("Générateur de texte non initialisé.")
            return ""
        
        try:
            # Générer la réponse
            result = self.generator(prompt, max_length=max_length, num_return_sequences=1)
            
            # Extraire le texte généré
            generated_text = result[0]["generated_text"]
            
            # Supprimer le prompt du texte généré
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {e}")
            return ""
    
    def generate_email_response(self, email_body: str, sender_name: str) -> str:
        """
        Génère une réponse à un email.
        
        Args:
            email_body: Le corps de l'email auquel répondre.
            sender_name: Le nom de l'expéditeur.
            
        Returns:
            La réponse générée.
        """
        # Créer un prompt pour la génération de réponse
        prompt = f"""Email reçu de {sender_name}:
{email_body}

Ma réponse:
"""
        
        # Générer la réponse
        response = self.generate_response(prompt, max_length=250)
        
        # Si la génération a échoué, utiliser une réponse par défaut
        if not response:
            response = f"""Bonjour {sender_name},

Merci pour votre email. Je l'ai bien reçu et je vous répondrai dans les plus brefs délais.

Cordialement,
[Votre nom]
"""
        
        return response