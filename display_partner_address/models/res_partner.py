# -*- coding: utf-8 -*-

from odoo import models, fields, _


class Partner(models.Model):
    _inherit = "res.partner"

    invoice_child_ids = fields.One2many('res.partner', 'parent_id', string='Invoice Address',
                                        domain=[('type', '=', 'invoice')])
    delivery_child_ids = fields.One2many('res.partner', 'parent_id', string='Delivery Address',
                                         domain=[('type', '=', 'delivery')])