from odoo import models, fields, api
import math

class SMSComposeWizard(models.TransientModel):
    _name = 'sms.compose.wizard'
    _description = 'Send SMS Wizard'

    recipient_ids = fields.Char(string="Recipients (Comma separated)")
    message = fields.Text(required=True)
    provider_id = fields.Many2one('sms.provider', string="Force Provider (Optional)")
    
    # Live Calculation Fields
    char_count = fields.Integer(compute='_compute_segments')
    segment_count = fields.Integer(compute='_compute_segments')
    is_unicode = fields.Boolean(compute='_compute_segments')

    @api.depends('message')
    def _compute_segments(self):
        for rec in self:
            msg = rec.message or ""
            rec.char_count = len(msg)
            
            # Unicode Detection
            try:
                msg.encode('ascii')
                rec.is_unicode = False
                # GSM 7-bit standard: 160 chars per segment, if concat 153
                limit = 160 if len(msg) <= 160 else 153
            except UnicodeEncodeError:
                rec.is_unicode = True
                # Unicode standard: 70 chars per segment, if concat 67
                limit = 70 if len(msg) <= 70 else 67
                
            rec.segment_count = math.ceil(len(msg) / limit) if len(msg) > 0 else 0

    def action_send_sms(self):
        numbers = [x.strip() for x in self.recipient_ids.split(',')]
        
        # Batch creation of logs
        logs = []
        for num in numbers:
            logs.append({
                'mobile': num,
                'message': self.message,
                'provider_id': self.provider_id.id if self.provider_id else False,
                'state': 'draft' # Set to draft so the Cron picks it up (async)
            })
        
        self.env['sms.log'].create(logs)
        
        # Optional: Trigger immediate processing
        self.env['sms.log'].search([('state','=','draft')]).action_send_queued()