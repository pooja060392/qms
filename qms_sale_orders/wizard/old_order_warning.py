from odoo import models,fields,api
import datetime


class OldOrderWarning(models.TransientModel):
    _name = 'old.order.warning'

    sale_order_id = fields.Many2one('sale.order', 'Sale')
    name = fields.Text('Name')

    # NEHA: Mail trigger when Quotation set as Mask as old

    def action_send_email(self):
        for data in self:
            active_id = self.env.context.get('active_id')
            sale_id = self.env['sale.order'].browse(active_id)
            action_id = self.env.ref('sale.action_quotations').id
            params = "web#id=%s&view_type=form&model=sale.order&action=%s" % (
                sale_id.id, action_id
            )
            sale_url = str(params)
            template = self.env.ref('qms_sale_orders.sale_mark_old_template')
            get_group = self.env.ref('qms_sale_orders.group_purchase_team_packaging')
            Users = get_group.users.filtered(lambda x: x.email)
            for user_ in Users:
                if template:
                    values = template.generate_email(sale_id.id)
                    values['email_to'] = user_.partner_id.email
                    values['email_from'] = sale_id.user_id.partner_id.email
                    values['body_html'] = values['body_html'].replace('_sale_url', sale_url)
                    mail = self.env['mail.mail'].create(values)
                    try:
                        mail.send()
                    except Exception:
                            pass


    def make_changes(self):
        active_id = self.env.context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        sale_id.customisation = False
        sale_id.artwork_need = False
        sale_id.is_old_order = True
        # NEHA: Call Function to mail triger
        self.action_send_email()
        for line in sale_id.order_line:
            if line.product_id.name == 'Customization':
                line.unlink()
        return True
