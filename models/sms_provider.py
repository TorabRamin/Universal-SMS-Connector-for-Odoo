from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import boto3
import logging

_logger = logging.getLogger(__name__)

class SMSProvider(models.Model):
    _name = 'sms.provider'
    _description = 'SMS Gateway Provider'
    _order = 'priority asc'

    name = fields.Char(required=True)
    provider_type = fields.Selection([
        ('boomcast', 'Boomcast (BD)'),
        ('mimsms', 'MiMSMS (BD)'),
        ('aws_sns', 'Amazon SNS'),
        ('generic', 'Generic HTTP')
    ], string="Provider Type", required=True)
    
    state = fields.Selection([('enabled', 'Enabled'), ('disabled', 'Disabled')], default='enabled')
    priority = fields.Integer(default=10, help="Lower number = Higher priority for Load Balancing")
    
    # Credentials
    api_url = fields.Char(string="Base API URL")
    api_username = fields.Char()
    api_password = fields.Char()
    api_key = fields.Char()
    sender_id = fields.Char(string="Masking/Sender ID", help="Brand name or Approved Sender ID")
    
    # Specifics
    mimsms_campaign_id = fields.Char(string="MiMSMS Campaign ID")
    aws_region_name = fields.Char(default='us-east-1')
    aws_access_key = fields.Char()
    aws_secret_key = fields.Char()
    
    # Settings
    is_unicode_supported = fields.Boolean(default=True)
    daily_limit = fields.Integer(string="Daily SMS Limit", default=0)
    
    def check_unicode(self, message):
        """Helper to detect if message requires Unicode handling"""
        try:
            message.encode('ascii')
            return False
        except UnicodeEncodeError:
            return True

    def _sanitize_number(self, number):
        """Ensure number format is standard (e.g., remove +, spaces)"""
        if not number:
            return False
        return number.replace(' ', '').replace('-', '').replace('+', '')

    # ---------------------------------------------------------
    # PUBLIC SEND METHOD
    # ---------------------------------------------------------
    def send_sms(self, number, message, logs=None):
        """
        Universal dispatch method.
        Returns: (bool success, str api_response_id, str error_msg)
        """
        self.ensure_one()
        number = self._sanitize_number(number)
        
        # Dispatch to specific provider method
        method_name = f'_send_{self.provider_type}'
        if hasattr(self, method_name):
            return getattr(self, method_name)(number, message)
        else:
            return False, None, "Provider method implementation missing."

    # ---------------------------------------------------------
    # BOOMCAST IMPLEMENTATION (FIXED NUMBER FORMAT)
    # ---------------------------------------------------------
    def _send_boomcast(self, number, message):
        """
        API: http://api.boom-cast.com/...
        Constraint: Numbers MUST be 11 digits (e.g., 017...) 
        Boomcast fails if you send +88 or 88.
        """
        # --- NUMBER FORMATTING FIX ---
        clean_number = str(number).strip()
        
        # 1. Remove '+' (e.g. +88017...) -> 88017...
        if clean_number.startswith('+'):
            clean_number = clean_number[1:]
        
        # 2. Remove '88' if present (e.g. 88017...) -> 017...
        if clean_number.startswith('880'):
            clean_number = clean_number[2:]
            
        # 3. Handle '0088' edge case
        if clean_number.startswith('00880'):
            clean_number = clean_number[4:]

        # 4. Final check: It should start with '01' now
        # If it doesn't, we send it as is, but it might fail at provider level.

        # --- UNICODE CHECK ---
        is_unicode = self.check_unicode(message)
        msg_type = 'UNICODE' if is_unicode else 'TEXT'
        
        params = {
            'masking': self.sender_id or 'NOMASK',
            'userName': self.api_username,
            'password': self.api_password,
            'MsgType': msg_type,
            'receiver': clean_number,   # <--- Sending the cleaned 01... number
            'message': message
        }
        
        try:
            # Boomcast uses GET request
            response = requests.get(self.api_url, params=params, timeout=15)
            
            # Boomcast usually returns XML or plain text like:
            # "SUCCESS - <msgId>" or "FAILED - Reason"
            
            resp_text = response.text.strip()
            _logger.info(f"Boomcast Response: {resp_text}")
            
            if response.status_code == 200 and ('success' in resp_text.lower() or 'sent' in resp_text.lower()):
                # Try to extract ID if possible, otherwise use full text
                return True, resp_text[:50], None
                
            return False, None, f"Boomcast Error: {resp_text}"
            
        except Exception as e:
            return False, None, f"Boomcast Connection Error: {str(e)}"

    # ---------------------------------------------------------
    # MiMSMS IMPLEMENTATION (FIXED NUMBER FORMAT)
    # ---------------------------------------------------------
    def _send_mimsms(self, number, message):
        """
        Docs: https://apidoc.mimsms.com/
        Constraint: Numbers MUST start with 880
        """
        base_url = self.api_url.rstrip('/')
        url = f"{base_url}/api/SmsSending/SMS"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # --- NUMBER FORMATTING FIX ---
        clean_number = str(number).strip()
        
        # 1. Remove '+' if it exists (e.g. +88017...) -> 88017...
        if clean_number.startswith('+'):
            clean_number = clean_number[1:]
            
        # 2. If it starts with '01' (e.g. 017...), add '88' -> 88017...
        if clean_number.startswith('01'):
            clean_number = '88' + clean_number
            
        # 3. Validation: If it still doesn't start with 88, warn the user
        if not clean_number.startswith('88'):
             # Optional: Force add 88 if you are sure it's BD only
             # clean_number = '88' + clean_number 
             pass 

        payload = {
            'UserName': self.api_username,
            'Apikey': self.api_key,
            'MobileNumber': clean_number,
            'SenderName': self.sender_id,
            'TransactionType': 'T',
            'Message': message
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            try:
                res_json = response.json()
            except ValueError:
                return False, None, f"MiMSMS Invalid JSON: {response.text}"

            _logger.info(f"MiMSMS Response: {res_json}")

            # Check for Success (200) or Failure (206, etc.)
            status_code = str(res_json.get('statusCode') or res_json.get('response_code'))
            
            if status_code == '200':
                msg_id = res_json.get('MessageId') or res_json.get('trxnId') or 'sent_ok'
                return True, msg_id, None
            
            # Capture specific error messages like "Invalid Mobile Number"
            error_detail = res_json.get('responseResult') or res_json.get('status')
            return False, None, f"MiMSMS Error ({status_code}): {error_detail}"

        except Exception as e:
            return False, None, f"MiMSMS Connection Error: {str(e)}"

    # ---------------------------------------------------------
    # AWS SNS IMPLEMENTATION
    # ---------------------------------------------------------
    def _send_aws_sns(self, number, message):
        try:
            client = boto3.client(
                'sns',
                region_name=self.aws_region_name,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
            
            # Attributes for Sender ID and Type
            attributes = {
                'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': 'Transactional'}
            }
            if self.sender_id:
                attributes['AWS.SNS.SMS.SenderID'] = {'DataType': 'String', 'StringValue': self.sender_id}

            # AWS requires E.164 format (+880...)
            if not number.startswith('+'):
                number = f"+{number}"

            response = client.publish(
                PhoneNumber=number,
                Message=message,
                MessageAttributes=attributes
            )
            
            if 'MessageId' in response:
                return True, response['MessageId'], None
            return False, None, "AWS No Message ID returned"
            
        except Exception as e:
            return False, None, f"AWS Error: {str(e)}"