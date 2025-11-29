from odoo import models, api, _, fields

class SmsSms(models.Model):
    _inherit = 'sms.sms'

    def _send(self, unlink_failed=False, unlink_sent=True, raise_exception=False):
        """ 
        OVERRIDE: Intercepts native Odoo SMS sending.
        If a custom provider is enabled, use it. Otherwise, fall back to IAP.
        """
        # 1. Check if we have an enabled custom provider
        custom_provider = self.env['sms.provider'].search([
            ('state', '=', 'enabled')
        ], order='priority asc', limit=1)

        if custom_provider:
            # --- CUSTOM ROUTE ---
            for record in self:
                # Use your module's send_sms method
                success, api_id, error = custom_provider.send_sms(
                    record.number, 
                    record.body
                )

                # Update the Odoo native SMS record status
                if success:
                    record.write({
                        'state': 'sent',
                        'failure_type': False,
                        'to_delete': unlink_sent
                    })
                    
                    # --- FIXED: Get document info from the linked Mail Message ---
                    doc_model = False
                    doc_id = 0
                    if record.mail_message_id:
                        doc_model = record.mail_message_id.model
                        doc_id = record.mail_message_id.res_id

                    # Create a log in your custom sms.log
                    self.env['sms.log'].create({
                        'mobile': record.number,
                        'message': record.body,
                        'provider_id': custom_provider.id,
                        'state': 'sent',
                        'api_response_id': api_id,
                        'res_model': doc_model, # Fixed
                        'res_id': doc_id,       # Fixed
                    })
                else:
                    record.write({
                        'state': 'error',
                        'failure_type': 'sms_server',
                    })
                    # Only raise if Odoo expects it (usually strictly required for batching)
                    if raise_exception:
                        # Log error internally instead of crashing the UI
                        print(f"SMS Failed via {custom_provider.name}: {error}")

            # Remove successfully sent messages if unlink_sent is True
            if unlink_sent:
                self.filtered(lambda s: s.state == 'sent').unlink()
                
            return True

        else:
            # --- STANDARD ODOO IAP ROUTE ---
            return super(SmsSms, self)._send(unlink_failed=unlink_failed, unlink_sent=unlink_sent, raise_exception=raise_exception)