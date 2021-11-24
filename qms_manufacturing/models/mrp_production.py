from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_id = fields.Many2one('sale.order', 'Sale Reference')
    production_pack_line = fields.One2many('prod.pack.line','prod_pack_id')
    delivery_date = fields.Date('Delivery Date')

    # @api.multi
    # def action_cancel(self):
    #     res = super(MrpProduction, self).action_cancel()
    #     for picking in self:
    #         for line in picking.move_lines:
    #             if line.sale_line_id:
    #                 line.sale_line_id.return_status = 'cancel'
    #     return res
    #
    # @api.multi
    # def action_draft(self):
    #     res = super(MrpProduction, self).action_draft()
    #     self.write({'state': 'draft'})


class PackLine(models.Model):
    _name = 'prod.pack.line'

    prod_pack_id = fields.Many2one('mrp.production')
    product_id = fields.Many2one('product.product','Customization Name')
    # product_qty = fields.Float('Product Available Qty')
    type = fields.Char('Type')
    size = fields.Char('Size')
    price = fields.Float('Cost To Us/Piece')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('package.design'))

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.model
    def create(self, values):
        res = super(MrpBom, self).create(values)
        tax = {}
        if 'product_tmpl_id' in values:
            for line in res.bom_line_ids:
                tax.update({line.product_id.id: line.product_id.hsn_code.igst_sale.amount})
            maximum = max(tax, key=tax.get)
            product = self.env['product.product'].browse(maximum)
            res.product_tmpl_id.hsn_code = product.hsn_code.id
        return res


    def write(self, values):
        res = super(MrpBom, self).write(values)
        tax = {}
        if 'product_tmpl_id' in values:
            for line in self.bom_line_ids:
                tax.update({line.product_id.id: line.product_id.hsn_code.igst_sale.amount})
            maximum = max(tax, key=tax.get)
            product = self.env['product.product'].browse(maximum)
            self.product_tmpl_id.hsn_code = product.hsn_code.id
        return res

