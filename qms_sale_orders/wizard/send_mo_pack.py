from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError

class Daysfill(models.TransientModel):
    _name = 'days.fill.mo'

    mo_user_id = fields.Many2one('res.users','User')


    def submit_button(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        template = self.env.ref('qms_sale_orders.mo_packing_mail_template')
        action_id = self.env.ref('qms_sale_orders.action_sale_order_fill_days').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            sale_id.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.mo_user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_sale_url', _sale_url)
        template.send_mail(sale_id.id, force_send=True)
        sale_id.write({'send_mail_to_mo': True, 'packaging_req_id': self.mo_user_id.id})
        template.body_html = template.body_html.replace(_sale_url, '_sale_url')
        return True

class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def check_mo_days(self):
        for users in self:
            if users.has_group('mrp.group_mrp_manager'):
                users.is_mo_days = True
            else:
                users.is_mo_days = False

    is_mo_days = fields.Boolean('Is Fill MO Days', compute='check_mo_days', store=True)


