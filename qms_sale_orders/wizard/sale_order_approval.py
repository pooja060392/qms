from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError


class SOAppprovalWiz(models.TransientModel):
    _name = 'so.approval.wiz'

    user_id = fields.Many2one('res.users', 'User')


    def send_for_so_approval(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        template = self.env.ref('qms_sale_orders.send_quotation_approval_mail_template')
        # if sale_id.sale_type == 'sale':
        action_id = self.env.ref('sale.action_orders').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            sale_id.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_approval_sale_url', _sale_url)
        template.send_mail(sale_id.id, force_send=True)
        template.body_html = template.body_html.replace(_sale_url , '_approval_sale_url')
        sale_id.write({
            'state': 'waiting_for_so_approval',
            'so_approved_by': self.user_id.id,
            'is_so_sent': True,
            'is_so_rejected': False
        })
        # if sale_id.sale_type == 'sample_gift':
        #     sale_id.write({'sample_state': 'waiting_for_approval'})
        return True


class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def check_so_approved(self):
        for users in self:
            if users.has_group('qms_sale_orders.group_sale_approval'):
                users.sales_approval = True
            else:
                users.sales_approval = False

    sales_approval = fields.Boolean('Sales Approval', compute='check_so_approved', store=True)
