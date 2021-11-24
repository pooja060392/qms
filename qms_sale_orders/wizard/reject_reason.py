from odoo import models,fields,api
import datetime

class rejectReason(models.TransientModel):
    _name = 'reject.reason'

    reason_of_reject = fields.Text('Reason')


    def reject(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        # if sale_id.convert_to_gift == True:
        #     sale_id.write({'convert_to_gift': False})
        #     for line in sale_id.order_line:
        #         line.write({'type': 'sample','gift_qty': 0})
        #     action_id = self.env.ref('gts_qms_sale_order.action_sample_sale_order').id
        #     template = self.env.ref('gts_qms_sale_order.reject_convert_into_gift')
        #     params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
        #         sale_id.id, action_id)
        #     current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        #     convert_line = str(current_url) + str(params)
        #     template.email_from = self.env.user.login
        #     template.email_to = sale_id.user_id.partner_id.email or ''
        #     template.body_html = template.body_html.replace('convert_line', convert_line)
        #     template.send_mail(sale_id.id, force_send=True)
        #     template.body_html = template.body_html.replace(convert_line, 'convert_line')
        # else:
        for rec in sale_id:
            rec.write({'line_status': 'rejected','state': 'rejected'})
        template = self.env.ref('qms_sale_order.reject_so_mail_template')
        # if sale_id.sale_type == 'sale':
        #     action_id = self.env.ref('gts_qms_sale_order.action_sale_order_cancel').id
        # if sale_id.sale_type == 'sample_gift':
        #     action_id = self.env.ref('gts_qms_sale_order.action_sample_cancel').id
        # if sale_id.sale_type == 'gift':
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
        sale_id.write({'state': 'rejected'})
        if sale_id.sale_type == 'sample_gift':
            sale_id.write({'sample_state': 'rejected'})
        sale_id.reject_reason_line.create({
            'date': datetime.datetime.now(),
            'user_id': self.env.user.id,
            'reason': self.reason_of_reject,
            'reason_id': sale_id.id,
            # 'is_quotation_sent': False
        })
        sale_id.is_quotation_rejected = True
        sale_id.is_quotation_sent = False
        return True
