from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_ids = fields.One2many('mrp.production', compute="_compute_production_ids",
                                    string='Related MO Orders')
    production_count = fields.Integer(compute="_compute_production_count",
                                      string='MO Count')

    @api.depends('name')
    def _compute_production_count(self):
        production_obj = self.env['mrp.production']
        for order in self:
            production_recs = production_obj.search([('origin', '=', order.name)])
            order.production_count = len(production_recs.ids)

    @api.depends('name')
    def _compute_production_ids(self):
        production_obj = self.env['mrp.production']
        for order in self:
            order.production_ids = production_obj.search([('origin', '=', order.name)])


    def view_production_orders(self):
        '''
        This function returns an action that display related production orders
        of current sales order.'''
        action = self.env.ref('gts_qms_manufacturing.mrp_production_sale_order_action').read()[0]
        production_recs = self.mapped('production_ids')
        if len(production_recs) > 1:
            action['domain'] = [('id', 'in', production_recs.ids)]
        elif production_recs:
            action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            action['res_id'] = production_recs.id
        return action
