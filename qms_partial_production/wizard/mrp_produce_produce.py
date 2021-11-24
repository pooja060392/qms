# -*- coding: utf-8 -*-
# Copyright 2015-2017 Geo Technosoft (<http://www.geotechnosoft.com>)

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    @api.model
    def default_get(self, fields):
        res = super(MrpProductProduce, self).default_get(fields)
        return res

    # @api.multi
    def do_produce(self):
        res = super(MrpProductProduce, self).do_produce()
        quantity = self.product_qty
        if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
            raise UserError(_('You should at least produce some quantity'))
        remaining_quantity = self.production_id.product_qty - self.production_id.qty_produced
        # updating produced quantity
        for workorder in self.production_id.workorder_ids:
            if self.product_id.tracking == 'serial':
                workorder.qty_produced = workorder.qty_produced + quantity
            else:
                workorder.qty_produced = workorder.qty_produced + self.product_qty
                workorder.qty_producing = workorder.qty_production - workorder.qty_produced
        self.production_id.post_inventory()
        return {'type': 'ir.actions.act_window_close'}
