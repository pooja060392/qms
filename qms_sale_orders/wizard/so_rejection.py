from odoo import models,fields,api
import datetime


class SORejectionReason(models.TransientModel):
    _name = 'so.rejection.reason'

    reason_of_rejection = fields.Text('Reason')


    def reject(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        for rec in sale_id:
            rec.write({'line_status': 'rejected_so','state': 'rejected_so'})
        template = self.env.ref('qms_sale_order.reject_so_mail_template')
        action_id = self.env.ref('sale.action_quotations').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            sale_id.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = sale_id.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_sale_url', sale_url)
        template.send_mail(sale_id.id, force_send=True)
        template.body_html = template.body_html.replace(sale_url, '_sale_url')
        sale_id.write({'state': 'rejected_so'})
        if sale_id.sale_type == 'sample_gift':
            sale_id.write({'sample_state': 'rejected'})
        sale_id.so_rejection_reason_line.create({
            'date': datetime.datetime.now(),
            'user_id': self.env.user.id,
            'reason': self.reason_of_rejection,
            'sale_order_id': sale_id.id,
            # 'is_quotation_sent': False
        })
        sale_id.is_so_rejected = True
        sale_id.is_so_sent = False
        return True
