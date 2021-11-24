# -*- coding: utf-8 -*-
# Copyright 2015-2017 Geo Technosoft (<http://www.geotechnosoft.com>)

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools import float_compare, float_round
from datetime import datetime


class MrpProduction(models.TransientModel):
    _inherit = "mrp.production"

    @api.model
    def default_get(self, fields):
        res = super(MrpProduction, self).default_get(fields)
        if self._context and self._context.get('active_id'):
            production = self.env['mrp.production'].browse(self._context['active_id'])
            if production:
                lot = self.env['stock.production.lot'].create(
                    {
                        'name': production.product_id.name + '/' + str(datetime.now().strftime('%Y/%H:%M:%S')),
                        'product_id': production.product_id.id
                    }
                )
                res['lot_id'] = lot.id
        return res


    def do_produce(self):
        res = super(MrpProduction, self).do_produce()
        for data in self.production_id:
            rec = {
                'picking_type_id': data.picking_type_id.id,
                'company_id': data.company_id.id,
                'location_id': data.picking_type_id.default_location_dest_id.id,
                'location_dest_id': data.picking_type_id.default_location_src_id.id,
                'name': str(data.name) + ': ' + str(self.lot_id.name),
                'internal_transfer_mo': data.internal_transfer_mo.id,
                'origin': data.name,
                'product_finalised': True
            }
            picking_create_id_ = self.env['stock.picking'].create(rec)
            dict_ = {
                'picking_type_id': data.picking_type_id.id,
                'product_id': self.product_id.id,
                'product_uom': self.product_uom_id.id,
                'product_uom_qty': self.product_qty,
                'picking_id': picking_create_id_.id,
                'name': data.name + ': ' + str(self.lot_id.name),
                'location_id': data.picking_type_id.default_location_dest_id.id,
                'location_dest_id': data.picking_type_id.default_location_src_id.id,
                'origin': data.name
            }
            move_create_id = self.env['stock.move'].create(dict_)
            move_line_dict_ = {
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom_id.id,
                'product_uom_qty': self.product_qty,
                'picking_id': picking_create_id_.id,
                'location_id': data.picking_type_id.default_location_dest_id.id,
                'location_dest_id': data.picking_type_id.default_location_src_id.id,
                'move_id': move_create_id.id,
                'lot_id': self.lot_id.id,
                'lot_name': self.lot_id.name,
                'remove_date': self.lot_id.removal_date,
                'qty_done': self.product_qty,
            }
            self.env['stock.move.line'].create(move_line_dict_)
        return {'type': 'ir.actions.act_window_close'}


    def check_finished_move_lots(self):
        produce_move = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel'))
        print(produce_move)
        if produce_move and produce_move.product_id.tracking != 'none':
            if not self.lot_id:
                raise UserError(_('You need to provide a lot for the finished product'))
            existing_move_line = produce_move.move_line_ids.filtered(lambda x: x.lot_id == self.lot_id)
            if existing_move_line:
                if self.product_id.tracking == 'serial':
                    raise UserError(_('You cannot produce the same serial number twice.'))
                existing_move_line.product_uom_qty += self.product_qty
                existing_move_line.qty_done += self.product_qty
            else:
                vals = {
                    'move_id': produce_move.id,
                    'product_id': produce_move.product_id.id,
                    'production_id': self.production_id.id,
                    'product_uom_qty': self.product_qty,
                    'product_uom_id': produce_move.product_uom.id,
                    'qty_done': self.product_qty,
                    'lot_id': self.lot_id.id,
                    'location_id': produce_move.location_id.id,
                    'location_dest_id': self.production_id.picking_type_id.default_location_src_id.id,
                }
                self.env['stock.move.line'].create(vals)

        for pl in self.produce_line_ids:
            if pl.qty_done:
                if not pl.lot_id:
                    raise UserError(_('Please enter a lot or serial number for %s !' % pl.product_id.name))
                if not pl.move_id:
                    # Find move_id that would match
                    move_id = self.production_id.move_raw_ids.filtered(
                        lambda x: x.product_id == pl.product_id and x.state not in ('done', 'cancel'))
                    if move_id:
                        pl.move_id = move_id
                    else:
                        # create a move and put it in there
                        order = self.production_id
                        pl.move_id = self.env['stock.move'].create({
                            'name': order.name,
                            'product_id': pl.product_id.id,
                            'product_uom': pl.product_uom_id.id,
                            'location_id': order.location_src_id.id,
                            'location_dest_id': self.product_id.property_stock_production.id,
                            'raw_material_production_id': order.id,
                            'group_id': order.procurement_group_id.id,
                            'origin': order.name,
                            'state': 'confirmed'})
                pl.move_id._generate_consumed_move_line(pl.qty_done, self.lot_id, lot=pl.lot_id)
        return True
