from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    quality_location = fields.Boolean('Is a Quality Location?', copy=False, index=True)
    manufacturing_location = fields.Boolean('Is a Manufacturing Location?', copy=False, index=True)
    sample_location = fields.Boolean('Is a Sample Location?', copy=False, index=True)
    gift_location = fields.Boolean('Is a Gift Location?', copy=False, index=True)

    # @api.onchange('sample_location')
    # def onchange_sample(self):
    #     location_search = self.env['stock.location'].search([])
    #     if any(data.sample_location is True for data in location_search):
    #         raise UserError(_('There is already a Sample Location Exists!'))
