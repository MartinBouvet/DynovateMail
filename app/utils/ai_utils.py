"""
Utilitaires pour l'intelligence artificielle - VERSION LOCALE.
"""
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Import conditionnel pour éviter les erreurs
try:
    import dateutil.parser as date_parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
    logging.warning("dateutil non disponible - parsing de dates simplifié")

logger = logging.getLogger(__name__)

def extract_datetime(text: str) -> Optional[Dict[str, datetime]]:
    """
    Extrait les informations de date et heure d'un texte (VERSION LOCALE).
    
    Args:
        text: Le texte à analyser.
        
    Returns:
        Dictionnaire avec start_time et end_time ou None.
    """
    try:
        # Patterns pour les dates en français
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{1,2}) (janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) (\d{4})',  # DD mois YYYY
            r'(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche) (\d{1,2}) (janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',  # jour DD mois
        ]
        
        # Patterns pour les heures
        time_patterns = [
            r'(\d{1,2})[h:](\d{2})',        # HH:MM ou HHhMM
            r'(\d{1,2})\s*(h|heures?)',     # HH h
            r'(\d{1,2})[h:](\d{2})\s*(am|pm)?',  # avec AM/PM
        ]
        
        # Rechercher les dates
        dates_found = []
        text_lower = text.lower()
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    if len(match) == 3:
                        if match[1].isdigit():  # DD/MM/YYYY format
                            day, month, year = int(match[0]), int(match[1]), int(match[2])
                            date_obj = datetime(year, month, day)
                        else:  # DD mois YYYY format
                            months = {
                                'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
                                'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
                            }
                            day, month_name, year = int(match[0]), match[1], int(match[2])
                            month = months.get(month_name, 1)
                            date_obj = datetime(year, month, day)
                        dates_found.append(date_obj)
                except (ValueError, TypeError):
                    continue
        
        # Rechercher les heures
        times_found = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) >= 2:
                        hour = int(match[0])
                        minute = int(match[1]) if len(match) > 1 and match[1].isdigit() else 0
                        
                        # Gérer AM/PM
                        if len(match) > 2 and match[2]:
                            if match[2] == 'pm' and hour != 12:
                                hour += 12
                            elif match[2] == 'am' and hour == 12:
                                hour = 0
                        
                        times_found.append((hour, minute))
                except (ValueError, TypeError):
                    continue
        
        # Combiner dates et heures
        if dates_found:
            base_date = dates_found[0]
            
            if times_found:
                hour, minute = times_found[0]
                start_time = base_date.replace(hour=hour, minute=minute)
                
                # Essayer de trouver une heure de fin
                end_time = None
                if len(times_found) > 1:
                    end_hour, end_minute = times_found[1]
                    end_time = base_date.replace(hour=end_hour, minute=end_minute)
                else:
                    # Durée par défaut de 1 heure
                    end_time = start_time + timedelta(hours=1)
                
                return {
                    'start_time': start_time,
                    'end_time': end_time
                }
            else:
                # Pas d'heure spécifiée, créer un événement toute la journée
                return {
                    'start_time': base_date.replace(hour=9, minute=0),
                    'end_time': base_date.replace(hour=17, minute=0)
                }
        
        # Rechercher des expressions relatives
        relative_patterns = [
            (r'demain', 1),
            (r'après[- ]demain', 2),
            (r'dans (\d+) jours?', None),
            (r'la semaine prochaine', 7),
            (r'(lundi|mardi|mercredi|jeudi|vendredi) prochain', None),
        ]
        
        for pattern, days_offset in relative_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if days_offset is None and pattern.startswith(r'dans'):
                    try:
                        days_offset = int(match.group(1))
                    except:
                        continue
                elif days_offset is None:  # jour de la semaine
                    weekdays = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi']
                    day_name = match.group(1)
                    if day_name in weekdays:
                        current_weekday = datetime.now().weekday()
                        target_weekday = weekdays.index(day_name)
                        days_offset = (target_weekday - current_weekday) % 7
                        if days_offset == 0:
                            days_offset = 7  # Semaine prochaine
                
                if days_offset is not None:
                    target_date = datetime.now() + timedelta(days=days_offset)
                    
                    # Essayer de trouver une heure
                    if times_found:
                        hour, minute = times_found[0]
                        start_time = target_date.replace(hour=hour, minute=minute)
                        end_time = start_time + timedelta(hours=1)
                    else:
                        start_time = target_date.replace(hour=9, minute=0)
                        end_time = target_date.replace(hour=17, minute=0)
                    
                    return {
                        'start_time': start_time,
                        'end_time': end_time
                    }
        
        return None
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de date/heure: {e}")
        return None

