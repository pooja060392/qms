from odoo import models, fields, api, _


class ProductStockWizard(models.TransientModel):
    _name = 'product.stock.wizard'

    sale_id = fields.Many2one('sale.order', string="Sale")
    product_line_ids = fields.One2many('product.stock.wiz.line', 'wizard_id', string="Products", readonly=False)

    @api.model
    def default_get(self, fields):
        res = super(ProductStockWizard, self).default_get(fields)
        context = self._context
        sale = context.get('active_id')
        sale_id = self.env['sale.order'].search([('id', '=', sale)])
        res['sale_id'] = sale_id.id
        # exclude used product
        ex_pro_list = []
        if sale_id:
            for pro in sale_id.order_line:
                ex_pro_list.append(pro.product_id.id)
        if not ex_pro_list:
            self._cr.execute("""select product_id from stock_quant sq
                                            join stock_location sl on sl.id = sq.location_id
                                            where product_id not in (select product_id from stock_quant where sl.sample_location = True) 
                                            """
                             )
        else:
            self._cr.execute("""select product_id from stock_quant sq
                                join stock_location sl on sl.id = sq.location_id
                                where product_id not in (select product_id from stock_quant where sl.sample_location = True) 
                                and product_id not in {0}""".format(tuple(ex_pro_list))
                         )
        product_ids = self._cr.fetchall()
        id_lines = []
        for data in product_ids:
            product_ids = self.env['product.product'].browse(data)
            for product in product_ids:
                prd = {
                    'product_id': product.id,
                    'available_qty': product.qty_available,
                    'sku_number': product.sku_number,
                    'stock_code': product.stock_code
                }
                id_lines.append((0, 0, prd))
        res.update({'product_line_ids': id_lines})
        return res


    def action_save(self):
        context = self._context
        sale_id = self.env['sale.order'].browse(context.get('active_id'))
        for wiz in self:
            for line in wiz.product_line_ids:
                if line.select_product is True:
                    sale_id.order_line.create({
                        'order_id': sale_id.id,
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        # 'mrp': line.product_id.mrp,
                        'location_type': 'from_stock',
                        'product_uom_qty': 1,
                        'price_unit': line.product_id.standard_price,

                    })
        # return {'type': 'ir.actions.act_window_close'}


class ProductStockWizLine(models.TransientModel):
    _name = 'product.stock.wiz.line'

    wizard_id = fields.Many2one('product.stock.wizard', stirng="Product")
    sale_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    product_id = fields.Many2one('product.product', string="Products")
    available_qty = fields.Float(string="Available Quantity")
    sku_number = fields.Char(string="SKU Number")
    stock_code = fields.Char(string="Stock Code")
    select_product = fields.Boolean("Select")

    # Comment: future development for selection

    # def action_add(self):
    #     self.select_product = True
