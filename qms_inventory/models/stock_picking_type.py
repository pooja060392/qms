# -*- coding: utf-8 -*-
# Copyright 2015-2017 Geo Technosoft (<http://www.geotechnosoft.com>)

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    new_dest_location = fields.Many2one(
        'stock.location',
        string='Destination Location for IT',
        copy=False,
        index=True
    )
    base_stock_picking_type = fields.Many2one(
        'stock.picking.type',
        string='Stock Picking Type',
        copy=False,
        index=True
    )
    is_manufacturing = fields.Boolean(
        string='Is Manufacturing',
        copy=False, default=False
    )


    related_delivery_location_id = fields.Many2one('res.partner', string='Receipt Location')

    @api.onchange('related_delivery_location_id')
    def onchange_related_location_id(self):
        if self.warehouse_id:
            return {'domain': {'related_delivery_location_id': [('parent_id', '=', self.warehouse_id.partner_id.id)]}}