# -*- coding: utf-8 -*-
# Copyright 2015-2017 Geo Technosoft (<http://www.geotechnosoft.com>)

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Orders',
        copy=False,
        index=True
    )
    internal_transfer_mo_done = fields.Boolean(
        string='Internal Transfer to Process',
        copy=False,
        index=True,
        default=False
    )
    product_finalised = fields.Boolean(
        string='Finalised Product',
        copy=False,
        index=True,
        default=False
    )
    labour_details_line = fields.One2many('labour.detail.line', 'labour_id', string='Packing Detail Charges')
    labour_ids = fields.Many2many('labour.name', 'labour_detail_rel', 'labour_detail_id',
                                 'lab_id', string='Scope Of Work', required=True, copy=True)


class LabourName(models.Model):
    _name = 'labour.name'
    _description = 'Labour Name'
    _order = 'id DESC'

    name = fields.Char('Name', required=True)


class LabourDetailLine(models.Model):
    _name = 'labour.detail.line'
    _description = 'Labour Details Line'
    _order = 'id DESC'

    labour_id = fields.Many2one('stock.picking', 'Labour')
    lab_id = fields.Many2one('labour.name', string='Other Charges')
    description = fields.Char('Description')
    rate = fields.Float(string='rate')



