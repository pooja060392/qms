# -*- coding: utf-8 -*-
# Part of GeoTechnosoft. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    # @api.multi
    def open_produce_product(self):
        self.ensure_one()
        context = self.env.context.copy() or {}
        context['active_id'] = self.production_id.id
        context['active_model'] = 'mrp.production'
        action = self.production_id.with_context(context).open_produce_product()
        action['context'] = context
        # create new Wizard
        produce_wiz = self.env['mrp.product.produce']
        production = produce_wiz.create({
            'product_id': self.production_id.product_id.id,
            'product_qty': 5,
            'lot_id': 1,
        })
        # for Default functions
        produce_wiz.with_context(context).default_get(
            ['product_id', 'product_qty', 'product_uom_id', 'lot_id', 'produce_line_ids'])
        # production._onchange_product_id()

        # Raw Material Lot
        for pro_line in production.produce_line_ids:
            if pro_line.product_id.categ_id and pro_line.product_id.tracking == 'lot':
                raw_search = self.env['stock.production.lot'].search([('product_id', '=', pro_line.product_id.id)])
                if not raw_search:
                    new_lot = self.env['stock.production.lot'].create({'product_id': pro_line.product_id.id})

                pro_line.update({'lot_id': raw_search[0].id or new_lot.id})
        production.do_produce()
        return True
