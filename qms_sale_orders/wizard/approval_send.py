from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError

class ApprovalSend(models.TransientModel):
    _name = 'approval.send'

    approved_user_id = fields.Many2one('res.users','User')


    def submit_button(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        template = self.env.ref('qms_sale_order.send_quotation_approval_mail_template')
        # if sale_id.sale_type == 'sale':
        action_id = self.env.ref('sale.action_quotations').id
        # if sale_id.sale_type == 'sample_gift':
        #     action_id = self.env.ref('gts_qms_sale_order.action_sample_sale_order_waiting').id
        # if sale_id.sale_type == 'gift':
        #     action_id = self.env.ref('gts_qms_sale_order.action_gift').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            sale_id.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.approved_user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_approval_sale_url', _sale_url)
        template.send_mail(sale_id.id, force_send=True)
        template.body_html = template.body_html.replace(_sale_url , '_approval_sale_url')
        sale_id.write({
            'state': 'waiting_for_approval',
            'requested_id': self.approved_user_id.id,
            'is_quotation_sent': True,
            'is_quotation_rejected': False
        })
        if sale_id.sale_type == 'sample_gift':
            sale_id.write({'sample_state': 'waiting_for_approval'})
        return True


class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def check_quotation_approved(self):
        for users in self:
            if users.has_group('qms_sale_orders.group_quotation_approval'):
                users.is_approved = True
            else:
                users.is_approved = False

    is_approved= fields.Boolean('Is Quotation Approved', compute='check_quotation_approved', store=True)










