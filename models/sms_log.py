from odoo import models, fields, api, _

class SMSLog(models.Model):
    _name = 'sms.log'
    _description = 'SMS Log & Queue'
    _order = 'create_date desc'
    _rec_name = 'mobile'

    provider_id = fields.Many2one('sms.provider', string="Provider")
    mobile = fields.Char(required=True)
    message = fields.Text(required=True)
    state = fields.Selection([
        ('draft', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered')
    ], default='draft')
    
    api_response_id = fields.Char(string="Trxn ID")
    api_response_dump = fields.Text(string="Raw Response")
    error_message = fields.Text()
    retry_count = fields.Integer(default=0)
    
    # Linked Document
    res_model = fields.Char()
    res_id = fields.Integer()

    def action_send_queued(self):
        """Triggered by Cron or Manually"""
        # Load Balancing: Get highest priority enabled provider
        default_provider = self.env['sms.provider'].search([
            ('state', '=', 'enabled')
        ], order='priority asc', limit=1)

        for log in self:
            provider = log.provider_id or default_provider
            
            # Smart Routing Logic (Example)
            if log.mobile.startswith('880') or log.mobile.startswith('+880'):
                # Prefer BD providers
                bd_provider = self.env['sms.provider'].search([
                    ('provider_type', 'in', ['boomcast', 'mimsms']),
                    ('state', '=', 'enabled')
                ], order='priority asc', limit=1)
                if bd_provider:
                    provider = bd_provider
            
            if not provider:
                log.write({'state': 'failed', 'error_message': 'No active provider found'})
                continue

            success, api_id, err = provider.send_sms(log.mobile, log.message)
            
            if success:
                log.write({
                    'state': 'sent',
                    'provider_id': provider.id,
                    'api_response_id': api_id,
                    'error_message': False
                })
            else:
                # Retry Logic / Fallback
                if log.retry_count < 3:
                    log.write({
                        'retry_count': log.retry_count + 1,
                        'error_message': f"Attempt {log.retry_count + 1} Failed: {err}"
                    })
                else:
                    log.write({'state': 'failed', 'error_message': f"Final Failure: {err}"})