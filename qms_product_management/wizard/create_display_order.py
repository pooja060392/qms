from odoo import api, fields, models

class CreateDisplayOrder(models.TransientModel):
    _name = 'create.display.order'


    def create_display(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        product_lst = []
        sale_order = self.env['sale.order']
        for record in self.env['product.template'].browse(active_ids):
            product_lst.append((0, 0, {
                        'product_id': record.id,
                        'product_uom_qty': 1,
                        'price_unit': record.list_price,
                        'name': record.name,
                        'product_uom': record.uom_id.id,
                        'return_status': 'new'
                    }))
            # sale_order.create({'order_line': product_lst})
        res = {
            'name': "Display order",
            'type': 'ir.actions.act_window',
            # 'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('qms_sale_order.display_sale_order_form_view').id,
            'res_model': 'sale.order',
            'context': {
                        'default_sale_type': 'display',
                        'default_order_line': product_lst}
        }
        return res
