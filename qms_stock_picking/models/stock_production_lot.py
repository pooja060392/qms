from odoo import api, fields, models
from datetime import datetime


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    manufacture_date = fields.Date('Manufacture Date')
    import_date = fields.Date('Import Date')
    mrp = fields.Float('MRP')
    removal_date = fields.Date(
        string='Removal Date',
        help='This is the date on which the goods with this Serial Number should be removed from the stock.'
    )
    # product_qty = fields.Float('Quantity', compute='_product_qty', readonly=False, force_save="1")

    # @api.model
    # def create(self, values):
    #     res = super(ProductionLot, self).create(values)
    #     import_date = values.get('import_date')
    #     if 'import_date' in values and values['import_date']:
    #         query = """
    #                     update stock_production_lot set create_date = %s where id = %s
    #                 """
    #         self._cr.execute(query, (import_date, res.id))
    #     return res


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    removal_date = fields.Date(related='lot_id.removal_date', store=True, string='Expiry Date')

    # @api.model
    # def _get_removal_strategy_order(self, removal_strategy):
    #     if removal_strategy == 'fefo':
    #         return 'removal_date, in_date, id'
    #     return super(StockQuant, self)._get_removal_strategy_order(removal_strategy)
