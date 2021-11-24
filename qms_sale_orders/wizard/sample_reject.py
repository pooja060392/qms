from odoo import models,fields,api
import datetime


class SampleRejectionReason(models.TransientModel):
    _name = 'sample.rejection.reason'

    reason_of_rejection = fields.Text('Reason')
    sale_id = fields.Many2one('sale.order', 'Sale')

    @api.model
    def default_get(self, default_fields):
        data = super(SampleRejectionReason, self).default_get(default_fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        sale_ = self.env['product.template'].browse(active_ids)
        data['sale_id'] = sale_.id

        return data


    def reject(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        for rec in sale_id:
            rec.write({'line_status': 'rejected_so','state': 'rejected_so'})
        template = self.env.ref('qms_sale_order.email_template_sample_rejection')
        action_id = self.env.ref('qms_sale_menus.action_sample_request').id
        params = "web#id=%s&view_type=form&model=sale.order&action=%s" % (
            sale_id.id, action_id
        )
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _sale_url = str(params)
        if template:
            values = template.generate_email(self.id)
            values['email_to'] = self.sale_id.user_id.partner_id.email
            values['email_from'] = self.env.user.partner_id.email
            values['body_html'] = values['body_html'].replace('_sale_url', _sale_url)
            mail = self.env['mail.mail'].create(values)
            try:
                mail.send()
            except Exception:
                pass
        sale_id.write({'state': 'rejected_so'})
        if sale_id.sale_type == 'sample_gift':
            sale_id.write({'sample_state': 'sample_rejected'})
        sale_id.sample_rejection_reason_line.create({
            'date': datetime.datetime.now(),
            'user_id': self.env.user.id,
            'reason': self.reason_of_rejection,
            'sale_order_id': sale_id.id,
            # 'is_quotation_sent': False
        })
        sale_id.is_sample_rejected = True
        sale_id.is_sample_sent = False
        return True
