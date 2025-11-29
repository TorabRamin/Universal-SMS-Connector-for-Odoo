from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SMSWebhook(http.Controller):

    @http.route('/sms/webhook/delivery', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def receive_delivery_status(self, **kwargs):
        """
        Generic endpoint to map provider callbacks.
        Expected URL: /sms/webhook/delivery?msgId=XYZ&status=DELIVRD
        """
        msg_id = kwargs.get('msgId') or kwargs.get('message_id')
        status = kwargs.get('status') or kwargs.get('dlr_status')
        
        if msg_id and status:
            log = request.env['sms.log'].sudo().search([('api_response_id', '=', msg_id)], limit=1)
            if log:
                new_state = 'sent'
                status_lower = status.lower()
                
                if 'deliv' in status_lower:
                    new_state = 'delivered'
                elif 'fail' in status_lower or 'undeliv' in status_lower:
                    new_state = 'failed'
                
                log.write({'state': new_state, 'api_response_dump': str(kwargs)})
                
        return "OK"