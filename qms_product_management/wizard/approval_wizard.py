from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError


class SendApproval(models.TransientModel):
    _name = 'send.approval'

    user_id = fields.Many2one('res.users','User')
    product_id = fields.Many2one('product.template')


    def submit_button(self):
        active_id = self.env.context.get('active_id')
        product = self.env['product.template'].browse(active_id)
        template = self.env.ref('qms_product_management.product_approve_mail_template')
        action_id = self.env.ref('qms_product_management.product_template_waiting_approval_action').id
        params = "/web#id=%s&view_type=form&model=product.template&action=%s" % (
            product.id, action_id
        )
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        product_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('product_url', product_url)
        template.send_mail(product.id, force_send=True)
        template.body_html = template.body_html.replace(product_url, 'product_url')
        product.write({'state': 'waiting_approval',
                       'requested_id': self.user_id.id})
        return True

    @api.model
    def default_get(self, default_fields):
        data = super(SendApproval, self).default_get(default_fields)
        res_id = self.env.context.get('active_id', [])
        product = self.env['product.template'].browse(res_id)
        if product:
            data['product_id'] = product.id
        return data


class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def check_product_approval(self):
        for users in self:
            if users.has_group('qms_product_management.group_product_approval'):
                users.is_product_approved = True
            else:
                users.is_product_approved = False

    is_product_approved = fields.Boolean('Is Product Approval', compute='check_product_approval',
                                         store=True)
