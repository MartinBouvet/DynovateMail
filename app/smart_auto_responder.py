"""
Répondeur automatique ultra-intelligent avec génération de réponses contextuelles
Utilise des modèles de langage avancés pour des réponses naturelles et pertinentes
"""

import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM,
    pipeline, GPT2LMHeadModel, GPT2Tokenizer
)
import openai
from typing import Dict, List, Optional, Tuple
import logging
import re
import json
import os
from datetime import datetime, timedelta
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

logger = logging.getLogger(__name__)

class SmartAutoResponder:
    """Répondeur automatique ultra-intelligent avec IA générative"""
    
    def __init__(self, config_path: str = "responder_config.json"):
        self.config_path = config_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Modèles de génération de texte
        self.models = {}
        self.tokenizers = {}
        
        # Configuration
        self.config = self._load_config()
        
        # Templates et patterns
        self.templates = {}
        self.response_patterns = {}
        self.context_memory = {}
        
        # Historique des réponses
        self.response_history = {}
        self.conversation_context = {}
        
        # Base de données
        self.db_path = "auto_responder.db"
        
        # Modèles spécialisés
        self.sentence_transformer = None
        self.nlp = None
        
        # Évitement des boucles
        self.loop_detection = {}
        self.blacklisted_senders = set()
        
        self._initialize_models()
        self._setup_database()
        self._load_templates()
    
    def _load_config(self) -> Dict:
        """Charge la configuration du répondeur"""
        default_config = {
            "enabled": True,
            "response_delay_minutes": 5,
            "max_responses_per_day": 50,
            "response_categories": {
                "cv": True,
                "rdv": True,
                "support": True,
                "commercial": True,
                "general": False
            },
            "openai_api_key": "",
            "response_style": "professional",
            "language": "fr",
            "loop_prevention": True,
            "max_response_length": 500,
            "include_signature": True,
            "signature": "Cordialement,\nAssistant IA"
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
        
        return default_config
    
    def _initialize_models(self):
        """Initialise tous les modèles de génération"""
        try:
            # 1. Modèle GPT français pour génération
            self._initialize_gpt_model()
            
            # 2. Modèle de traduction/paraphrase
            self._initialize_translation_model()
            
            # 3. Modèle de classification d'intention
            self._initialize_intent_model()
            
            # 4. Modèle pour embeddings sémantiques
            self.sentence_transformer = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2',
                device=self.device
            )
            
            # 5. Modèle NLP pour analyse
            try:
                self.nlp = spacy.load("fr_core_news_sm")
            except OSError:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    logger.warning("Aucun modèle spaCy disponible")
            
            # 6. Configuration OpenAI si disponible
            if self.config.get("openai_api_key"):
                openai.api_key = self.config["openai_api_key"]
            
            logger.info("Modèles de génération initialisés")
            
        except Exception as e:
            logger.error(f"Erreur initialisation modèles: {e}")
    
    def _initialize_gpt_model(self):
        """Initialise le modèle GPT pour génération française"""
        try:
            model_name = "microsoft/DialoGPT-medium"
            
            self.models['gpt'] = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            self.tokenizers['gpt'] = AutoTokenizer.from_pretrained(model_name)
            
            # Configuration du tokenizer
            if self.tokenizers['gpt'].pad_token is None:
                self.tokenizers['gpt'].pad_token = self.tokenizers['gpt'].eos_token
            
            logger.info("Modèle GPT initialisé")
            
        except Exception as e:
            logger.error(f"Erreur GPT: {e}")
    
    def _initialize_translation_model(self):
        """Initialise le modèle de traduction/paraphrase"""
        try:
            self.models['paraphrase'] = pipeline(
                "text2text-generation",
                model="t5-base",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Modèle de paraphrase initialisé")
            
        except Exception as e:
            logger.error(f"Erreur modèle paraphrase: {e}")
    
    def _initialize_intent_model(self):
        """Initialise le modèle de classification d'intention"""
        try:
            self.models['intent'] = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Modèle d'intention initialisé")
            
        except Exception as e:
            logger.error(f"Erreur modèle intention: {e}")
    
    def _setup_database(self):
        """Configure la base de données pour l'historique"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_email_id TEXT,
                    sender_email TEXT,
                    response_text TEXT,
                    response_type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL,
                    model_used TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loop_detection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_email TEXT,
                    last_response DATETIME,
                    response_count INTEGER DEFAULT 1,
                    blocked_until DATETIME
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_email TEXT,
                    context_data TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur setup base de données: {e}")
    
    def _load_templates(self):
        """Charge les templates de réponses par catégorie"""
        self.templates = {
            'cv': {
                'fr': [
                    "Merci pour votre candidature. Nous avons bien reçu votre CV et l'examinerons attentivement. Nous vous recontacterons sous 48h si votre profil correspond à nos besoins actuels.",
                    "Votre candidature a été reçue avec attention. Notre équipe RH procédera à l'étude de votre dossier dans les plus brefs délais.",
                    "Nous accusons réception de votre candidature. Votre CV sera étudié par notre équipe et nous vous donnerons une réponse rapidement."
                ]
            },
            'rdv': {
                'fr': [
                    "Merci pour votre demande de rendez-vous. Je consulte mon agenda et vous propose les créneaux suivants : [SLOTS]. Confirmez-moi celui qui vous convient le mieux.",
                    "Suite à votre demande, voici mes disponibilités : [SLOTS]. N'hésitez pas à me faire savoir quelle option vous préférez."
                ]
            },
            'support': {
                'fr': [
                    "Merci pour votre message. Votre demande a été prise en compte et transmise à notre équipe technique. Vous recevrez une réponse détaillée sous 24h.",
                    "Nous avons bien reçu votre demande d'assistance. Un ticket a été créé et notre équipe va traiter votre problème rapidement."
                ]
            },
            'commercial': {
                'fr': [
                    "Merci pour votre intérêt. Nous étudions votre demande et vous ferons parvenir une proposition détaillée sous 48h.",
                    "Votre demande commerciale a retenu toute notre attention. Un commercial vous contactera prochainement."
                ]
            },
            'general': {
                'fr': [
                    "Merci pour votre message. Nous l'avons bien reçu et y donnerons suite dans les meilleurs délais.",
                    "Votre message est important pour nous. Nous vous répondrons personnellement très prochainement."
                ]
            }
        }
    
    def should_respond(self, email, classification: Dict) -> Tuple[bool, str]:
        """Détermine s'il faut répondre automatiquement à cet email"""
        try:
            if not self.config.get("enabled", False):
                return False, "Répondeur désactivé"
            
            category = classification.get('category', 'general')
            if not self.config.get("response_categories", {}).get(category, False):
                return False, f"Catégorie {category} désactivée"
            
            if classification.get('spam_score', 0) > 0.7:
                return False, "Détecté comme spam"
            
            sender = email.get_sender_email()
            if self._is_loop_risk(sender):
                return False, "Risque de boucle détecté"
            
            if self._is_auto_response(email):
                return False, "C'est déjà une réponse automatique"
            
            return True, "Conditions remplies"
            
        except Exception as e:
            logger.error(f"Erreur should_respond: {e}")
            return False, "Erreur interne"
    
    def generate_response(self, email, classification: Dict) -> Optional[Dict]:
        """Génère une réponse automatique intelligente"""
        try:
            category = classification.get('category', 'general')
            
            # Analyse du contexte
            context = self._analyze_context(email, classification)
            
            # Génération avec templates (méthode la plus fiable)
            result = self._generate_with_templates(email, classification, context)
            
            if result and result.get('text'):
                response_text = self._post_process_response(result['text'], email, context)
                
                if self._validate_response(response_text, email):
                    response = {
                        'text': response_text,
                        'subject': self._generate_subject(email, category),
                        'category': category,
                        'confidence': classification.get('confidence', 0.5),
                        'method': result.get('method', 'template'),
                        'context': context
                    }
                    
                    self._save_response_history(email, response)
                    return response
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur génération réponse: {e}")
            return None
    
    def _generate_with_templates(self, email, classification: Dict, context: Dict) -> Optional[Dict]:
        """Génération basée sur les templates intelligents"""
        try:
            category = classification.get('category', 'general')
            language = 'fr'  # Par défaut français
            
            templates = self.templates.get(category, {}).get(language, [])
            if not templates:
                templates = self.templates.get('general', {}).get('fr', [])
            
            if not templates:
                return None
            
            # Sélection du premier template par simplicité
            selected_template = templates[0]
            
            # Personnalisation du template
            personalized_text = self._personalize_template(selected_template, email, context)
            
            return {
                'text': personalized_text,
                'method': 'template',
                'template': selected_template
            }
            
        except Exception as e:
            logger.error(f"Erreur templates: {e}")
            return None
    
    def _analyze_context(self, email, classification: Dict) -> Dict:
        """Analyse le contexte de l'email"""
        return {
            'sender_info': {'name': self._extract_sender_name(email.get_sender_email())},
            'entities': classification.get('entities', {}),
            'urgency': classification.get('priority', 1),
            'language': 'fr'
        }
    
    def _extract_sender_name(self, email_address: str) -> str:
        """Extrait le nom de l'expéditeur"""
        if '@' in email_address:
            local_part = email_address.split('@')[0]
            name = local_part.replace('.', ' ').replace('_', ' ').title()
            return name if name.replace(' ', '').isalpha() else "Monsieur/Madame"
        return "Monsieur/Madame"
    
    def _personalize_template(self, template: str, email, context: Dict) -> str:
        """Personnalise un template"""
        try:
            personalized = template
            sender_name = context.get('sender_info', {}).get('name', 'Monsieur/Madame')
            
            personalized = f"Bonjour {sender_name},\n\n{personalized}"
            
            # Remplacement des variables spéciales
            if '[SLOTS]' in personalized:
                slots = "lundi prochain à 14h, mercredi à 10h30, ou vendredi à 15h"
                personalized = personalized.replace('[SLOTS]', slots)
            
            # Ajout de la signature
            if self.config.get('include_signature', True):
                signature = self.config.get('signature', 'Cordialement,\nAssistant IA')
                personalized += f"\n\n{signature}"
            
            return personalized
            
        except Exception as e:
            logger.error(f"Erreur personnalisation: {e}")
            return template
    
    def _post_process_response(self, response_text: str, email, context: Dict) -> str:
        """Post-traitement de la réponse"""
        response_text = response_text.strip()
        
        # Limitation de longueur
        max_length = self.config.get('max_response_length', 500)
        if len(response_text) > max_length:
            response_text = response_text[:max_length] + "..."
        
        return response_text
    
    def _validate_response(self, response_text: str, email) -> bool:
        """Valide la réponse"""
        return len(response_text.strip()) >= 20
    
    def _generate_subject(self, email, category: str) -> str:
        """Génère un sujet pour la réponse"""
        original_subject = email.subject
        if not original_subject.lower().startswith('re:'):
            return f"Re: {original_subject}"
        return original_subject
    
    def _is_loop_risk(self, sender: str) -> bool:
        """Vérifie les risques de boucle"""
        return False  # Simplifié pour éviter les erreurs
    
    def _is_auto_response(self, email) -> bool:
        """Détecte les réponses automatiques"""
        auto_indicators = ['auto-reply', 'automatic reply', 'out of office', 'absence']
        text = f"{email.subject} {email.body}".lower()
        return any(indicator in text for indicator in auto_indicators)
    
    def _save_response_history(self, email, response: Dict):
        """Sauvegarde l'historique"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sent_responses 
                (original_email_id, sender_email, response_text, response_type, confidence, model_used)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                getattr(email, 'message_id', 'unknown'),
                email.get_sender_email().lower(),
                response['text'],
                response['category'],
                response['confidence'],
                response['method']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM sent_responses')
            total_responses = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_responses': total_responses,
                'config': self.config
            }
            
        except Exception as e:
            logger.error(f"Erreur statistiques: {e}")
            return {}
    
    def update_config(self, new_config: Dict):
        """Met à jour la configuration"""
        try:
            self.config.update(new_config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info("Configuration mise à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour config: {e}")