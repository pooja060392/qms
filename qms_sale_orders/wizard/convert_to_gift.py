from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class ConvertGift(models.TransientModel):
    _name = 'convert.gift'

    product_line = fields.One2many('product.line', 'line_id')
    user_id = fields.Many2one('res.users', 'Request User for Approval')
    sale_id = fields.Many2one('sale.order')

    # @api.model
    # def default_get(self, fields):
    #     res = super(ConvertGift, self).default_get(fields)
    #     product_lst = []
    #     active_ids = self.env.context.get('active_ids')
    #     sale_id = self.env['sale.order'].browse(active_ids)
    #     for line in sale_id.order_line:
    #         if line.order_id.gift_amt < line.price_unit:
    #             product_lst.append((0,0, {
    #                 'product_id': line.product_id.id,
    #                 'sale_line_id': line.id
    #             }))
    #         # else:
    #         #     raise UserError(_('Can not convert to Gift as Gift Amount is Greater than the Unit Price'))
    #     res['product_line'] = product_lst
    #     res['sale_id'] = sale_id.id
    #     return res


    def convert_gift(self):
        if self.product_line:
            for line in self.product_line:
                if line.qty <= 0:
                    raise UserError(_('Please fill product quantity!'))
                if line.qty > line.sale_line_id.product_uom_qty:
                    raise UserError(_('Conversion quantity can not be greater than delivered quantity!'))
                line.sale_line_id.write({'type': 'pending',
                                         'gift_qty': line.qty})
            # self.sale_id.convert_to_gift = True
            self.sale_id.write({'convert_to_gift': True, 'sample_state': 'waiting_for_gift_approval'})
            template = self.env.ref('qms_sale_orders.request_for_convert_into_gift')
            action_id = self.env.ref('qms_sale_orders.action_sample_sale_order').id
            params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
                self.sale_id.id, action_id)
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            # NEHA: theis group not used to send email, need to remove
            sale_approve_group = self.env.ref('qms_sale_orders.group_sample_approved')
            email_to = ' '
            for user in sale_approve_group.sudo().users:
                email_to = email_to + user.partner_id.email + ','
            _sale_url = str(current_url) + str(params)
            template.email_from = self.env.user.login
            template.email_to = self.user_id.partner_id.email or ''
            template.body_html = template.body_html.replace('_sale_url', _sale_url)
            template.send_mail(self.sale_id.id, force_send=True)
            template.body_html = template.body_html.replace(_sale_url, '_sale_url')
            query = ("""update sale_order set gift_rejected = False where id = %s""" % self.sale_id.id)
            self._cr.execute(query)
            self.action_add_amount()
        return True


    def action_add_amount(self):
        if self.product_line:
            for line in self.product_line:
                amt = line.qty * line.sale_line_id.price_unit
            if self.sale_id.user_id:
                self.sudo().user_id.used_sale_amt = self.user_id.used_sale_amt - amt


class ProductLine(models.TransientModel):
    _name = 'product.line'

    line_id = fields.Many2one('convert.gift')
    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Quantity')
    sale_line_id = fields.Many2one('sale.order.line')



