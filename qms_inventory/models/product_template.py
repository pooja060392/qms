from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name = fields.Char('Name', index=True, required=True, translate=True, track_visibility='onchange')

    product_brand_id = fields.Many2one(
        'product.brand',
        string='Brand', track_visibility='onchange'
    )
    list_price = fields.Float(
        'Sales Price', default=1.0, track_visibility='onchange',
        digits=dp.get_precision('Product Price'),
        help="Base price to compute the customer price. Sometimes called the catalog price.")

    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')], string="Tracking", track_visibility='onchange',
               default='none', required=True)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # to_procure = fields.Float('To Procure Quantity', compute='_compute_quantities',
    #                           digits=dp.get_precision('Product Unit of Measure'),
    #                           help="Shortfall quantity")
    stock_code = fields.Char('Stock Code', track_visibility='onchange')
    sku_number = fields.Char('SKU Number', track_visibility='onchange')
    standard_price = fields.Float(
        'Cost', company_dependent=True, track_visibility='onchange',
        digits=dp.get_precision('Product Price'),
        groups="base.group_user",
        help = "Cost used for stock valuation in standard price and as a first price to set in average/fifo. "
               "Also used as a base price for pricelists. "
               "Expressed in the default unit of measure of the product.")

    # @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    # def _compute_quantities(self):
    #     res = self._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'),
    #                                         self._context.get('package_id'), self._context.get('from_date'),
    #                                         self._context.get('to_date'))
    #     for product in self:
    #         to_procure = 0
    #         if res[product.id]['virtual_available'] < res[product.id]['qty_available']:
    #             to_procure = abs(res[product.id]['virtual_available'])
    #         product.qty_available = res[product.id]['qty_available']
    #         product.incoming_qty = res[product.id]['incoming_qty']
    #         product.outgoing_qty = res[product.id]['outgoing_qty']
    #         product.virtual_available = res[product.id]['virtual_available']
    #         product.to_procure = to_procure

    @api.model
    def open_products(self):
        ''' Function to open to procure products '''
        product_obj = self.env['product.product']
        product_ids = []
        product_recs = product_obj.search([])
        locations = self.env['stock.location'].search(['|', ('name', 'ilike', 'Stock'),
                                                      ('name', 'ilike', 'Head Office Stock')])
        for product in product_recs:
            if product.with_context(location=locations.ids).virtual_available < 0 and \
                            product.with_context(location=locations.ids).virtual_available < \
                            product.with_context(location=locations.ids).qty_available:
                product_ids.append(product.id)
        view_type = 'tree,form'
        domain = "[('id', 'in', " + str(product_ids) + ")]"
        # form_view_id = self.env.ref('procurement.product_product_procurement_form_view').id
        # tree_view_id = self.env.ref('gts_qms_inventory.inventory_report_tree_purchase').id

        ctx = self.env.context.copy()
        ctx['location'] = locations.ids
        ctx['create'] = False
        ctx['delete'] = False
        value = {
            'domain': domain,
            'name': _('Purchase Required'),
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'product.product',
            'view_id': False,
            'views': [[tree_view_id, 'list']],
            'type': 'ir.actions.act_window',
            'context': ctx
        }
        return value
