from odoo import api, fields, models
import math


class ProductProduceLine(models.TransientModel):
    _name = "mrp.product.produce"

    @api.onchange('product_qty')
    def onchange_produce_qty(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        mrp = self.env['mrp.production'].browse(active_ids)
        rem = 0.0
        pro_list = []
        for move in mrp.bom_id.bom_line_ids:
            pro_list.append(move.product_id.id)
        pro_comsume_qty = ''

        for move in pro_list:
            count = 0
            for line in self.produce_line_ids:
                pro_comsume_qty = qty = 0
                if move == line.product_id.id:
                    pro_comsume = mrp.move_raw_ids.filtered(lambda x: x.product_id.id == move)
                    for pro in pro_comsume:
                        pro_comsume_qty += pro.product_uom_qty
                    qty = (pro_comsume_qty / mrp.product_qty) * self.product_qty
                    # if count > 0:
                    #     line.qty_done = 0.0
                    #     continue
                    # if line.qty_to_consume:
                    line.qty_done = math.ceil(qty)
                        # count = count + 1
                    # if line.qty_to_consume < qty:
                    #     rem = qty - line.qty_to_consume
                    #     line.qty_done = line.qty_to_consume
                    #     qty = rem


