"""
Processeur IA 100% LOCAL pour l'analyse et le traitement des emails.
Aucune dépendance externe (OpenAI, etc.) - Tout fonctionne en local !
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

# Import conditionnel pour éviter les erreurs
try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("Transformers non disponible - IA simplifiée")

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logging.warning("spaCy non disponible - analyse de texte simplifiée")

from models.email_model import Email
from models.calendar_model import CalendarEvent
from utils.ai_utils import extract_datetime, extract_contact_info, clean_text

logger = logging.getLogger(__name__)

class LocalAIProcessor:
    """Processeur IA 100% LOCAL pour l'analyse des emails."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le processeur IA local.
        
        Args:
            config: Configuration de l'application.
        """
        self.config = config
        self.initialized = False
        
        # Modèles IA locaux
        self.classifier = None
        self.sentiment_analyzer = None
        self.nlp = None
        
        # Catégories d'emails avec mots-clés français
        self.categories = {
            'cv': [
                'cv', 'curriculum', 'candidature', 'postule', 'emploi', 'stage', 
                'recrutement', 'expérience', 'diplôme', 'formation', 'compétences',
                'lettre de motivation', 'profil', 'poste', 'carrière'
            ],
            'rdv': [
                'rendez-vous', 'meeting', 'réunion', 'entretien', 'rdv', 'rencontrer',
                'disponible', 'planning', 'agenda', 'créneau', 'horaire', 'date',
                'quand', 'voir', 'discuter', 'prendre contact'
            ],
            'spam': [
                'viagra', 'casino', 'gagnant', 'promotion', 'offre spéciale', 
                'gratuit', 'urgent', 'félicitations', 'loterie', 'prix',
                'cliquez ici', 'offre limitée', 'argent facile', 'investissement'
            ],
            'facture': [
                'facture', 'devis', 'commande', 'paiement', 'montant', 'prix',
                'tarif', 'coût', 'règlement', 'échéance', 'tva', 'total',
                'payer', 'somme', 'euro', '€', 'facturation'
            ],
            'support': [
                'problème', 'aide', 'support', 'assistance', 'bug', 'erreur',
                'dysfonctionnement', 'panne', 'réparer', 'résoudre', 'solution',
                'question', 'comment', 'pourquoi', 'ne fonctionne pas'
            ],
            'partenariat': [
                'partenariat', 'collaboration', 'proposition', 'business',
                'coopération', 'projet', 'ensemble', 'alliance', 'accord',
                'contrat', 'opportunité', 'développement', 'mutuel'
            ],
            'newsletter': [
                'newsletter', 'actualité', 'info', 'bulletin', 'magazine',
                'journal', 'nouveautés', 'mise à jour', 'édition', 'numéro',
                'abonnement', 'désabonner', 'monthly', 'weekly'
            ],
            'important': [
                'urgent', 'important', 'priorité', 'asap', 'emergency', 'critique',
                'immédiat', 'rapidement', 'tout de suite', 'deadline', 'échéance'
            ]
        }
        
        # Patterns pour détecter les réponses automatiques
        self.auto_response_patterns = [
            r'out of office', r'absent', r'congé', r'vacances', r'indisponible',
            r'auto.{0,10}reply', r'réponse automatique', r'automatic response'
        ]
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialise les modèles IA locaux."""
        try:
            logger.info("Initialisation des modèles IA locaux...")
            
            # Analyseur de sentiment local
            if HAS_TRANSFORMERS:
                try:
                    self.sentiment_analyzer = pipeline(
                        "sentiment-analysis",
                        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                        return_all_scores=True
                    )
                    logger.info("Analyseur de sentiment local chargé")
                except Exception as e:
                    logger.warning(f"Impossible de charger le modèle de sentiment: {e}")
            
            # Modèle spaCy pour l'analyse de texte
            if HAS_SPACY:
                try:
                    self.nlp = spacy.load('fr_core_news_sm')
                    logger.info("Modèle spaCy français chargé")
                except Exception as e:
                    logger.warning(f"Impossible de charger spaCy: {e}")
                    try:
                        self.nlp = spacy.load('en_core_web_sm')
                        logger.info("Modèle spaCy anglais chargé")
                    except Exception as e2:
                        logger.warning(f"Aucun modèle spaCy disponible: {e2}")
            
            self.initialized = True
            logger.info("Modèles IA locaux initialisés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des modèles IA: {e}")
            self.initialized = False
    
    def classify_email(self, email: Email) -> str:
        """
        Classifie un email dans une catégorie en utilisant des mots-clés.
        
        Args:
            email: L'email à classifier.
            
        Returns:
            La catégorie de l'email.
        """
        try:
            text = f"{email.subject} {email.body}".lower()
            
            # Scores pour chaque catégorie
            category_scores = {}
            
            # Vérifier chaque catégorie
            for category, keywords in self.categories.items():
                score = 0
                for keyword in keywords:
                    # Compter les occurrences avec bonus pour le sujet
                    subject_count = email.subject.lower().count(keyword) * 2  # Bonus sujet
                    body_count = email.body.lower().count(keyword)
                    score += subject_count + body_count
                
                if score > 0:
                    category_scores[category] = score
            
            # Retourner la catégorie avec le score le plus élevé
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                logger.info(f"Email classifié comme '{best_category}' (score: {category_scores[best_category]})")
                return best_category
            
            # Analyse plus poussée si disponible
            if self.nlp:
                return self._advanced_classification(email)
            
            return 'general'
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {e}")
            return 'general'
    
    def _advanced_classification(self, email: Email) -> str:
        """Classification avancée avec spaCy."""
        try:
            doc = self.nlp(f"{email.subject} {email.body}")
            
            # Analyser les entités pour détecter des patterns
            entities = [ent.label_ for ent in doc.ents]
            
            # Règles basées sur les entités
            if 'PERSON' in entities and any(keyword in email.body.lower() for keyword in ['cv', 'candidature']):
                return 'cv'
            
            if 'DATE' in entities and any(keyword in email.body.lower() for keyword in ['rdv', 'meeting']):
                return 'rdv'
            
            if 'MONEY' in entities:
                return 'facture'
            
            return 'general'
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification avancée: {e}")
            return 'general'
    
    def extract_meeting_info(self, email: Email) -> Optional[CalendarEvent]:
        """
        Extrait les informations de rendez-vous d'un email.
        
        Args:
            email: L'email à analyser.
            
        Returns:
            Un événement de calendrier ou None.
        """
        if self.classify_email(email) != 'rdv':
            return None
        
        try:
            # Extraire les informations temporelles
            datetime_info = extract_datetime(email.body)
            
            # Extraire les informations de contact
            contact_info = extract_contact_info(email.body)
            
            if datetime_info and datetime_info.get('start_time'):
                event = CalendarEvent(
                    title=f"Rendez-vous - {email.get_sender_name()}",
                    description=f"Email de: {email.sender}\nSujet: {email.subject}\n\n{email.body[:200]}...",
                    start_time=datetime_info.get('start_time'),
                    end_time=datetime_info.get('end_time'),
                    location=contact_info.get('location', ''),
                    attendees=[email.get_sender_email()],
                    email_id=email.id
                )
                
                logger.info(f"Rendez-vous extrait: {event.title}")
                return event
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des infos de RDV: {e}")
        
        return None
    
    def should_auto_respond(self, email: Email) -> bool:
        """
        Détermine si un email doit recevoir une réponse automatique.
        
        Args:
            email: L'email à analyser.
            
        Returns:
            True si une réponse automatique doit être envoyée.
        """
        try:
            # Ne pas répondre aux emails envoyés par l'utilisateur
            if email.is_sent:
                return False
            
            # Ne pas répondre aux newsletters
            if self.classify_email(email) == 'newsletter':
                return False
            
            # Ne pas répondre aux spams
            if self.classify_email(email) == 'spam':
                return False
            
            # Ne pas répondre aux réponses automatiques
            text = f"{email.subject} {email.body}".lower()
            for pattern in self.auto_response_patterns:
                if re.search(pattern, text):
                    return False
            
            # Vérifier si c'est une demande qui nécessite une réponse
            response_triggers = [
                r'question', r'demande', r'besoin', r'pourriez-vous', 
                r'pouvez-vous', r'j\'aimerais', r'est-ce que',
                r'comment', r'quand', r'où', r'pourquoi'
            ]
            
            for trigger in response_triggers:
                if re.search(trigger, text):
                    return True
            
            # Répondre aux catégories spécifiques
            category = self.classify_email(email)
            return category in ['cv', 'rdv', 'support', 'partenariat']
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de réponse automatique: {e}")
            return False
    
    def generate_auto_response(self, email: Email) -> str:
        """
        Génère une réponse automatique pour un email.
        
        Args:
            email: L'email auquel répondre.
            
        Returns:
            La réponse générée.
        """
        try:
            category = self.classify_email(email)
            sender_name = email.get_sender_name()
            
            # Templates de réponses par catégorie
            templates = {
                'cv': f"""Bonjour {sender_name},

Merci pour votre candidature que nous avons bien reçue.

Notre équipe RH va examiner votre profil dans les plus brefs délais. Nous vous contacterons prochainement si votre candidature correspond à nos besoins actuels.

Nous vous remercions pour l'intérêt que vous portez à notre entreprise.

Cordialement,
L'équipe Recrutement""",
                
                'rdv': f"""Bonjour {sender_name},

Merci pour votre demande de rendez-vous.

J'ai bien reçu votre message et je vais vérifier mes disponibilités. Je vous recontacterai rapidement pour convenir d'un créneau qui nous convient.

Cordialement""",
                
                'support': f"""Bonjour {sender_name},

Merci pour votre message.

J'ai bien reçu votre demande d'assistance et je vais l'examiner attentivement. Je vous répondrai dans les plus brefs délais avec une solution appropriée.

Si votre demande est urgente, n'hésitez pas à me contacter directement.

Cordialement,
L'équipe Support""",
                
                'partenariat': f"""Bonjour {sender_name},

Merci pour votre proposition de partenariat.

Nous sommes toujours intéressés par de nouvelles opportunités de collaboration. Je vais examiner votre proposition et la transmettre aux personnes concernées.

Nous vous recontacterons prochainement pour discuter des possibilités de collaboration.

Cordialement,
L'équipe Développement""",
                
                'facture': f"""Bonjour {sender_name},

Merci pour votre facture que nous avons bien reçue.

Elle va être transmise à notre service comptable pour traitement. Le règlement sera effectué selon nos conditions de paiement habituelles.

Cordialement,
Service Comptabilité""",
                
                'general': f"""Bonjour {sender_name},

Merci pour votre email.

J'ai bien reçu votre message et je vous répondrai dans les plus brefs délais.

Cordialement"""
            }
            
            response = templates.get(category, templates['general'])
            
            # Ajouter une signature personnalisée si configurée
            user_signature = self.config.get('user', {}).get('signature', '')
            if user_signature:
                response += f"\n\n{user_signature}"
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse: {e}")
            return f"Bonjour {email.get_sender_name()},\n\nMerci pour votre message.\n\nCordialement"
    
    def analyze_email_priority(self, email: Email) -> int:
        """
        Analyse la priorité d'un email (1=faible, 3=élevée).
        
        Args:
            email: L'email à analyser.
            
        Returns:
            Niveau de priorité (1-3).
        """
        try:
            priority = 1
            text = f"{email.subject} {email.body}".lower()
            
            # Mots-clés de priorité élevée
            high_priority_keywords = [
                'urgent', 'asap', 'important', 'priorité', 'emergency', 'critique',
                'deadline', 'échéance', 'time-sensitive', 'immédiat', 'rapidement'
            ]
            
            # Vérifier les mots-clés
            for keyword in high_priority_keywords:
                if keyword in text:
                    priority = 3
                    break
            
            # Vérifier si c'est un email professionnel
            if self._is_professional_email(email.get_sender_email()):
                priority = max(priority, 2)
            
            # Analyser le sentiment si disponible
            if self.sentiment_analyzer:
                sentiment = self._analyze_sentiment_local(text)
                if sentiment.get('negative_score', 0) > 0.7:
                    priority = max(priority, 2)
            
            return priority
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de priorité: {e}")
            return 1
    
    def _is_professional_email(self, email_address: str) -> bool:
        """Détermine si une adresse email est professionnelle."""
        try:
            personal_domains = [
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                'free.fr', 'orange.fr', 'wanadoo.fr', 'sfr.fr',
                'laposte.net', 'bbox.fr'
            ]
            
            domain = email_address.split('@')[1].lower()
            return domain not in personal_domains
            
        except Exception:
            return False
    
    def _analyze_sentiment_local(self, text: str) -> Dict[str, float]:
        """Analyse le sentiment avec le modèle local."""
        try:
            if not self.sentiment_analyzer:
                return {'positive_score': 0.5, 'negative_score': 0.5, 'neutral_score': 0.5}
            
            # Limiter la taille du texte
            text_sample = text[:512]
            
            results = self.sentiment_analyzer(text_sample)
            
            # Convertir les résultats en scores
            scores = {'positive_score': 0, 'negative_score': 0, 'neutral_score': 0}
            
            for result in results[0]:  # Premier résultat
                label = result['label'].lower()
                score = result['score']
                
                if 'positive' in label:
                    scores['positive_score'] = score
                elif 'negative' in label:
                    scores['negative_score'] = score
                else:
                    scores['neutral_score'] = score
            
            return scores
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de sentiment: {e}")
            return {'positive_score': 0.5, 'negative_score': 0.5, 'neutral_score': 0.5}
    
    def extract_key_information(self, email: Email) -> Dict[str, Any]:
        """
        Extrait les informations clés d'un email.
        
        Args:
            email: L'email à analyser.
            
        Returns:
            Dictionnaire des informations extraites.
        """
        try:
            category = self.classify_email(email)
            priority = self.analyze_email_priority(email)
            should_respond = self.should_auto_respond(email)
            meeting_info = self.extract_meeting_info(email)
            
            # Analyse de sentiment
            sentiment = self._analyze_sentiment_local(f"{email.subject} {email.body}")
            
            # Extraire les entités si spaCy est disponible
            entities = []
            if self.nlp:
                try:
                    doc = self.nlp(email.body[:1000])  # Limiter à 1000 caractères
                    entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents[:10]]
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction d'entités: {e}")
            
            info = {
                'category': category,
                'priority': priority,
                'should_auto_respond': should_respond,
                'meeting_info': meeting_info,
                'sentiment': {
                    'label': 'POSITIVE' if sentiment['positive_score'] > 0.6 else 'NEGATIVE' if sentiment['negative_score'] > 0.6 else 'NEUTRAL',
                    'score': max(sentiment['positive_score'], sentiment['negative_score'], sentiment['neutral_score'])
                },
                'entities': entities,
                'is_professional': self._is_professional_email(email.get_sender_email())
            }
            
            logger.info(f"Analyse complète terminée - Catégorie: {category}, Priorité: {priority}")
            return info
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'informations: {e}")
            return {
                'category': 'general',
                'priority': 1,
                'should_auto_respond': False,
                'meeting_info': None,
                'sentiment': {'label': 'NEUTRAL', 'score': 0.5},
                'entities': [],
                'is_professional': False
            }

# Alias pour compatibilité
AIProcessor = LocalAIProcessor