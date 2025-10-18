#!/usr/bin/env python3
"""
Processeur IA - VERSION CORRIGÉE COMPLÈTE
"""
import logging
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

from app.ollama_client import OllamaClient
from app.models.email_model import Email

logger = logging.getLogger(__name__)

class AIProcessor:
    """Processeur IA pour analyse d'emails."""
    
    def __init__(self, ollama_client: OllamaClient):
        """
        Initialise le processeur IA.
        
        Args:
            ollama_client: Client Ollama pour les requêtes IA
        """
        self.ollama_client = ollama_client
        logger.info("AIProcessor initialisé")
    
    def analyze_email(self, email: Email) -> Dict[str, Any]:
        """
        Analyse un email avec l'IA.
        
        Args:
            email: Email à analyser
            
        Returns:
            Dictionnaire avec l'analyse (category, sentiment, summary)
        """
        try:
            # Construire le prompt
            content = email.snippet or (email.body[:500] if email.body else '')
            
            prompt = f"""Analyse cet email et réponds UNIQUEMENT en JSON valide sans aucun texte avant ou après:

Expéditeur: {email.sender}
Sujet: {email.subject}
Contenu: {content}

Réponds au format JSON suivant (UNIQUEMENT le JSON, rien d'autre):
{{
    "category": "cv|meeting|invoice|newsletter|support|spam|important|personal|work",
    "sentiment": "positive|negative|neutral",
    "summary": "résumé en 1 phrase courte"
}}"""
            
            # Générer la réponse
            response = self.ollama_client.generate(prompt, max_tokens=200)
            
            # Parser le JSON
            analysis = self._parse_json_response(response)
            
            if analysis:
                logger.info(f"✅ Email analysé: {analysis.get('category')}")
                return analysis
            else:
                # Valeur par défaut
                return self._default_analysis(email)
        
        except Exception as e:
            logger.error(f"Erreur analyse email {email.id}: {e}")
            return self._default_analysis(email)
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse la réponse JSON de l'IA."""
        try:
            # Nettoyer la réponse
            response = response.strip()
            
            # Extraire le JSON
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                # Valider les champs
                if 'category' in analysis and 'sentiment' in analysis:
                    return analysis
            
            return None
        
        except Exception as e:
            logger.error(f"Erreur parsing JSON: {e}")
            return None
    
    def _default_analysis(self, email: Email) -> Dict[str, Any]:
        """Retourne une analyse par défaut."""
        # Détection basique de catégorie
        subject_lower = (email.subject or '').lower()
        sender_lower = (email.sender or '').lower()
        
        category = 'work'
        
        if any(word in subject_lower for word in ['cv', 'candidature', 'postul']):
            category = 'cv'
        elif any(word in subject_lower for word in ['réunion', 'meeting', 'rdv']):
            category = 'meeting'
        elif any(word in subject_lower for word in ['facture', 'invoice', 'paiement']):
            category = 'invoice'
        elif 'noreply' in sender_lower or 'newsletter' in subject_lower:
            category = 'newsletter'
        elif any(word in subject_lower for word in ['support', 'aide', 'help']):
            category = 'support'
        
        return {
            'category': category,
            'sentiment': 'neutral',
            'summary': email.subject or 'Email sans sujet'
        }
    
    def generate_response(self, email: Email, tone: str = "professional") -> str:
        """
        Génère une réponse automatique à un email.
        
        Args:
            email: Email auquel répondre
            tone: Ton de la réponse (professional, friendly, formal)
            
        Returns:
            Texte de la réponse générée
        """
        try:
            tone_instructions = {
                'professional': 'professionnel et courtois',
                'friendly': 'amical et chaleureux',
                'formal': 'très formel et respectueux'
            }
            
            tone_text = tone_instructions.get(tone, 'professionnel')
            
            prompt = f"""Rédige une réponse {tone_text} à cet email.

Email reçu:
De: {email.sender}
Sujet: {email.subject}
Message: {email.snippet or email.body[:500] if email.body else ''}

Rédige une réponse appropriée en français (maximum 200 mots):"""
            
            response = self.ollama_client.generate(prompt, max_tokens=300)
            
            logger.info("✅ Réponse générée")
            return response.strip()
        
        except Exception as e:
            logger.error(f"Erreur génération réponse: {e}")
            return "Merci pour votre email. Je reviendrai vers vous prochainement."
    
    def summarize_email(self, email: Email, max_length: int = 100) -> str:
        """
        Résume un email.
        
        Args:
            email: Email à résumer
            max_length: Longueur maximale du résumé
            
        Returns:
            Résumé de l'email
        """
        try:
            content = email.body or email.snippet or ''
            
            if len(content) <= max_length:
                return content
            
            prompt = f"""Résume cet email en 1-2 phrases maximum:

Sujet: {email.subject}
Contenu: {content[:1000]}

Résumé concis:"""
            
            summary = self.ollama_client.generate(prompt, max_tokens=100)
            
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Erreur résumé: {e}")
            return email.snippet or email.subject or "Résumé non disponible"
    
    def extract_action_items(self, email: Email) -> list:
        """
        Extrait les actions à faire depuis un email.
        
        Args:
            email: Email à analyser
            
        Returns:
            Liste des actions détectées
        """
        try:
            content = email.body or email.snippet or ''
            
            prompt = f"""Liste les actions à faire mentionnées dans cet email.

Email:
{content[:800]}

Liste les actions (une par ligne, commençant par "-"):"""
            
            response = self.ollama_client.generate(prompt, max_tokens=200)
            
            # Parser les actions
            actions = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    actions.append(line[1:].strip())
            
            return actions
        
        except Exception as e:
            logger.error(f"Erreur extraction actions: {e}")
            return []
    
    def detect_urgency(self, email: Email) -> str:
        """
        Détecte le niveau d'urgence d'un email.
        
        Args:
            email: Email à analyser
            
        Returns:
            'urgent', 'important', 'normal', ou 'low'
        """
        try:
            subject_lower = (email.subject or '').lower()
            content_lower = (email.snippet or email.body or '')[:500].lower()
            
            # Mots-clés d'urgence
            urgent_keywords = ['urgent', 'asap', 'immédiat', 'critique', 'emergency']
            important_keywords = ['important', 'prioritaire', 'rapidement', 'bientôt']
            
            # Vérification simple
            if any(keyword in subject_lower or keyword in content_lower for keyword in urgent_keywords):
                return 'urgent'
            elif any(keyword in subject_lower or keyword in content_lower for keyword in important_keywords):
                return 'important'
            
            # Demander à l'IA
            prompt = f"""Évalue l'urgence de cet email. Réponds uniquement par: URGENT, IMPORTANT, NORMAL ou LOW

Sujet: {email.subject}
Contenu: {email.snippet or ''}

Urgence:"""
            
            response = self.ollama_client.generate(prompt, max_tokens=10).strip().upper()
            
            if 'URGENT' in response:
                return 'urgent'
            elif 'IMPORTANT' in response:
                return 'important'
            elif 'LOW' in response:
                return 'low'
            else:
                return 'normal'
        
        except Exception as e:
            logger.error(f"Erreur détection urgence: {e}")
            return 'normal'
    
    def categorize_batch(self, emails: list) -> Dict[str, list]:
        """
        Catégorise un lot d'emails.
        
        Args:
            emails: Liste d'emails à catégoriser
            
        Returns:
            Dictionnaire avec les emails groupés par catégorie
        """
        try:
            categories = {
                'cv': [],
                'meeting': [],
                'invoice': [],
                'newsletter': [],
                'support': [],
                'important': [],
                'spam': [],
                'personal': [],
                'work': []
            }
            
            for email in emails:
                analysis = self.analyze_email(email)
                category = analysis.get('category', 'work')
                
                if category in categories:
                    categories[category].append(email)
                else:
                    categories['work'].append(email)
            
            logger.info(f"✅ {len(emails)} emails catégorisés")
            return categories
        
        except Exception as e:
            logger.error(f"Erreur catégorisation batch: {e}")
            return {'work': emails}
    
    def detect_spam(self, email: Email) -> bool:
        """
        Détecte si un email est du spam.
        
        Args:
            email: Email à analyser
            
        Returns:
            True si spam détecté, False sinon
        """
        try:
            # Indicateurs de spam simples
            sender_lower = (email.sender or '').lower()
            subject_lower = (email.subject or '').lower()
            
            spam_indicators = [
                'noreply' in sender_lower and 'promo' in subject_lower,
                subject_lower.count('!') > 3,
                'viagra' in subject_lower or 'casino' in subject_lower,
                'lottery' in subject_lower or 'winner' in subject_lower,
            ]
            
            if any(spam_indicators):
                return True
            
            # Demander à l'IA
            prompt = f"""Cet email est-il du spam? Réponds uniquement par OUI ou NON

Expéditeur: {email.sender}
Sujet: {email.subject}
Contenu: {email.snippet or ''}

Spam:"""
            
            response = self.ollama_client.generate(prompt, max_tokens=10).strip().upper()
            
            return 'OUI' in response or 'YES' in response
        
        except Exception as e:
            logger.error(f"Erreur détection spam: {e}")
            return False
    
    def generate_smart_reply_suggestions(self, email: Email, count: int = 3) -> list:
        """
        Génère des suggestions de réponses rapides.
        
        Args:
            email: Email source
            count: Nombre de suggestions
            
        Returns:
            Liste de suggestions de réponses
        """
        try:
            prompt = f"""Génère {count} suggestions de réponses courtes à cet email.

Email:
De: {email.sender}
Sujet: {email.subject}
Message: {email.snippet or ''}

Génère {count} réponses courtes et pertinentes (une par ligne, maximum 15 mots chacune):"""
            
            response = self.ollama_client.generate(prompt, max_tokens=200)
            
            # Parser les suggestions
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and len(line) > 10:
                    # Retirer les numéros et tirets
                    line = re.sub(r'^[\d\-\.\)]+\s*', '', line)
                    suggestions.append(line)
                    
                    if len(suggestions) >= count:
                        break
            
            return suggestions[:count]
        
        except Exception as e:
            logger.error(f"Erreur suggestions: {e}")
            return [
                "Merci pour votre message.",
                "Je reviens vers vous rapidement.",
                "C'est noté, merci !"
            ]
    
    def analyze_sentiment_batch(self, emails: list) -> Dict[str, int]:
        """
        Analyse le sentiment d'un lot d'emails.
        
        Args:
            emails: Liste d'emails
            
        Returns:
            Statistiques de sentiment
        """
        try:
            sentiments = {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
            
            for email in emails:
                analysis = self.analyze_email(email)
                sentiment = analysis.get('sentiment', 'neutral')
                
                if sentiment in sentiments:
                    sentiments[sentiment] += 1
            
            logger.info(f"✅ Sentiment analysé sur {len(emails)} emails")
            return sentiments
        
        except Exception as e:
            logger.error(f"Erreur analyse sentiment batch: {e}")
            return {'positive': 0, 'negative': 0, 'neutral': len(emails)}
    
    def extract_contact_info(self, email: Email) -> Dict[str, Any]:
        """
        Extrait les informations de contact depuis un email.
        
        Args:
            email: Email à analyser
            
        Returns:
            Dictionnaire avec les infos de contact trouvées
        """
        try:
            content = f"{email.subject} {email.body or email.snippet or ''}"
            
            # Regex pour extraire des infos
            phone_pattern = r'(?:\+33|0)[1-9](?:[0-9]{8}|[0-9\s\-\.]{8,})'
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            
            phones = re.findall(phone_pattern, content)
            emails_found = re.findall(email_pattern, content)
            
            return {
                'phones': list(set(phones)),
                'emails': list(set(emails_found)),
                'sender': email.sender
            }
        
        except Exception as e:
            logger.error(f"Erreur extraction contact: {e}")
            return {'phones': [], 'emails': [], 'sender': email.sender}
    
    def prioritize_emails(self, emails: list) -> Dict[str, list]:
        """
        Priorise une liste d'emails.
        
        Args:
            emails: Liste d'emails à prioriser
            
        Returns:
            Dictionnaire avec emails groupés par priorité
        """
        try:
            priorities = {
                'urgent': [],
                'important': [],
                'normal': [],
                'low': []
            }
            
            for email in emails:
                urgency = self.detect_urgency(email)
                
                if urgency in priorities:
                    priorities[urgency].append(email)
                else:
                    priorities['normal'].append(email)
            
            logger.info(f"✅ {len(emails)} emails priorisés")
            return priorities
        
        except Exception as e:
            logger.error(f"Erreur priorisation: {e}")
            return {'normal': emails, 'urgent': [], 'important': [], 'low': []}
    
    def generate_email_draft(self, topic: str, recipient: str, tone: str = "professional") -> str:
        """
        Génère un brouillon d'email.
        
        Args:
            topic: Sujet de l'email
            recipient: Destinataire
            tone: Ton (professional, friendly, formal)
            
        Returns:
            Brouillon d'email généré
        """
        try:
            tone_instructions = {
                'professional': 'professionnel et courtois',
                'friendly': 'amical et décontracté',
                'formal': 'très formel et respectueux'
            }
            
            tone_text = tone_instructions.get(tone, 'professionnel')
            
            prompt = f"""Rédige un email {tone_text} en français.

Destinataire: {recipient}
Sujet: {topic}

Rédige l'email complet avec:
- Une formule de politesse d'ouverture
- Le corps du message (3-4 phrases)
- Une formule de politesse de clôture
- La signature

Email:"""
            
            draft = self.ollama_client.generate(prompt, max_tokens=400)
            
            logger.info("✅ Brouillon généré")
            return draft.strip()
        
        except Exception as e:
            logger.error(f"Erreur génération brouillon: {e}")
            return f"Bonjour,\n\nConcernant {topic}...\n\nCordialement"
    
    def detect_language(self, text: str) -> str:
        """
        Détecte la langue d'un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Code de langue ('fr', 'en', etc.)
        """
        try:
            # Détection simple basée sur des mots communs
            french_words = ['le', 'la', 'les', 'de', 'un', 'une', 'est', 'sont', 'pour']
            english_words = ['the', 'is', 'are', 'for', 'and', 'to', 'in', 'of']
            
            text_lower = text.lower()
            
            french_count = sum(1 for word in french_words if f' {word} ' in text_lower)
            english_count = sum(1 for word in english_words if f' {word} ' in text_lower)
            
            if french_count > english_count:
                return 'fr'
            elif english_count > french_count:
                return 'en'
            else:
                return 'fr'  # Par défaut
        
        except Exception as e:
            logger.error(f"Erreur détection langue: {e}")
            return 'fr'
    
    def translate_text(self, text: str, target_lang: str = 'fr') -> str:
        """
        Traduit un texte.
        
        Args:
            text: Texte à traduire
            target_lang: Langue cible
            
        Returns:
            Texte traduit
        """
        try:
            lang_names = {
                'fr': 'français',
                'en': 'anglais',
                'es': 'espagnol',
                'de': 'allemand'
            }
            
            target_name = lang_names.get(target_lang, 'français')
            
            prompt = f"""Traduis ce texte en {target_name}:

{text}

Traduction:"""
            
            translation = self.ollama_client.generate(prompt, max_tokens=500)
            
            return translation.strip()
        
        except Exception as e:
            logger.error(f"Erreur traduction: {e}")
            return text
    
    def check_grammar(self, text: str) -> Dict[str, Any]:
        """
        Vérifie la grammaire et l'orthographe.
        
        Args:
            text: Texte à vérifier
            
        Returns:
            Corrections suggérées
        """
        try:
            prompt = f"""Corrige les fautes d'orthographe et de grammaire dans ce texte.

Texte original:
{text}

Texte corrigé:"""
            
            corrected = self.ollama_client.generate(prompt, max_tokens=600)
            
            has_errors = corrected.strip() != text.strip()
            
            return {
                'has_errors': has_errors,
                'original': text,
                'corrected': corrected.strip(),
                'suggestions': []
            }
        
        except Exception as e:
            logger.error(f"Erreur vérification grammaire: {e}")
            return {
                'has_errors': False,
                'original': text,
                'corrected': text,
                'suggestions': []
            }
    
    def summarize_thread(self, emails: list) -> str:
        """
        Résume une conversation email (thread).
        
        Args:
            emails: Liste d'emails du thread
            
        Returns:
            Résumé de la conversation
        """
        try:
            if not emails:
                return "Aucun email dans la conversation"
            
            # Construire l'historique
            thread_text = "\n\n".join([
                f"De: {email.sender}\nSujet: {email.subject}\nMessage: {email.snippet or ''}"
                for email in emails[:5]  # Limiter à 5 emails
            ])
            
            prompt = f"""Résume cette conversation email en 2-3 phrases:

{thread_text}

Résumé de la conversation:"""
            
            summary = self.ollama_client.generate(prompt, max_tokens=200)
            
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Erreur résumé thread: {e}")
            return "Résumé non disponible"
    
    def health_check(self) -> bool:
        """
        Vérifie que l'IA fonctionne correctement.
        
        Returns:
            True si OK, False sinon
        """
        try:
            test_prompt = "Réponds simplement par OK"
            response = self.ollama_client.generate(test_prompt, max_tokens=10)
            
            return bool(response and len(response.strip()) > 0)
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False