from odoo import api, fields, models,_
from odoo.exceptions import UserError, AccessError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta

class DesignSend(models.TransientModel):
    _name = 'design.send.wiz'

    design_user_id = fields.Many2one('res.users','User')


    def submit_button(self):
        active_id = self.env.context.get('active_id')
        artwork_date = ''
        sale_id = self.env['sale.order'].browse(active_id)
        pack_lst = []
        design = self.env['package.design']
        for line in sale_id.packing_line:
            pack_lst.append((0, 0, {
                'product_id': line.product_id.id,
                'description': line.description,
                'quantity': line.quantity,
                'type': line.type,
                'size': line.size,
                'price': line.price,
                'total': line.total
            }))
        # if not sale_id.po_date:
        #     raise UserError(_('Please fill PO date!!!'))
        # if not sale_id.delivery_date:
        #     raise UserError(_('Please fill Delivery Date!!!'))
        po_date = datetime.strptime(sale_id.po_date, "%Y-%m-%d")
        delivery_date = datetime.strptime(sale_id.delivery_date, "%Y-%m-%d")
        different_date = delivery_date - po_date
        if different_date.days > 17:
            artwork_date = delivery_date - timedelta(days=17)
        else:
            artwork_date = fields.Datetime.now()
        design_id = design.create({'sale_id': sale_id.id,
                                   'artwork_deadline': artwork_date,
                                   'design_packing_line': pack_lst})
        sale_id.write({'pack_design_id': design_id.id,'sent_for_design': True, 'design_requested_id': self.design_user_id.id})
        template = self.env.ref('qms_sale_orders.send_for_design_mail_template')
        action_id = self.env.ref('qms_sale_orders.action_design').id
        params = "/web#id=%s&view_type=form&model=package.design&action=%s" % (
            sale_id.pack_design_id.id, action_id
        )
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        design_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.design_user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('design_url', design_url)
        template.send_mail(sale_id.id, force_send=True)
        template.body_html = template.body_html.replace(design_url, 'design_url')
        return True

class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def check_contract_default(self):
        for users in self:
            if users.has_group('qms_sale_orders.group_design_packing'):
                users.is_design_pack = True
            else:
                users.is_design_pack = False

    is_design_pack = fields.Boolean('Is design Approval', compute='check_contract_default', store=True)










