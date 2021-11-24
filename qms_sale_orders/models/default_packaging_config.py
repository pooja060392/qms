from odoo import api, fields, models,_
from odoo.exceptions import UserError

class PackageConfig(models.Model):
    _name = 'package.config'

    name = fields.Char('Default Pack Name',default='Default Customization')
    config_pack_line = fields.One2many('packing.line','config_id')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('package.design'))

    @api.model
    def create(self, values):
        config_pack = self.search([])
        if len(config_pack) >= 1:
            raise UserError(_('You can create only one record !!!.'))
        return super(PackageConfig, self).create(values)


class PackLine(models.Model):
    _inherit = 'packing.line'

    config_id = fields.Many2one('package.config')
#     pack_order_id = fields.Many2one('sale.order')
#     product_id = fields.Many2one('product.product','Customization Name')
#     type = fields.Char('Type')
#     size = fields.Char('Size')
#     price = fields.Float('Cost To Us/Piece')



