from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    po_id = fields.Many2one("purchase.order", string="PO #")


