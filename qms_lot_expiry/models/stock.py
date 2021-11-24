from odoo import api, fields, models, _
from lxml import etree, html
from odoo.exceptions import UserError
from datetime import datetime


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    active = fields.Boolean('Active', default=True)

    @api.model
    def get_expired_lots(self):
        lot_ids = self.env['stock.production.lot'].search([])
        for data in lot_ids:
            date_today = fields.Datetime.now()
            date_ = datetime.strptime(date_today, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            if data.removal_date and data.removal_date <= date_:
                data.active = False
