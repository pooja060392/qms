from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError

class SendApproval(models.TransientModel):
    _name = 'send.approval.po'

    approved_user_id = fields.Many2one('res.users','User')


    def submit_button(self):
        active_id = self.env.context.get('active_id')
        po_id = self.env['purchase.order'].browse(active_id)
        template = self.env.ref('qms_purchase.send_approval_po_mail')
        action_id = self.env.ref('qms_purchase.action_packaging_purchase_waiting').id
        params = "/web#id=%s&view_type=form&model=purchase.order&action=%s" % (
            po_id.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        po_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.approved_user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('po_url', po_url)
        template.send_mail(po_id.id, force_send=True)
        template.body_html = template.body_html.replace(po_url , 'po_url')
        po_id.write({'state': 'waiting_for_approval', 'requested_id': self.approved_user_id.id})
        return True

class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def check_packaging_po(self):
        for users in self:
            if users.has_group('qms_purchase.group_packaging_po'):
                users.is_approved_po = True
            else:
                users.is_approved_po = False

    is_approved_po = fields.Boolean('Is packaging po', compute='check_packaging_po', store=True)











