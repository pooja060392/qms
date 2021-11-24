from odoo import models,fields,api
import datetime


class GiftRejectionReason(models.TransientModel):
    _name = 'gift.rejection.reason'

    reason_of_rejection = fields.Text('Reason')
    sale_id = fields.Many2one('sale.order')


    def reject_gift(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        # sale_id.write({'convert_to_gift': False})
        for line in sale_id.order_line:
            line.write({'type': 'sample','gift_qty': 0})
        action_id = self.env.ref('qms_sale_orders.action_sample_sale_order').id
        template = self.env.ref('qms_sale_orders.reject_convert_into_gift')
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            sale_id.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        convert_line = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = sale_id.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('convert_line', convert_line)
        template.send_mail(sale_id.id, force_send=True)
        template.body_html = template.body_html.replace(convert_line, 'convert_line')
        sale_id.reject_reason_line.create({
            'date': datetime.datetime.now(),
            'user_id': self.env.user.id,
            'reason': self.reason_of_rejection,
            'reason_id': sale_id.id,
            # 'is_quotation_sent': False
        })
        query = ("""update sale_order set gift_rejected = True where id = %s""" % sale_id.id)
        self._cr.execute(query)
        sale_id.write({'sample_state': 'rejected'})