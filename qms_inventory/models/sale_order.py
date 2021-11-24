from odoo import api, fields, models, registry, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        mo_id = self.env['mrp.production'].search([('sale_id', '=', self.id)], limit=1)
        for data in self:
            if data.is_kit:
                if not data.internal_transfer_mo:
                    rec = {
                        'picking_type_id': data.picking_type_mo.id,
                        'company_id': data.company_id.id,
                        'location_id': data.picking_type_mo.default_location_src_id.id,
                        'location_dest_id': data.picking_type_mo.default_location_dest_id.id,
                        'name': data.name,
                        'internal_transfer_mo': data.internal_transfer_mo.id,
                        'origin': data.name,
                        'internal_transfer_mo_done': True,
                        'production_id': mo_id.id
                    }
                    picking_create_id_ = self.env['stock.picking'].create(rec)
                    for line in data.order_line:
                        dict_ = {
                            'picking_type_id': data.picking_type_mo.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'product_uom_qty':  line.qty_per_kit * data.kit_quantity,
                            'picking_id': picking_create_id_.id,
                            'name': line.name,
                            'location_id': data.picking_type_mo.default_location_src_id.id,
                            'location_dest_id': data.picking_type_mo.default_location_dest_id.id,
                            'origin': data.name
                        }
                        self.env['stock.move'].create(dict_)
                    if picking_create_id_:
                        data.write({
                            'internal_transfer_mo': picking_create_id_.id,
                        })
        return res



