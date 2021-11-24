from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import pycompat


class ProductProduct(models.Model):
    _inherit = 'product.product'

    to_procure = fields.Float('To Procure Quantity', compute='_compute_quantities',
                              digits=dp.get_precision('Product Unit of Measure'),
                              help="Shortfall quantity", track_visibility='onchange')
    relates_moves = fields.One2many('stock.move', 'product_id', 'Related Moves', track_visibility='onchange',
                                    domain=[('state', 'in', (
                                        'partially_available', 'waiting', 'confirmed', 'assigned')),
                                            ('location_id.usage', '=', 'internal'),
                                            ('location_dest_id.usage', '!=', 'internal'),
                                            ('location_id.name', 'not ilike', 'sample'),
                                            ('location_dest_id.name', 'not ilike', 'sample')]) # 'assigned'
    # default_code = fields.Char('SKU Number', index=True)
    # packaging_product = fields.Boolean('Packaging Product')

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    def _compute_quantities(self):
        res = self._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'),
                                            self._context.get('package_id'), self._context.get('from_date'),
                                            self._context.get('to_date'))
        for product in self:
            to_procure = 0
            if res[product.id]['virtual_available'] < res[product.id]['qty_available']:
                to_procure = abs(res[product.id]['virtual_available'])
            product.qty_available = res[product.id]['qty_available']
            product.incoming_qty = res[product.id]['incoming_qty']
            product.outgoing_qty = res[product.id]['outgoing_qty']
            product.virtual_available = res[product.id]['virtual_available']
            product.free_qty = res[product.id]['free_qty']
            product.to_procure = to_procure

    # @api.model
    # def open_products(self):
    #     ''' Function to open to procure products '''
    #     product_obj = self.env['product.product']
    #     product_ids = []
    #     product_recs = product_obj.search([])
    #     locations = self.env['stock.location'].search(['|', ('name', 'ilike', 'Stock'),
    #                                                   ('name', 'ilike', 'Head Office Stock')])
    #     for product in product_recs:
    #         if product.with_context(location=locations.ids).virtual_available < 0 and \
    #                         product.with_context(location=locations.ids).virtual_available < \
    #                         product.with_context(location=locations.ids).qty_available:
    #             product_ids.append(product.id)
    #     view_type = 'tree,form'
    #     domain = "[('id', 'in', " + str(product_ids) + ")]"
    #     form_view_id = self.env.ref('gts_procurement.product_product_procurement_form_view').id
    #     tree_view_id = self.env.ref('gts_procurement.product_product_procurement_tree_view').id
    #
    #     ctx = self.env.context.copy()
    #     ctx['location'] = locations.ids
    #     value = {
    #         'domain': domain,
    #         'name': _('Purchase Required'),
    #         'view_type': 'form',
    #         'view_mode': view_type,
    #         'res_model': 'product.product',
    #         'view_id': False,
    #         'views': [[tree_view_id, 'list']],
    #         'type': 'ir.actions.act_window',
    #         'context': ctx
    #     }
    #     return value


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    to_procure = fields.Float(
        'To Procure', compute='_compute_quantities', search='_search_to_procure',
        digits=dp.get_precision('Product Unit of Measure'), track_visibility='onchange')
    need_procurement = fields.Boolean('Need Procurement?', compute='_need_procurement',
                                      store=True, track_visibility='onchange')


    @api.depends(
                 'product_variant_ids.relates_moves.product_qty',
                 'product_variant_ids.relates_moves.product_uom_qty',
                 'product_variant_ids.relates_moves.product_uom',
                 'product_variant_ids.relates_moves.state')
    def _need_procurement(self):
        for template in self:
            if template.virtual_available < template.qty_available:
                template.need_procurement = True
            else:
                template.need_procurement = False

    def _compute_quantities(self):
        res = self._compute_quantities_dict()
        for template in self:
            to_procure = 0
            if res[template.id]['virtual_available'] < res[template.id]['qty_available']:
                to_procure = res[template.id]['qty_available'] - res[template.id]['virtual_available']
            template.qty_available = res[template.id]['qty_available']
            template.virtual_available = res[template.id]['virtual_available']
            template.incoming_qty = res[template.id]['incoming_qty']
            template.outgoing_qty = res[template.id]['outgoing_qty']
            template.free_qty = res[template.id]['free_qty']
            template.to_procure = to_procure

    def _search_to_procure(self, operator, value):
        domain = [('to_procure', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]