def extract_contact_info(text: str) -> Dict[str, str]:
    """
    Extrait les informations de contact d'un texte.
    
    Args:
        text: Le texte à analyser.
        
    Returns:
        Dictionnaire avec les informations de contact.
    """
    contact_info = {}
    
    try:
        # Numéros de téléphone français
        phone_patterns = [
            r'(?:\+33|0)[1-9](?:[0-9]{8})',  # Format français
            r'(?:\+\d{1,3})?[- ]?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}',  # Format international
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                contact_info['phone'] = matches[0]
                break
        
        # Adresses email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Adresses physiques
        address_patterns = [
            r'\d+\s+[\w\s]+(?:rue|avenue|boulevard|place|impasse|allée)\s+[\w\s]+',
            r'(?:rue|avenue|boulevard|place|impasse|allée)\s+[\w\s]+\s+\d+',
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact_info['address'] = matches[0]
                break
        
        # Lieux/salles
        location_patterns = [
            r'(?:salle|bureau|local|étage)\s+[\w\s\d]+',
            r'(?:au|à la|à l\'|dans le|dans la)\s+[\w\s]+',
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact_info['location'] = matches[0]
                break
        
        return contact_info
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction d'informations de contact: {e}")
        return {}

def clean_text(text: str) -> str:
    """
    Nettoie un texte en supprimant les caractères indésirables.
    
    Args:
        text: Le texte à nettoyer.
        
    Returns:
        Le texte nettoyé.
    """
    try:
        # Supprimer les caractères spéciaux
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\'\"àâäçéèêëïîôùûüÿ]', '', text)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les espaces en début/fin
        text = text.strip()
        
        return text
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du texte: {e}")
        return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extrait les mots-clés d'un texte.
    
    Args:
        text: Le texte à analyser.
        max_keywords: Nombre maximum de mots-clés à retourner.
        
    Returns:
        Liste des mots-clés.
    """
    try:
        # Mots vides en français
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'à', 'il',
            'elle', 'on', 'ils', 'elles', 'je', 'tu', 'nous', 'vous', 'me', 'te',
            'se', 'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son', 'ma', 'ta',
            'sa', 'mes', 'tes', 'ses', 'notre', 'votre', 'leur', 'dans', 'pour',
            'avec', 'sans', 'sur', 'sous', 'par', 'en', 'au', 'aux', 'du', 'des',
            'que', 'qui', 'quoi', 'dont', 'où', 'si', 'mais', 'ou', 'donc', 'car',
            'ni', 'or', 'est', 'être', 'avoir', 'faire', 'aller', 'venir', 'voir',
            'savoir', 'pouvoir', 'vouloir', 'devoir', 'falloir', 'prendre', 'dire',
            'mettre', 'donner', 'passer', 'partir', 'sortir', 'venir', 'arriver',
            'entrer', 'monter', 'descendre', 'rester', 'tenir', 'porter', 'suivre'
        }
        
        # Nettoyer le texte et extraire les mots
        words = re.findall(r'\b[a-zA-Zàâäçéèêëïîôùûüÿ]+\b', text.lower())
        
        # Filtrer les mots vides et courts
        filtered_words = [
            word for word in words
            if word not in stop_words and len(word) > 2
        ]
        
        # Compter les occurrences
        word_count = {}
        for word in filtered_words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Trier par fréquence et retourner les top mots-clés
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, count in sorted_words[:max_keywords]]
        
        return keywords
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des mots-clés: {e}")
        return []

def is_professional_email(email_address: str) -> bool:
    """
    Détermine si une adresse email est professionnelle.
    
    Args:
        email_address: L'adresse email à analyser.
        
    Returns:
        True si l'email semble professionnel, False sinon.
    """
    try:
        # Domaines personnels courants
        personal_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'free.fr', 'orange.fr', 'wanadoo.fr', 'sfr.fr',
            'laposte.net', 'numericable.fr', 'bbox.fr'
        ]
        
        domain = email_address.split('@')[1].lower()
        
        # Si le domaine est dans la liste des domaines personnels
        if domain in personal_domains:
            return False
        
        # Vérifier si le domaine contient des mots-clés professionnels
        professional_keywords = [
            'company', 'corp', 'inc', 'ltd', 'sa', 'sarl', 'sas',
            'groupe', 'consulting', 'services', 'solutions'
        ]
        
        if any(keyword in domain for keyword in professional_keywords):
            return True
        
        # Si le domaine n'est pas personnel et semble être un domaine d'entreprise
        return '.' in domain and len(domain.split('.')) >= 2
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'email professionnel: {e}")
        return False

def calculate_email_importance(email_content: str, sender_email: str) -> int:
    """
    Calcule l'importance d'un email sur une échelle de 1 à 5.
    
    Args:
        email_content: Le contenu de l'email.
        sender_email: L'adresse de l'expéditeur.
        
    Returns:
        Score d'importance (1-5).
    """
    try:
        importance = 1
        content_lower = email_content.lower()
        
        # Mots-clés d'urgence
        urgent_keywords = [
            'urgent', 'asap', 'immédiat', 'priorité', 'deadline',
            'échéance', 'time-sensitive', 'critique', 'important'
        ]
        
        if any(keyword in content_lower for keyword in urgent_keywords):
            importance += 2
        
        # Vérifier si c'est un email professionnel
        if is_professional_email(sender_email):
            importance += 1
        
        # Mots-clés de business
        business_keywords = [
            'contrat', 'projet', 'client', 'réunion', 'meeting',
            'deadline', 'budget', 'facture', 'commande'
        ]
        
        if any(keyword in content_lower for keyword in business_keywords):
            importance += 1
        
        # Limiter à 5
        return min(importance, 5)
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul d'importance: {e}")
        return 1

logger = logging.getLogger(__name__)

def extract_datetime(text: str) -> Optional[Dict[str, datetime]]:
    """
    Extrait les informations de date et heure d'un texte.
    
    Args:
        text: Le texte à analyser.
        
    Returns:
        Dictionnaire avec start_time et end_time ou None.
    """
    try:
        # Patterns pour les dates en français
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{1,2}) (\w+) (\d{4})',      # DD mois YYYY
            r'(\w+) (\d{1,2}), (\d{4})',     # mois DD, YYYY
        ]
        
        # Patterns pour les heures
        time_patterns = [
            r'(\d{1,2})[h:](\d{2})',        # HH:MM ou HHhMM
            r'(\d{1,2})[h:](\d{2})\s*(am|pm)?',  # avec AM/PM
            r'(\d{1,2})\s*(h|heures?)',     # HH h
        ]
        
        # Rechercher les dates
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    if len(match) == 3:
                        if match[1].isdigit():  # DD/MM/YYYY format
                            date_str = f"{match[0]}/{match[1]}/{match[2]}"
                            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                        else:  # DD mois YYYY format
                            date_str = f"{match[0]} {match[1]} {match[2]}"
                            date_obj = date_parser.parse(date_str, dayfirst=True)
                        dates_found.append(date_obj)
                except (ValueError, TypeError):
                    continue
        
        # Rechercher les heures
        times_found = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) >= 2:
                        hour = int(match[0])
                        minute = int(match[1]) if match[1].isdigit() else 0
                        
                        # Gérer AM/PM
                        if len(match) > 2 and match[2]:
                            if match[2] == 'pm' and hour != 12:
                                hour += 12
                            elif match[2] == 'am' and hour == 12:
                                hour = 0
                        
                        times_found.append((hour, minute))
                except (ValueError, TypeError):
                    continue
        
        # Combiner dates et heures
        if dates_found:
            base_date = dates_found[0]
            
            if times_found:
                hour, minute = times_found[0]
                start_time = base_date.replace(hour=hour, minute=minute)
                
                # Essayer de trouver une heure de fin
                end_time = None
                if len(times_found) > 1:
                    end_hour, end_minute = times_found[1]
                    end_time = base_date.replace(hour=end_hour, minute=end_minute)
                else:
                    # Durée par défaut de 1 heure
                    end_time = start_time + timedelta(hours=1)
                
                return {
                    'start_time': start_time,
                    'end_time': end_time
                }
            else:
                # Pas d'heure spécifiée, créer un événement toute la journée
                return {
                    'start_time': base_date.replace(hour=9, minute=0),
                    'end_time': base_date.replace(hour=17, minute=0)
                }
        
        # Rechercher des expressions relatives
        relative_patterns = [
            (r'demain', 1),
            (r'après[- ]demain', 2),
            (r'dans (\d+) jours?', None),
            (r'la semaine prochaine', 7),
            (r'lundi prochain', None),
            (r'mardi prochain', None),
            (r'mercredi prochain', None),
            (r'jeudi prochain', None),
            (r'vendredi prochain', None),
        ]
        
        for pattern, days_offset in relative_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if days_offset is None and pattern.startswith(r'dans'):
                    days_offset = int(match.group(1))
                elif days_offset is None:  # jour de la semaine
                    weekdays = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi']
                    day_name = pattern.split()[0]
                    if day_name in weekdays:
                        current_weekday = datetime.now().weekday()
                        target_weekday = weekdays.index(day_name)
                        days_offset = (target_weekday - current_weekday) % 7
                        if days_offset == 0:
                            days_offset = 7  # Semaine prochaine
                
                if days_offset is not None:
                    target_date = datetime.now() + timedelta(days=days_offset)
                    
                    # Essayer de trouver une heure
                    if times_found:
                        hour, minute = times_found[0]
                        start_time = target_date.replace(hour=hour, minute=minute)
                        end_time = start_time + timedelta(hours=1)
                    else:
                        start_time = target_date.replace(hour=9, minute=0)
                        end_time = target_date.replace(hour=17, minute=0)
                    
                    return {
                        'start_time': start_time,
                        'end_time': end_time
                    }
        
        return None
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de date/heure: {e}")
        return None

def extract_contact_info(text: str) -> Dict[str, str]:
    """
    Extrait les informations de contact d'un texte.
    
    Args:
        text: Le texte à analyser.
        
    Returns:
        Dictionnaire avec les informations de contact.
    """
    contact_info = {}
    
    try:
        # Numéros de téléphone
        phone_patterns = [
            r'(?:\+33|0)[1-9](?:[0-9]{8})',  # Français
            r'(?:\+\d{1,3})?[- ]?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}',  # Général
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                contact_info['phone'] = matches[0]
                break
        
        # Adresses email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Adresses
        address_patterns = [
            r'\d+\s+[\w\s]+(?:rue|avenue|boulevard|place|impasse|allée)\s+[\w\s]+',
            r'(?:rue|avenue|boulevard|place|impasse|allée)\s+[\w\s]+\s+\d+',
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact_info['address'] = matches[0]
                break
        
        # Lieux/salles
        location_patterns = [
            r'(?:salle|bureau|local|étage)\s+[\w\s\d]+',
            r'(?:au|à la|à l\'|dans le|dans la)\s+[\w\s]+',
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact_info['location'] = matches[0]
                break
        
        return contact_info
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction d'informations de contact: {e}")
        return {}

def clean_text(text: str) -> str:
    """
    Nettoie un texte en supprimant les caractères indésirables.
    
    Args:
        text: Le texte à nettoyer.
        
    Returns:
        Le texte nettoyé.
    """
    try:
        # Supprimer les caractères spéciaux
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\'\"àâäçéèêëïîôùûüÿ]', '', text)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les espaces en début/fin
        text = text.strip()
        
        return text
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du texte: {e}")
        return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extrait les mots-clés d'un texte.
    
    Args:
        text: Le texte à analyser.
        max_keywords: Nombre maximum de mots-clés à retourner.
        
    Returns:
        Liste des mots-clés.
    """
    try:
        # Mots vides en français
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'à', 'il',
            'elle', 'on', 'ils', 'elles', 'je', 'tu', 'nous', 'vous', 'me', 'te',
            'se', 'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son', 'ma', 'ta',
            'sa', 'mes', 'tes', 'ses', 'notre', 'votre', 'leur', 'dans', 'pour',
            'avec', 'sans', 'sur', 'sous', 'par', 'en', 'au', 'aux', 'du', 'des',
            'que', 'qui', 'quoi', 'dont', 'où', 'si', 'mais', 'ou', 'donc', 'car',
            'ni', 'or', 'est', 'être', 'avoir', 'faire', 'aller', 'venir', 'voir',
            'savoir', 'pouvoir', 'vouloir', 'devoir', 'falloir', 'prendre', 'dire',
            'mettre', 'donner', 'passer', 'partir', 'sortir', 'venir', 'arriver',
            'entrer', 'monter', 'descendre', 'rester', 'tenir', 'porter', 'suivre'
        }
        
        # Nettoyer le texte et extraire les mots
        words = re.findall(r'\b[a-zA-Zàâäçéèêëïîôùûüÿ]+\b', text.lower())
        
        # Filtrer les mots vides et courts
        filtered_words = [
            word for word in words
            if word not in stop_words and len(word) > 2
        ]
        
        # Compter les occurrences
        word_count = {}
        for word in filtered_words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Trier par fréquence et retourner les top mots-clés
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, count in sorted_words[:max_keywords]]
        
        return keywords
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des mots-clés: {e}")
        return []

