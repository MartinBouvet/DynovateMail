#!/usr/bin/env python3
"""
Processeur IA - AVEC GÉNÉRATION INTELLIGENTE
"""
import logging
import re
from typing import Optional
from dataclasses import dataclass

from models.email_model import Email

logger = logging.getLogger(__name__)

@dataclass
class AIAnalysis:
    """Résultat d'analyse IA."""
    category: str
    priority: int
    sentiment: str
    summary: str
    is_spam: bool
    confidence: float
    needs_response: bool = False

class AIProcessor:
    """Processeur IA pour analyse d'emails."""
    
    def __init__(self):
        logger.info("AIProcessor initialisé")
        
        self.spam_domains = [
            'instagram.com', 'facebook.com', 'twitter.com', 'tiktok.com',
            'linkedin.com', 'notifications', 'noreply', 'no-reply', 'mailer-daemon'
        ]
        
        self.spam_keywords = [
            'unsubscribe', 'se désabonner', 'newsletter', 'promotional',
            'limited time', 'click here', 'free', 'winner', 'suggestions pour vous',
            'suggested for you', 'friend suggestion', 'people you may know'
        ]
    
    def analyze_email(self, email: Email) -> Optional[AIAnalysis]:
        """Analyse un email."""
        try:
            full_text = f"{email.subject or ''} {email.body or ''} {email.snippet or ''}".lower()
            sender = (email.sender or '').lower()
            
            is_spam = self._detect_spam_advanced(email, sender, full_text)
            
            if is_spam:
                return AIAnalysis(
                    category="spam",
                    priority=1,
                    sentiment="Neutre",
                    summary="Email publicitaire ou spam détecté",
                    is_spam=True,
                    confidence=0.95,
                    needs_response=False
                )
            
            category = self._classify_category(email, full_text)
            priority = self._calculate_priority_improved(email, full_text, category)
            sentiment = self._analyze_sentiment(full_text)
            summary = self._generate_smart_summary(email, full_text)
            needs_response = self._needs_response(email, full_text, category)
            
            return AIAnalysis(
                category=category,
                priority=priority,
                sentiment=sentiment,
                summary=summary,
                is_spam=is_spam,
                confidence=0.85,
                needs_response=needs_response
            )
            
        except Exception as e:
            logger.error(f"Erreur analyse IA: {e}")
            return None
    
    def generate_smart_response(self, email: Email) -> str:
        """Génère une réponse intelligente basée sur le contenu de l'email."""
        try:
            # Extraire le contexte
            subject = email.subject or ""
            body_text = email.body or email.snippet or ""
            
            # Nettoyer le HTML
            if email.is_html:
                body_text = re.sub('<[^<]+?>', '', body_text)
            
            # Limiter à 500 caractères pour l'analyse
            body_text = body_text[:500]
            
            # Analyse du contenu
            text_lower = f"{subject} {body_text}".lower()
            
            # Détecter les questions
            questions = self._extract_questions(body_text)
            
            # Détecter le contexte
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                category = email.ai_analysis.category
            else:
                category = "general"
            
            # Générer la réponse selon le contexte
            response = self._generate_contextual_response(
                category=category,
                subject=subject,
                body_text=body_text,
                questions=questions,
                sender=email.sender or ""
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur génération réponse: {e}")
            return "Bonjour,\n\nMerci pour votre message. Nous avons bien pris en compte votre demande.\n\nCordialement"
    
    def _extract_questions(self, text: str) -> list:
        """Extrait les questions du texte."""
        sentences = re.split(r'[.!?]+', text)
        questions = [s.strip() + '?' for s in sentences if '?' in s or any(word in s.lower() for word in ['comment', 'quand', 'pourquoi', 'qui', 'quoi', 'où', 'how', 'when', 'why', 'who', 'what', 'where'])]
        return questions[:3]  # Limiter à 3 questions
    
    def _generate_contextual_response(self, category: str, subject: str, body_text: str, questions: list, sender: str) -> str:
        """Génère une réponse contextuelle basée sur l'analyse."""
        
        # Extraire le prénom si possible
        first_name = ""
        if sender and '<' in sender:
            name_part = sender.split('<')[0].strip()
            if name_part:
                first_name = name_part.split()[0]
        
        greeting = f"Bonjour {first_name},\n\n" if first_name else "Bonjour,\n\n"
        
        if category == "cv":
            return f"""{greeting}Merci pour l'envoi de votre candidature{f' concernant {subject}' if subject else ''}.

Nous avons bien reçu votre CV et nous l'examinerons avec attention. Votre profil sera étudié par notre équipe de recrutement.

Nous reviendrons vers vous dans les prochains jours si votre profil correspond à nos besoins actuels.

Nous vous remercions de l'intérêt que vous portez à notre entreprise.

Cordialement,
L'équipe Recrutement"""
        
        elif category == "meeting":
            has_date_request = any(word in body_text.lower() for word in ['quand', 'when', 'disponibilité', 'disponible', 'rendez-vous', 'meeting'])
            
            if has_date_request:
                return f"""{greeting}Merci pour votre demande de rendez-vous{f' concernant {subject}' if subject else ''}.

Je serais ravi d'échanger avec vous sur ce sujet.

Voici quelques créneaux qui pourraient me convenir:
- Mardi prochain - 10h00 ou 14h30
- Mercredi prochain - 11h00 ou 15h00
- Jeudi prochain - 9h30 ou 16h00

N'hésitez pas à me confirmer le créneau qui vous convient le mieux, ou à me proposer d'autres options si ceux-ci ne vous conviennent pas.

Au plaisir d'échanger avec vous.

Cordialement"""
            else:
                return f"""{greeting}Merci pour votre message{f' concernant {subject}' if subject else ''}.

Je prends bonne note de votre demande de rendez-vous. Pourriez-vous me préciser vos disponibilités afin que nous puissions organiser notre échange dans les meilleures conditions ?

Je reste à votre disposition.

Cordialement"""
        
        elif category == "support":
            has_problem = any(word in body_text.lower() for word in ['problème', 'erreur', 'bug', 'ne fonctionne pas', 'problem', 'error', 'issue'])
            
            if has_problem:
                return f"""{greeting}Merci de nous avoir contacté{f' concernant {subject}' if subject else ''}.

Nous avons bien pris en compte votre demande de support et nous comprenons votre situation.

Notre équipe technique va analyser le problème que vous rencontrez et nous reviendrons vers vous rapidement avec une solution.

Si vous avez des informations complémentaires qui pourraient nous aider à résoudre ce problème plus rapidement, n'hésitez pas à nous les transmettre.

Nous mettons tout en œuvre pour résoudre cette situation au plus vite.

Cordialement,
L'équipe Support"""
            else:
                return f"""{greeting}Merci pour votre message.

Nous avons bien reçu votre demande et nous allons l'examiner avec attention.

Notre équipe reviendra vers vous dans les plus brefs délais avec les informations demandées.

N'hésitez pas à nous recontacter si vous avez besoin d'informations complémentaires.

Cordialement,
L'équipe Support"""
        
        elif category == "invoice":
            return f"""{greeting}Merci pour votre message{f' concernant {subject}' if subject else ''}.

Nous avons bien pris en compte votre demande concernant la facturation.

Notre service comptabilité va traiter votre demande et reviendra vers vous avec les informations nécessaires dans les 48 heures.

Si vous avez des questions complémentaires, notre équipe reste à votre disposition.

Cordialement,
Le service Comptabilité"""
        
        # Réponse générique intelligente
        else:
            # Analyser si c'est une question
            if questions:
                return f"""{greeting}Merci pour votre message{f' concernant {subject}' if subject else ''}.

J'ai bien pris connaissance de vos questions:
{chr(10).join('• ' + q for q in questions)}

Je vais examiner ces points et vous apporter une réponse détaillée dans les plus brefs délais.

N'hésitez pas si vous avez besoin de précisions supplémentaires.

Cordialement"""
            
            # Réponse standard mais personnalisée
            return f"""{greeting}Merci pour votre message{f' concernant {subject}' if subject else ''}.

J'ai bien pris connaissance de votre demande et je vais l'examiner attentivement.

Je reviendrai vers vous rapidement avec les informations nécessaires.

Restant à votre disposition pour tout complément d'information.

Cordialement"""
    
    def _detect_spam_advanced(self, email: Email, sender: str, text: str) -> bool:
        """Détection de spam avancée."""
        spam_score = 0
        
        for domain in self.spam_domains:
            if domain in sender:
                spam_score += 3
        
        spam_keyword_count = sum(1 for keyword in self.spam_keywords if keyword in text)
        spam_score += spam_keyword_count
        
        if any(word in sender for word in ['noreply', 'no-reply', 'notification', 'automated']):
            spam_score += 2
        
        subject_lower = (email.subject or '').lower()
        if any(word in subject_lower for word in ['unsubscribe', 'newsletter', 'promotional']):
            spam_score += 2
        
        link_count = text.count('http')
        if link_count > 5:
            spam_score += 2
        
        return spam_score >= 3
    
    def _classify_category(self, email: Email, text: str) -> str:
        """Classifie la catégorie."""
        cv_keywords = ['cv', 'curriculum', 'candidature', 'postuler', 'emploi', 'recrutement']
        meeting_keywords = ['rendez-vous', 'rdv', 'reunion', 'meeting', 'appointment', 'calendrier']
        invoice_keywords = ['facture', 'invoice', 'paiement', 'payment', 'prix', '€', '$']
        support_keywords = ['support', 'aide', 'probleme', 'bug', 'erreur', 'help']
        
        cv_score = sum(1 for kw in cv_keywords if kw in text)
        meeting_score = sum(1 for kw in meeting_keywords if kw in text)
        invoice_score = sum(1 for kw in invoice_keywords if kw in text)
        support_score = sum(1 for kw in support_keywords if kw in text)
        
        scores = {
            'cv': cv_score,
            'meeting': meeting_score,
            'invoice': invoice_score,
            'support': support_score
        }
        
        max_score = max(scores.values())
        if max_score >= 2:
            for category, score in scores.items():
                if score == max_score:
                    return category
        
        return "important"
    
    def _calculate_priority_improved(self, email: Email, text: str, category: str) -> int:
        """Calcule la priorité."""
        priority = 3
        
        urgent_keywords = ['urgent', 'asap', 'important', 'prioritaire', 'critique']
        if any(kw in text for kw in urgent_keywords):
            priority += 2
        
        if not email.is_read:
            priority += 1
        
        if category == 'support':
            priority += 1
        elif category == 'meeting':
            priority += 1
        
        return max(1, min(5, priority))
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyse le sentiment."""
        positive_keywords = ['merci', 'excellent', 'parfait', 'super', 'genial', 'thanks', 'great']
        negative_keywords = ['probleme', 'erreur', 'bug', 'mecontent', 'plainte', 'issue']
        
        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)
        
        if positive_count > negative_count + 1:
            return "Positif"
        elif negative_count > positive_count + 1:
            return "Négatif"
        else:
            return "Neutre"
    
    def _generate_smart_summary(self, email: Email, text: str) -> str:
        """Génère un résumé intelligent."""
        if email.snippet and len(email.snippet) > 20:
            summary = email.snippet.strip()
            if len(summary) > 150:
                summary = summary[:150] + "..."
            return summary
        
        if email.body:
            clean_text = re.sub('<[^<]+?>', '', email.body)
            clean_text = clean_text.strip()
            sentences = re.split(r'[.!?]+', clean_text)
            summary = '. '.join(s.strip() for s in sentences[:2] if s.strip())
            if len(summary) > 150:
                summary = summary[:150] + "..."
            return summary if summary else "Aucun résumé disponible"
        
        return "Email vide"
    
    def _needs_response(self, email: Email, text: str, category: str) -> bool:
        """Détermine si besoin de réponse."""
        sender = (email.sender or '').lower()
        
        for domain in self.spam_domains:
            if domain in sender:
                return False
        
        if 'noreply' in sender or 'no-reply' in sender:
            return False
        
        response_categories = ['cv', 'meeting', 'support', 'invoice']
        if category in response_categories:
            return True
        
        question_keywords = ['?', 'question', 'pouvez-vous', 'can you', 'could you']
        if any(kw in text for kw in question_keywords):
            return True
        
        if not email.is_read and email.received_date:
            from datetime import datetime, timezone, timedelta
            age = datetime.now(timezone.utc) - email.received_date
            if age < timedelta(days=2):
                return True
        
        return False