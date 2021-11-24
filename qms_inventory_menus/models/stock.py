from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    warehouse_type = fields.Selection([
        ('1', 'Bhiwandi'), ('3', 'HO')
    ], string='Warehouse Type', copy=False, index=True, related='picking_type_id.warehouse_type', store=True)
    quality_location = fields.Boolean('Is a Quality Location?', copy=False, index=True,
                                      compute='get_quality', store=True)

    @api.depends('picking_type_id')
    def get_quality(self):
        for data in self:
            if data.picking_type_id:
                data.quality_location = data.picking_type_id.quality_location


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    warehouse_type = fields.Selection([
        ('1', 'Bhiwandi'),('3', 'HO')
    ], string='Warehouse Type', copy=False, index=True)
    quality_location = fields.Boolean('Is a Quality Location?', copy=False, index=True,
                                      compute='get_quality', store=True)

    @api.depends('default_location_src_id')
    def get_quality(self):
        for data in self:
            if data.default_location_src_id:
                data.quality_location = data.default_location_src_id.quality_location
