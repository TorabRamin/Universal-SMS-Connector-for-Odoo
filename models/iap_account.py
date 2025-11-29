from odoo import models, api

class IapAccount(models.Model):
    _inherit = 'iap.account'

    @api.model
    def get_credits(self, service_name):
        """
        OVERRIDE: Mock credit balance for SMS to avoid UI warnings.
        """
        # Check if we are using a custom SMS provider
        if service_name == 'sms':
            custom_provider = self.env['sms.provider'].search_count([('state', '=', 'enabled')])
            if custom_provider > 0:
                # Return a fake high balance so Odoo thinks we are rich
                return 999999
        
        return super(IapAccount, self).get_credits(service_name)