def is_professional_email(email_address: str) -> bool:
    """
    Détermine si une adresse email est professionnelle.
    
    Args:
        email_address: L'adresse email à analyser.
        
    Returns:
        True si l'email semble professionnel, False sinon.
    """
    try:
        # Domaines personnels courants
        personal_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'free.fr', 'orange.fr', 'wanadoo.fr', 'sfr.fr',
            'laposte.net', 'numericable.fr', 'bbox.fr'
        ]
        
        domain = email_address.split('@')[1].lower()
        
        # Si le domaine est dans la liste des domaines personnels
        if domain in personal_domains:
            return False
        
        # Vérifier si le domaine contient des mots-clés professionnels
        professional_keywords = [
            'company', 'corp', 'inc', 'ltd', 'sa', 'sarl', 'sas',
            'groupe', 'consulting', 'services', 'solutions'
        ]
        
        if any(keyword in domain for keyword in professional_keywords):
            return True
        
        # Si le domaine n'est pas personnel et semble être un domaine d'entreprise
        return '.' in domain and len(domain.split('.')) >= 2
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'email professionnel: {e}")
        return False

def calculate_email_importance(email_content: str, sender_email: str) -> int:
    """
    Calcule l'importance d'un email sur une échelle de 1 à 5.
    
    Args:
        email_content: Le contenu de l'email.
        sender_email: L'adresse de l'expéditeur.
        
    Returns:
        Score d'importance (1-5).
    """
    try:
        importance = 1
        content_lower = email_content.lower()
        
        # Mots-clés d'urgence
        urgent_keywords = [
            'urgent', 'asap', 'immédiat', 'priorité', 'deadline',
            'échéance', 'time-sensitive', 'critique', 'important'
        ]
        
        if any(keyword in content_lower for keyword in urgent_keywords):
            importance += 2
        
        # Vérifier si c'est un email professionnel
        if is_professional_email(sender_email):
            importance += 1
        
        # Mots-clés de business
        business_keywords = [
            'contrat', 'projet', 'client', 'réunion', 'meeting',
            'deadline', 'budget', 'facture', 'commande'
        ]
        
        if any(keyword in content_lower for keyword in business_keywords):
            importance += 1
        
        # Limiter à 5
        return min(importance, 5)
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul d'importance: {e}")
        return 1