from odoo import api, fields, models


class StockBackorder(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    remarks = fields.Text('Remarks')
    related_code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'),
                                     ('internal', 'Internal'), ('mrp_operation', 'Manufacturing Operation')], 'Type of Operation')


    def _process(self, cancel_backorder=False):
        self.pick_ids.action_done()
        if self.related_code in ('internal','incoming'):
            purchase = self.env['purchase.order'].search([('name', '=', self.pick_ids.origin)],limit=1)
            self.pick_ids.write({'remarks': self.remarks})
            template = self.env.ref('qms_stock_picking.mail_template_backorder')
            action_id = self.env.ref('purchase.purchase_form_action').id
            params = "/web#id=%s&view_type=form&model=purchase.order&action=%s" % (
                purchase.id, action_id)
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            backorder_url = str(current_url) + str(params)
            template.email_from = self.env.user.login
            template.email_to = purchase.create_uid.partner_id.email or ''
            template.body_html = template.body_html.replace('backorder_url', backorder_url)
            template.send_mail(self.id, force_send=True)
            template.body_html = template.body_html.replace(backorder_url, 'backorder_url')
        if cancel_backorder:
            for pick_id in self.pick_ids:
                backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', pick_id.id)])
                backorder_pick.action_cancel()
                pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))

