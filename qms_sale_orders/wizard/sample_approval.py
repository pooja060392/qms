from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError


class SampleAppprovalWizard(models.TransientModel):
    _name = 'sample.approval.wizard'

    user_id = fields.Many2one('res.users', 'User')
    sale_id = fields.Many2one('sale.order', 'Sale')

    @api.model
    def default_get(self, default_fields):
        data = super(SampleAppprovalWizard, self).default_get(default_fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        sale_ = self.env['product.template'].browse(active_ids)
        data['sale_id'] = sale_.id

        return data


    def send_for_sample_approval(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        template = self.env.ref('qms_sale_order.email_template_send_sample_for_approval')
        action_id = self.env.ref('qms_sale_menus.action_sample_request').id
        # params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
        #     sale_id.id, action_id)
        params = "web#id=%s&view_type=form&model=sale.order&action=%s" % (
            sale_id.id, action_id
        )
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _sale_url = str(params)
        if template:
            values = template.generate_email(self.id)
            values['email_to'] = self.user_id.partner_id.email
            values['email_from'] = sale_id.user_id.partner_id.email
            values['email_cc'] = self.env.user.email or self.env.user.partner_id.email
            values['body_html'] = values['body_html'].replace('_sale_url', _sale_url)
            mail = self.env['mail.mail'].create(values)
            try:
                mail.send()
            except Exception:
                pass
        sale_id.write({
            'sample_state': 'waiting_for_sample_approval',
            'sample_approved_by': self.user_id.id,
            'is_sample_sent': True,
            'is_sample_rejected': False
        })
        return True


class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def check_so_approved(self):
        for users in self:
            if users.has_group('qms_sale_order.group_sale_approval'):
                users.sales_approval = True
            else:
                users.sales_approval = False

    sales_approval = fields.Boolean('Sales Approval', compute='check_so_approved', store=True)
