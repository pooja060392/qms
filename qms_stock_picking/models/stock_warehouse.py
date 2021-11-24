from odoo import api, fields, models

class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    user_id = fields.Many2one('res.users', 'Responsible')
    sample_picking_type = fields.Many2one(
        'stock.picking.type', string='Sample Picking Type',
        copy=False, index=True
    )
    stock_manu_picking_type = fields.Many2one(
        'stock.picking.type', string='Stock to Manufacturing Type',
        copy=False, index=True
    )
