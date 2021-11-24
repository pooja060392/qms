from odoo import api, fields, models, tools, _
from datetime import datetime
from datetime import timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customization_email_sent = fields.Boolean('Email Sent', copy=False, index=True, default=False)
    purchase_team_intimation = fields.Datetime(
        string="Date of Intimation",
        index=True, copy=False,
        default=fields.Datetime.now)


    def write(self, values):
        rec = super(SaleOrder, self).write(values)
        for data in self:
            if data.customization_email_sent is False and data.customisation is True:
                action_id = self.env.ref('qms_sale_order.action_sale_order_fill_days').id
                params = "web#id=%s&view_type=form&model=sale.order&action=%s" % (
                    data.id, action_id
                )
                sale_url = str(params)
                template = self.env.ref('qms_sale_order.email_template_customization_to_packaging')
                get_group = self.env.ref('qms_sale_order.group_purchase_team_packaging')
                Users = get_group.users.filtered(lambda x: x.email)
                for user_ in Users:
                    if template:
                        data.customization_email_sent = True
                        values = template.generate_email(data.id)
                        values['email_to'] = user_.partner_id.email
                        values['email_from'] = data.user_id.partner_id.email
                        values['body_html'] = values['body_html'].replace('_sale_url', sale_url)
                        mail = self.env['mail.mail'].create(values)
                        try:
                            mail.send()
                        except Exception:
                            pass
        return rec

    @api.model
    def create(self, values):
        rec = super(SaleOrder, self).create(values)
        for data in rec:
            if rec.customization_email_sent is False and rec.customisation is True:
                action_id = self.env.ref('qms_sale_order.action_sale_order_fill_days').id
                params = "web#id=%s&view_type=form&model=sale.order&action=%s" % (
                    data.id, action_id
                )
                sale_url = str(params)
                template = self.env.ref('qms_sale_order.email_template_customization_to_packaging')
                get_group = self.env.ref('qms_sale_order.group_purchase_team_packaging')
                Users = get_group.users.filtered(lambda x: x.email)
                for user_ in Users:
                    if template:
                        rec.customization_email_sent = True
                        values = template.generate_email(data.id)
                        values['email_to'] = user_.partner_id.email
                        values['email_from'] = data.user_id.partner_id.email
                        values['body_html'] = values['body_html'].replace('_sale_url', sale_url)
                        mail = self.env['mail.mail'].create(values)
                        try:
                            mail.send()
                        except Exception:
                            pass
        return rec


    # def send_ready(self):
    #     x = datetime.strptime(self.purchase_team_intimation, '%Y-%m-%d %H:%M:%S') + timedelta(hours=24)
    #     y = fields.Datetime.now()
    #     for rec in self.packing_line:
    #         if x == y and not rec.size or rec.price:
    #             template_id = self.env.ref('gts_customise_email.email_template_top_customise')
    #             users_list = self.env.ref('gts_customise_email.group_top_management')
    #             Users = users_list.users.filtered(lambda x: x.email)
    #             if template_id:
    #                 template_id.email_from = self.env.user.email
    #                 template_id.email_to = Users
    #                 template_id.body_html = template_id.body_html
    #                 template_id.send_mail(self.id, force_send=True)


