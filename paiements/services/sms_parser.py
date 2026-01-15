# paiements/services/sms_parser.py
import re
import json
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class SMSParser:
    """Service de parsing des SMS de paiement mobile"""
    
    @staticmethod
    def detect_operator(sms_content, sender=None):
        """Détecte l'opérateur à partir du contenu du SMS"""
        sms_lower = sms_content.lower()
        
        # Détection par mots-clés
        if any(keyword in sms_lower for keyword in ['moov', 'tigo cash', 'tigo']):
            return 'moov'
        elif any(keyword in sms_lower for keyword in ['orange', 'orange money']):
            return 'orange'
        elif any(keyword in sms_lower for keyword in ['wave', 'wave money']):
            return 'wave'
        
        # Détection par numéro expéditeur
        if sender:
            if sender in ['10', '22310', '*100#']:
                return 'moov'
            elif sender in ['11', '22311', '*150#']:
                return 'orange'
            elif sender in ['22390']:
                return 'wave'
        
        return 'unknown'
    
    @staticmethod
    def parse_moov_sms(sms_content):
        """Parse les SMS Moov Money"""
        try:
            result = {
                'amount': None,
                'sender_phone': None,
                'date': None,
                'transaction_id': None,
                'balance': None,
                'sender_name': None,
                'raw_content': sms_content
            }
            
            # Extraction du montant (format: 10 100,00 FCFA ou 10100 FCFA)
            amount_patterns = [
                r'(\d[\d\s]*(?:\.|,)\d{2})\s*FCFA',
                r'(\d[\d\s]*)\s*FCFA',
                r'recu\s*(\d[\d\s]*)\s*F',
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, sms_content.replace(',', '.'))
                if match:
                    amount_str = match.group(1).replace(' ', '').replace(',', '.')
                    try:
                        result['amount'] = Decimal(amount_str)
                        break
                    except:
                        pass
            
            # Extraction du numéro expéditeur
            phone_patterns = [
                r'Numero\s*(\d{8,15})',
                r'de\s*(\d{8,15})',
                r'(\+?226[67]\d{7})',
                r'(\b[67]\d{7}\b)'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, sms_content)
                if match:
                    phone = match.group(1).replace(' ', '')
                    if phone.startswith('226'):
                        phone = '+' + phone
                    elif len(phone) == 8:
                        phone = '+226' + phone
                    result['sender_phone'] = phone
                    break
            
            # Extraction de la date
            date_patterns = [
                r'Date:\s*(\d{2}/\d{2}/\d{4}\s*\d{1,2}H?\d{2})',
                r'le\s*(\d{2}/\d{2}/\d{4}\s*\d{1,2}:\d{2})',
                r'(\d{2}/\d{2}/\d{4}\s*\d{1,2}H?\d{2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, sms_content)
                if match:
                    date_str = match.group(1).replace('H', ':')
                    try:
                        result['date'] = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                    except:
                        try:
                            result['date'] = datetime.strptime(date_str, '%d/%m/%Y %H%M')
                        except:
                            pass
                    break
            
            # Extraction de l'ID de transaction
            id_patterns = [
                r'TID:\s*(\S+)',
                r'Ref:\s*(\S+)',
                r'(\b[A-Z]{2}\d{6}\.\d{4}\.[A-Z]\d{5}\b)',
                r'(\b[A-Z]{2}\d{6}\b)'
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, sms_content)
                if match:
                    result['transaction_id'] = match.group(1)
                    break
            
            # Extraction du solde
            balance_match = re.search(r'Solde:\s*([\d\s,]+\.?\d{0,2})\s*FCFA', sms_content)
            if balance_match:
                balance_str = balance_match.group(1).replace(' ', '').replace(',', '.')
                try:
                    result['balance'] = Decimal(balance_str)
                except:
                    pass
            
            # Extraction du nom
            name_match = re.search(r'de\s+([A-Za-z\s]+(?:[A-Za-z]|$))', sms_content)
            if name_match:
                result['sender_name'] = name_match.group(1).strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur parsing Moov SMS: {str(e)}")
            return None
    
    @staticmethod
    def parse_orange_sms(sms_content):
        """Parse les SMS Orange Money"""
        try:
            result = {
                'amount': None,
                'sender_phone': None,
                'transaction_id': None,
                'balance': None,
                'raw_content': sms_content
            }
            
            # Formats Orange Money courants
            patterns = [
                # Format 1: Vous avez recu 5000 FCFA du 77889900
                r'(?:recu|reçu)\s*(\d+)\s*FCFA\s*(?:du|de|depuis)\s*(\d{8,10})',
                # Format 2: Transaction recue: 2500 FCFA. Votre nouveau solde: 12500 FCFA
                r'Transaction\s*recue[:\s]*(\d+)\s*FCFA',
                # Format 3: Vous venez de recevoir 10000 FCFA de 70707070
                r'recevoir\s*(\d+)\s*FCFA\s*(?:de|du)\s*(\d{8,10})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, sms_content, re.IGNORECASE)
                if match:
                    try:
                        result['amount'] = Decimal(match.group(1))
                        if match.lastindex >= 2:
                            phone = match.group(2)
                            if len(phone) == 8:
                                phone = '+226' + phone
                            result['sender_phone'] = phone
                    except:
                        pass
                    break
            
            # Extraction ID transaction
            id_match = re.search(r'(?:ID|Ref|Reference)[:\s]*(\S+)', sms_content, re.IGNORECASE)
            if id_match:
                result['transaction_id'] = id_match.group(1)
            
            # Extraction solde
            balance_match = re.search(r'(?:solde|nouveau solde)[:\s]*(\d+)\s*FCFA', sms_content, re.IGNORECASE)
            if balance_match:
                try:
                    result['balance'] = Decimal(balance_match.group(1))
                except:
                    pass
            
            # Si pas de numéro trouvé, chercher un numéro dans le SMS
            if not result['sender_phone']:
                phone_match = re.search(r'(\b[67]\d{7}\b)', sms_content)
                if phone_match:
                    phone = phone_match.group(1)
                    if len(phone) == 8:
                        phone = '+226' + phone
                    result['sender_phone'] = phone
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur parsing Orange SMS: {str(e)}")
            return None
    
    @staticmethod
    def parse_sms(sms_content, sender=None):
        """Parse un SMS et détecte l'opérateur"""
        try:
            # Détecter l'opérateur
            operator = SMSParser.detect_operator(sms_content, sender)
            
            # Parser selon l'opérateur
            if operator == 'moov':
                parsed_data = SMSParser.parse_moov_sms(sms_content)
            elif operator == 'orange':
                parsed_data = SMSParser.parse_orange_sms(sms_content)
            else:
                parsed_data = None
            
            log_entry = {
                'operator': operator,
                'parsed_successfully': parsed_data is not None,
                'timestamp': timezone.now().isoformat()
            }
            
            return operator, parsed_data, log_entry
            
        except Exception as e:
            logger.error(f"Erreur parsing SMS: {str(e)}")
            return 'unknown', None, {'error': str(e)}
